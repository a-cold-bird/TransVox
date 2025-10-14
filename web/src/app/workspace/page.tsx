'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Play, Check, StopCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { VideoUpload } from '@/components/video/VideoUpload'
import { VideoPreview } from '@/components/video/VideoPreview'
import { UserConfigPanel } from '@/components/pipeline/UserConfigPanel'
import { HistoryPanel } from '@/components/pipeline/HistoryPanel'
import { SystemStatsBar } from '@/components/system/SystemStatsBar'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { useTranslation } from '@/hooks/useTranslation'
import { useAppStore } from '@/store/useAppStore'
import { pipelineService, configService } from '@/api/services'
import type { PipelineConfig as PipelineConfigType } from '@/types'
import Link from 'next/link'
import { useToast } from '@/hooks/use-toast'

// 提取错误信息的关键部分，只保留错误类型和错误原因
const extractErrorCode = (errorDetails: string): string => {
  if (!errorDetails) return '未知错误'

  const lines = errorDetails.trim().split('\n')
  // 从最后几行中查找实际的错误信息
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim()
    // 查找包含错误类型的行（通常以大写字母开头，包含Error或Exception）
    if (line && /^[A-Z]\w*(Error|Exception)/.test(line)) {
      return line
    }
  }

  // 如果没找到，返回最后一行非空行
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim()
    if (line) return line
  }

  return '未知错误'
}

