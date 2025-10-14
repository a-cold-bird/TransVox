'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Play, Pause, Upload, FileVideo, FileText, Volume2, RefreshCw, Download,
  Scissors, Headphones, Eye, Settings, ChevronRight, CheckCircle, XCircle, Clock,
  AlertCircle, Loader2, Film, Type
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

// 类型定义
interface SubtitleSegment {
  index: number
  start_time: string
  end_time: string
  start_seconds: number
  end_seconds: number
  content: string
  speaker?: string
}

interface VideoSegment {
  index: number
  start_time: number
  end_time: number
  duration: number
  file_path: string
  file_size: number
}

interface TTSSegment {
  index: number
  text: string
  audio_path: string
  duration: number
  file_size: number
  engine: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

interface WorkbenchData {
  project_id: string
  video_path?: string
  srt_path?: string
  subtitles: SubtitleSegment[]
  video_segments: VideoSegment[]
  tts_segments: TTSSegment[]
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'

export function SubtitleWorkbench() {
  const [workbenchData, setWorkbenchData] = useState<WorkbenchData | null>(null)
  const [loading, setLoading] = useState(false)
  const [processingTask, setProcessingTask] = useState<string | null>(null)
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null)
  const { toast } = useToast()

  // 创建新的工作台项目
  const createWorkbench = async (projectName: string) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: projectName
        })
      })
      const data = await response.json()
      if (data.success) {
        const projectId = data.data.project_id
        await loadWorkbenchData(projectId)
        toast({
          title: "工作台创建成功",
          description: "请上传视频和字幕文件"
        })
      } else {
        toast({
          title: "创建工作台失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  // 上传SRT文件
  const uploadSRTFile = async (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects/${projectId}/upload-srt`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        await loadWorkbenchData(projectId)
        toast({
          title: "SRT文件上传成功",
          description: `已解析 ${data.data.subtitles_count} 条字幕`
        })
      } else {
        toast({
          title: "SRT文件上传失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    }
  }

  // 上传视频文件
  const uploadVideoFile = async (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects/${projectId}/upload-video`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        await loadWorkbenchData(projectId)
        toast({
          title: "视频文件上传成功",
          description: "视频文件已准备就绪"
        })
      } else {
        toast({
          title: "视频文件上传失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    }
  }

  // 加载工作台数据
  const loadWorkbenchData = async (projectId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects/${projectId}`)
      const data = await response.json()
      if (data.success) {
        setWorkbenchData(data.data)
      }
    } catch (error) {
      console.error('加载工作台数据失败:', error)
    }
  }

  // 提取视频片段
  const extractVideoSegments = async () => {
    if (!workbenchData) return

    setProcessingTask('extract')
    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects/${workbenchData.project_id}/extract-segments`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.success) {
        toast({
          title: "开始提取视频片段",
          description: "正在后台处理中..."
        })
        pollTaskStatus(data.data.task_id)
      } else {
        toast({
          title: "提取视频片段失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    } finally {
      setProcessingTask(null)
    }
  }

  // 批量生成TTS
  const generateBatchTTS = async (engine: string = 'indextts') => {
    if (!workbenchData) return

    setProcessingTask('tts')
    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects/${workbenchData.project_id}/generate-tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine })
      })
      const data = await response.json()
      if (data.success) {
        toast({
          title: "开始生成TTS",
          description: "正在后台处理中..."
        })
        pollTaskStatus(data.data.task_id)
      } else {
        toast({
          title: "生成TTS失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    } finally {
      setProcessingTask(null)
    }
  }

  // 重新生成单个TTS
  const regenerateSingleTTS = async (segmentIndex: number, engine: string = 'indextts') => {
    if (!workbenchData) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/workbench/projects/${workbenchData.project_id}/regenerate-tts/${segmentIndex}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine })
      })
      const data = await response.json()
      if (data.success) {
        toast({
          title: "开始重新生成TTS",
          description: `片段 ${segmentIndex} 正在处理中...`
        })
        pollTaskStatus(data.data.task_id)
      } else {
        toast({
          title: "重新生成TTS失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    }
  }

  // 轮询任务状态
  const pollTaskStatus = async (taskId: string) => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/tools/download-result/${taskId}/status`)
        const data = await response.json()
        if (data.success && data.data.status === 'completed') {
          toast({
            title: "任务完成",
            description: data.data.result.message
          })
          if (workbenchData) {
            await loadWorkbenchData(workbenchData.project_id)
          }
        } else if (data.data.status === 'failed') {
          toast({
            title: "任务失败",
            description: data.data.result.error,
            variant: "destructive"
          })
        } else {
          setTimeout(checkStatus, 2000)
        }
      } catch (error) {
        console.error('轮询任务状态失败:', error)
      }
    }
    checkStatus()
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">字幕切片与TTS工作台</h2>
          <p className="text-muted-foreground">
            基于现有字幕文件进行视频切片和TTS生成，支持批量处理和精细化对比展示
          </p>
        </div>
      </div>

      {!workbenchData ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Film className="h-5 w-5" />
              创建新的工作台
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">项目名称</label>
              <input
                type="text"
                placeholder="输入项目名称"
                className="w-full p-2 border rounded-md"
                id="project-name"
                defaultValue={`工作台_${new Date().toLocaleString()}`}
              />
            </div>
            <Button
              onClick={() => {
                const projectName = (document.getElementById('project-name') as HTMLInputElement)?.value || `工作台_${Date.now()}`
                createWorkbench(projectName)
              }}
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Scissors className="h-4 w-4 mr-2" />
              )}
              创建工作台
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* 文件上传区域 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Type className="h-5 w-5" />
                  文件上传
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedSegment(null)
                    setWorkbenchData(null)
                  }}
                >
                  关闭工作台
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                {/* SRT文件上传 */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-600 mb-4">
                    支持 .srt 格式的字幕文件
                  </p>
                  <input
                    type="file"
                    accept=".srt"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) uploadSRTFile(workbenchData.project_id, file)
                    }}
                    className="hidden"
                    id="srt-upload"
                  />
                  <Button asChild variant="outline">
                    <label htmlFor="srt-upload" className="cursor-pointer">
                      <Upload className="h-4 w-4 mr-2" />
                      选择SRT文件
                    </label>
                  </Button>
                  {workbenchData.srt_path && (
                    <p className="text-xs text-green-600 mt-2">
                      ✓ 已加载 {workbenchData.subtitles.length} 条字幕
                    </p>
                  )}
                </div>

                {/* 视频文件上传 */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <FileVideo className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-600 mb-4">
                    支持 MP4, AVI, MOV, MKV, WebM 格式
                  </p>
                  <input
                    type="file"
                    accept=".mp4,.avi,.mov,.mkv,.webm"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) uploadVideoFile(workbenchData.project_id, file)
                    }}
                    className="hidden"
                    id="video-upload"
                  />
                  <Button asChild variant="outline">
                    <label htmlFor="video-upload" className="cursor-pointer">
                      <Upload className="h-4 w-4 mr-2" />
                      选择视频文件
                    </label>
                  </Button>
                  {workbenchData.video_path && (
                    <p className="text-xs text-green-600 mt-2">
                      ✓ 视频文件已加载
                    </p>
                  )}
                </div>
              </div>

              {/* 工作台状态 */}
              <div className="grid gap-4 md:grid-cols-3 mt-6 pt-6 border-t">
                <div className="flex items-center gap-2">
                  <FileVideo className="h-4 w-4 text-blue-500" />
                  <span className="text-sm">视频文件:</span>
                  <span className="text-sm font-mono">{workbenchData.video_path ? '✓ 已加载' : '✗ 未加载'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-green-500" />
                  <span className="text-sm">字幕条数:</span>
                  <span className="text-sm font-mono">{workbenchData.subtitles.length}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Volume2 className="h-4 w-4 text-purple-500" />
                  <span className="text-sm">TTS片段:</span>
                  <span className="text-sm font-mono">{workbenchData.tts_segments.length}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 操作按钮 */}
          <div className="flex gap-4">
            <Button
              onClick={extractVideoSegments}
              disabled={processingTask === 'extract' || !workbenchData.video_path || workbenchData.subtitles.length === 0}
            >
              {processingTask === 'extract' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Scissors className="h-4 w-4 mr-2" />
              )}
              提取视频片段
            </Button>
            <Button
              onClick={() => generateBatchTTS()}
              disabled={processingTask === 'tts' || workbenchData.subtitles.length === 0}
              variant="outline"
            >
              {processingTask === 'tts' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Volume2 className="h-4 w-4 mr-2" />
              )}
              批量生成TTS
            </Button>
          </div>

          {/* 字幕片段列表 */}
          <Card>
            <CardHeader>
              <CardTitle>字幕片段列表</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {workbenchData.subtitles.map((subtitle) => {
                  const videoSegment = workbenchData.video_segments.find(s => s.index === subtitle.index)
                  const ttsSegment = workbenchData.tts_segments.find(s => s.index === subtitle.index)

                  return (
                    <div
                      key={subtitle.index}
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        selectedSegment === subtitle.index
                          ? 'border-primary bg-primary/5'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedSegment(subtitle.index)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-sm">片段 {subtitle.index}</span>
                            {subtitle.speaker && (
                              <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                {subtitle.speaker}
                              </span>
                            )}
                            <span className="text-xs text-gray-500">
                              {subtitle.start_time} → {subtitle.end_time}
                            </span>
                          </div>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <p className="text-sm mb-2 truncate cursor-help">{subtitle.content}</p>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-md">
                              <p className="whitespace-pre-wrap">{subtitle.content}</p>
                            </TooltipContent>
                          </Tooltip>

                          <div className="flex items-center gap-4 text-xs text-gray-600">
                            <span className="flex items-center gap-1">
                              <Film className="h-3 w-3" />
                              视频: {videoSegment ? '✓' : '✗'}
                            </span>
                            <span className="flex items-center gap-1">
                              {ttsSegment ? getStatusIcon(ttsSegment.status) : <Clock className="h-3 w-3" />}
                              TTS: {ttsSegment ? '✓' : '✗'}
                            </span>
                            {ttsSegment && (
                              <span>时长: {ttsSegment.duration.toFixed(2)}s</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1 ml-4">
                          {videoSegment && (
                            <button className="p-1 hover:bg-gray-100 rounded">
                              <Play className="h-4 w-4" />
                            </button>
                          )}
                          {ttsSegment && (
                            <button className="p-1 hover:bg-gray-100 rounded">
                              <Headphones className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            className="p-1 hover:bg-gray-100 rounded"
                            onClick={(e) => {
                              e.stopPropagation()
                              regenerateSingleTTS(subtitle.index)
                            }}
                            title={ttsSegment ? '重新生成TTS' : '生成TTS'}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      </div>
    </TooltipProvider>
  )
}