'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { History, Trash2, Video, Download, FileText } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { pipelineService } from '@/api/services'
import { useToast } from '@/hooks/use-toast'

interface SrtFile {
  name: string
  path: string
}

interface HistoryTask {
  id: string
  videoName: string
  status: 'completed'
  createdAt: number
  config: {
    sourceLanguage: string
    targetLanguage: string
    ttsEngine: string
  }
  result: {
    finalVideo: string
    srtFiles: SrtFile[]
  }
}

export function HistoryPanel() {
  const { toast } = useToast()
  const [historyTasks, setHistoryTasks] = useState<HistoryTask[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [previewingSrt, setPreviewingSrt] = useState<{ taskId: string; srtFile: SrtFile; content: string } | null>(null)
  const [loadingSrt, setLoadingSrt] = useState(false)

  const loadHistory = async () => {
    setLoading(true)
    try {
      const response = await pipelineService.getHistory()
      if (response.success && response.data) {
        setHistoryTasks(response.data)
      }
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const handleDelete = async (taskId: string) => {
    if (!confirm('确定要删除这条记录吗？')) return

    setDeleting(taskId)
    try {
      const response = await pipelineService.deleteTask(taskId)
      if (response.success) {
        // 从列表中移除
        setHistoryTasks(prev => prev.filter(task => task.id !== taskId))
        toast({
          title: '删除成功',
          description: '历史记录已删除',
        })
      } else {
        toast({
          title: '删除失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Delete task error:', error)
      toast({
        title: '删除失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setDeleting(null)
    }
  }

  const handlePreview = (task: HistoryTask) => {
    const videoUrl = `http://localhost:8000/video/${task.result.finalVideo}`
    window.open(videoUrl, '_blank')
  }

  const handleDownloadVideo = (task: HistoryTask) => {
    const videoUrl = `http://localhost:8000/video/${task.result.finalVideo}`
    const link = document.createElement('a')
    link.href = videoUrl
    link.download = `${task.videoName}_final.mp4`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handlePreviewSrt = async (taskId: string, srtFile: SrtFile) => {
    setLoadingSrt(true)
    try {
      const srtUrl = `http://localhost:8000/video/${srtFile.path}`
      const response = await fetch(srtUrl)
      if (response.ok) {
        const content = await response.text()
        setPreviewingSrt({ taskId, srtFile, content })
      } else {
        toast({
          title: '加载失败',
          description: '无法加载字幕文件',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to load SRT:', error)
      toast({
        title: '加载失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setLoadingSrt(false)
    }
  }

  const handleDownloadSrt = (srtFile: SrtFile) => {
    const srtUrl = `http://localhost:8000/video/${srtFile.path}`
    const link = document.createElement('a')
    link.href = srtUrl
    link.download = srtFile.name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            <CardTitle>历史记录</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={loadHistory}>
            刷新
          </Button>
        </div>
        <CardDescription>
          查看所有已完成的翻译任务
        </CardDescription>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">
            加载中...
          </div>
        ) : historyTasks.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            暂无历史记录
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {historyTasks.map((task) => (
                <motion.div
                  key={task.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  className="border rounded-lg p-4 space-y-3 hover:bg-muted/50 transition-colors"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <Video className="h-5 w-5 text-primary" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {task.videoName}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatTime(task.createdAt)}
                        </p>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(task.id)}
                      disabled={deleting === task.id}
                      className="h-8 w-8"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePreview(task)}
                    >
                      <Video className="h-3 w-3 mr-1" />
                      预览
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadVideo(task)}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      下载视频
                    </Button>
                  </div>

                  {/* SRT Files */}
                  {task.result.srtFiles && task.result.srtFiles.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-muted-foreground">字幕文件：</p>
                      <div className="flex flex-wrap gap-2">
                        {task.result.srtFiles.map((srtFile, index) => (
                          <div key={index} className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePreviewSrt(task.id, srtFile)}
                              disabled={loadingSrt}
                              className="text-xs h-7"
                            >
                              <FileText className="h-3 w-3 mr-1" />
                              {srtFile.name}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDownloadSrt(srtFile)}
                              className="h-7 w-7"
                              title="下载"
                            >
                              <Download className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* SRT Preview */}
                  {previewingSrt && previewingSrt.taskId === task.id && (
                    <div className="space-y-2 pt-2 border-t">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium">预览：{previewingSrt.srtFile.name}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setPreviewingSrt(null)}
                          className="h-6 text-xs"
                        >
                          关闭
                        </Button>
                      </div>
                      <div className="bg-muted/50 rounded-lg p-3 max-h-60 overflow-y-auto">
                        <pre className="text-xs font-mono whitespace-pre-wrap">
                          {previewingSrt.content}
                        </pre>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