export default function WorkspacePage() {
  const { t } = useTranslation()
  const { toast } = useToast()
  const {
    currentVideo,
    isPipelineRunning,
    pipelineProgress,
    completedVideoPath,
    currentTaskId,
    setIsPipelineRunning,
    setPipelineProgress,
    setCompletedVideoPath,
    setCurrentTaskId
  } = useAppStore()
  const [startingPipeline, setStartingPipeline] = useState(false)
  const [stoppingPipeline, setStoppingPipeline] = useState(false)
  const pollingIntervalRef = React.useRef<NodeJS.Timeout | null>(null)

  const handleStartPipeline = async () => {
    if (!currentVideo) return

    setStartingPipeline(true)

    try {
      // 从用户配置中读取配置
      const configResponse = await configService.getConfig()
      if (!configResponse.success || !configResponse.data) {
        toast({
          title: '配置错误',
          description: '无法加载配置，请先设置用户配置',
          variant: 'destructive',
        })
        return
      }

      const userConfig = configResponse.data
      const config: PipelineConfigType = {
        videoFile: currentVideo.path,
        outputDir: `output/${Date.now()}`,
        translation: {
          sourceLanguage: userConfig.translation?.source_lang || 'en',
          targetLanguage: userConfig.translation?.target_lang || 'zh',
        },
        tts: {
          engine: userConfig.tts?.engine || 'indextts',
        },
        subtitle: {
          mode: 'hardcode',
          position: 'bottom',
          fontSize: 24,
          fontColor: '#FFFFFF',
          outlineColor: '#000000',
          outlineWidth: 2,
          margin: 10,
        },
      }

      const response = await pipelineService.startPipeline(config)

      if (response.success && response.data) {
        const taskId = response.data.taskId
        setCurrentTaskId(taskId)
        setIsPipelineRunning(true)
        startProgressPolling(taskId)
      } else {
        toast({
          title: '启动失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Pipeline start error:', error)
      toast({
        title: '启动失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setStartingPipeline(false)
    }
  }

  const startProgressPolling = useCallback((taskId: string) => {
    // 清除之前的轮询
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }

    const interval = setInterval(async () => {
      try {
        const response = await pipelineService.getPipelineStatus(taskId)

        if (response.success && response.data) {
          const task = response.data

          setPipelineProgress({
            currentStep: task.progress,
            totalSteps: 100,
            currentTask: task.type,
            progress: task.progress,
            message: task.message || '',
          })

          if (task.status === 'completed' || task.status === 'error' || task.status === 'cancelled') {
            clearInterval(interval)
            pollingIntervalRef.current = null
            setIsPipelineRunning(false)
            setCurrentTaskId(null)

            if (task.status === 'completed') {
              // 从任务结果中获取视频路径
              if (task.result && task.result.final_video) {
                setCompletedVideoPath(task.result.final_video as string)
              }
              toast({
                title: '处理完成',
                description: '视频翻译和配音已完成',
              })
            } else if (task.status === 'cancelled') {
              toast({
                title: '已停止',
                description: '流水线已被停止',
              })
            } else {
              // 使用 toast 显示简化的错误信息
              const errorDetails = task.result?.error || task.message || '未知错误'
              const errorCode = extractErrorCode(errorDetails)
              toast({
                title: '处理失败',
                description: errorCode,
                variant: 'destructive',
              })
            }
          }
        }
      } catch (error) {
        console.error('Progress polling error:', error)
      }
    }, 2000)

    pollingIntervalRef.current = interval
  }, [setPipelineProgress, setIsPipelineRunning, setCurrentTaskId, setCompletedVideoPath, toast])

  const handleStopPipeline = async () => {
    if (!currentTaskId) return

    setStoppingPipeline(true)

    try {
      const response = await pipelineService.stopPipeline(currentTaskId)

      if (response.success) {
        // 清除轮询
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }

        // 更新状态
        setIsPipelineRunning(false)
        setCurrentTaskId(null)
        setPipelineProgress(null)

        toast({
          title: '已停止',
          description: '流水线已成功停止',
        })
      } else {
        toast({
          title: '停止失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Stop pipeline error:', error)
      toast({
        title: '停止失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setStoppingPipeline(false)
    }
  }

  // 组件卸载时清理轮询
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  // 页面加载时恢复轮询（如果pipeline正在运行）
  useEffect(() => {
    if (isPipelineRunning && currentTaskId && !pollingIntervalRef.current) {
      startProgressPolling(currentTaskId)
    }
  }, [isPipelineRunning, currentTaskId, startProgressPolling])

  const pipelineSteps = [
    { id: 1, name: t('workspace.step1.name'), description: t('workspace.step1.desc') },
    { id: 2, name: t('workspace.step2.name'), description: t('workspace.step2.desc') },
    { id: 3, name: t('workspace.step3.name'), description: t('workspace.step3.desc') },
    { id: 4, name: t('workspace.step4.name'), description: t('workspace.step4.desc') },
    { id: 5, name: t('workspace.step5.name'), description: t('workspace.step5.desc') },
    { id: 6, name: t('workspace.step6.name'), description: t('workspace.step6.desc') },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Button variant="ghost" asChild>
            <Link href="/" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              {t('nav.backToHome')}
            </Link>
          </Button>
          <h1 className="text-lg font-semibold">{t('workspace.title')}</h1>
          <LanguageSwitcher />
        </div>
      </header>

      {/* System Stats Bar - 系统监控状态栏 */}
      <SystemStatsBar />

      {/* Pipeline Steps Indicator - 简洁的顶部步骤条 */}
      <div className="border-b bg-background/50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-2 overflow-x-auto">
            {pipelineSteps.map((step, index) => {
              const isCompleted = pipelineProgress && pipelineProgress.currentStep > index * 14
              const isCurrent = pipelineProgress && Math.floor(pipelineProgress.currentStep / 14) === index
              const isLast = index === pipelineSteps.length - 1

              return (
                <React.Fragment key={step.id}>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <div
                      className={`
                        rounded-full p-1 transition-colors
                        ${isCompleted ? 'bg-primary text-primary-foreground' :
                          isCurrent ? 'bg-primary/20 text-primary ring-2 ring-primary/50' :
                          'bg-muted text-muted-foreground'}
                      `}
                    >
                      {isCompleted ? (
                        <Check className="h-3 w-3" />
                      ) : (
                        <span className="flex h-3 w-3 items-center justify-center text-[10px] font-bold">
                          {step.id}
                        </span>
                      )}
                    </div>
                    <span className={`text-xs font-medium ${isCurrent ? 'text-primary' : 'text-muted-foreground'}`}>
                      {step.name}
                    </span>
                  </div>
                  {!isLast && (
                    <div className={`h-px flex-1 min-w-4 ${isCompleted ? 'bg-primary' : 'bg-muted'}`} />
                  )}
                </React.Fragment>
              )
            })}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Upload & Pipeline Config */}
          <div className="lg:col-span-2 space-y-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <VideoUpload />
            </motion.div>

            {currentVideo && !isPipelineRunning && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>{t('workspace.readyToProcess')}</CardTitle>
                    <CardDescription>
                      {t('workspace.configureRightPanel')}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={handleStartPipeline}
                      disabled={isPipelineRunning || startingPipeline}
                      className="w-full relative overflow-hidden group"
                      size="lg"
                    >
                      <span className="relative z-10 flex items-center justify-center">
                        {startingPipeline ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="mr-2"
                          >
                            <Play className="h-4 w-4" />
                          </motion.div>
                        ) : (
                          <Play className="h-4 w-4 mr-2" />
                        )}
                        {startingPipeline ? t('workspace.starting') : t('pipeline.startPipeline')}
                      </span>
                      {/* 悬停效果 */}
                      <motion.div
                        className="absolute inset-0 bg-primary-foreground/10 opacity-0 group-hover:opacity-100"
                        transition={{ duration: 0.2 }}
                      />
                      {/* 启动中的光波效果 */}
                      {startingPipeline && (
                        <motion.div
                          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                          animate={{ x: ['-100%', '200%'] }}
                          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                        />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Pipeline Progress */}
            {isPipelineRunning && pipelineProgress && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Card className="border-primary/50 shadow-lg shadow-primary/10">
                  <CardHeader className="relative overflow-hidden">
                    {/* 背景动画效果 */}
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 animate-pulse" />

                    <CardTitle className="flex items-center gap-2 relative z-10">
                      {/* 脉冲光环效果 */}
                      <div className="relative">
                        <Play className="h-5 w-5 text-primary" />
                        <span className="absolute inset-0 rounded-full bg-primary/30 animate-ping" />
                      </div>
                      {t('workspace.processing')}
                    </CardTitle>
                    <CardDescription className="relative z-10">
                      {pipelineProgress.message}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* 增强的进度条 */}
                    <div className="space-y-2">
                      <Progress
                        value={pipelineProgress.progress}
                        className="h-3 relative overflow-hidden"
                      />
                      {/* 进度百分比 */}
                      <div className="flex justify-between items-center">
                        <p className="text-sm text-muted-foreground">
                          {pipelineProgress.progress}% {t('workspace.complete')}
                        </p>
                        {/* 动画的处理中指示器 */}
                        <motion.div
                          className="flex gap-1"
                          animate={{ opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                        >
                          <span className="w-2 h-2 rounded-full bg-primary" />
                          <span className="w-2 h-2 rounded-full bg-primary" style={{ animationDelay: '0.2s' }} />
                          <span className="w-2 h-2 rounded-full bg-primary" style={{ animationDelay: '0.4s' }} />
                        </motion.div>
                      </div>
                    </div>

                    {/* 停止按钮 */}
                    <Button
                      onClick={handleStopPipeline}
                      disabled={stoppingPipeline}
                      variant="destructive"
                      className="w-full relative overflow-hidden group"
                    >
                      <span className="relative z-10 flex items-center justify-center">
                        <StopCircle className="h-4 w-4 mr-2" />
                        {stoppingPipeline ? '停止中...' : '停止流水线'}
                      </span>
                      {stoppingPipeline && (
                        <motion.div
                          className="absolute inset-0 bg-destructive-foreground/10"
                          animate={{ x: ['-100%', '100%'] }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Video Preview */}
            {completedVideoPath && !isPipelineRunning && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <VideoPreview
                  videoUrl={`http://localhost:8000/video/${completedVideoPath}`}
                  title="处理完成的视频"
                  onClose={() => setCompletedVideoPath(null)}
                />
              </motion.div>
            )}
          </div>

          {/* Right Column - User Config Panel */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
              className="sticky top-8 space-y-6"
            >
              <UserConfigPanel />
              <HistoryPanel />
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}

