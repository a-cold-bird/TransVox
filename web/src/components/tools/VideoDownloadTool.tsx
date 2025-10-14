'use client'

import React, { useState } from 'react'
import { Download, Link as LinkIcon, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useTranslation } from '@/hooks/useTranslation'
import { downloadService } from '@/api/services'
import { useToast } from '@/hooks/use-toast'
import { useLocalStorage } from '@/hooks/useLocalStorage'

interface DownloadState {
  url: string
  quality: string
  audioOnly: boolean
  taskId: string | null
  downloadedFile: {
    filePath: string
    fileName: string
    fileSize: number
  } | null
}

export function VideoDownloadTool() {
  const { t } = useTranslation()
  const { toast } = useToast()

  // 使用持久化存储
  const [persistedState, setPersistedState] = useLocalStorage<DownloadState>('video-download-tool', {
    url: '',
    quality: '1080p',
    audioOnly: false,
    taskId: null,
    downloadedFile: null,
  })

  const [url, setUrl] = useState(persistedState.url)
  const [quality, setQuality] = useState(persistedState.quality)
  const [audioOnly, setAudioOnly] = useState(persistedState.audioOnly)
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [taskId, setTaskId] = useState<string | null>(persistedState.taskId)
  const [downloadedFile, setDownloadedFile] = useState<{
    filePath: string
    fileName: string
    fileSize: number
  } | null>(persistedState.downloadedFile)

  // 更新持久化状态的辅助函数
  const updatePersistedState = (updates: Partial<DownloadState>) => {
    setPersistedState(prev => ({ ...prev, ...updates }))
  }

  // 包装 setter 函数以自动持久化
  const handleSetUrl = (newUrl: string) => {
    setUrl(newUrl)
    updatePersistedState({ url: newUrl })
  }

  const handleSetQuality = (newQuality: string) => {
    setQuality(newQuality)
    updatePersistedState({ quality: newQuality })
  }

  const handleSetAudioOnly = (newAudioOnly: boolean) => {
    setAudioOnly(newAudioOnly)
    updatePersistedState({ audioOnly: newAudioOnly })
  }

  const handleSetTaskId = (newTaskId: string | null) => {
    setTaskId(newTaskId)
    updatePersistedState({ taskId: newTaskId })
  }

  const handleSetDownloadedFile = (newFile: { filePath: string; fileName: string; fileSize: number } | null) => {
    setDownloadedFile(newFile)
    updatePersistedState({ downloadedFile: newFile })
  }

  const handleDownload = async () => {
    if (!url) return

    setDownloading(true)
    setProgress(0)
    handleSetDownloadedFile(null)

    try {
      const response = await downloadService.downloadVideo(url, quality)

      if (response.success && response.data) {
        handleSetTaskId(response.data.taskId)
        pollDownloadStatus(response.data.taskId)
      } else {
        toast({
          title: '下载失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
        setDownloading(false)
      }
    } catch (error) {
      console.error('Download error:', error)
      toast({
        title: '下载失败',
        description: '请检查后端服务是否运行',
        variant: 'destructive',
      })
      setDownloading(false)
    }
  }

  const pollDownloadStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await downloadService.getDownloadStatus(taskId)
        
        if (response.success && response.data) {
          const task = response.data
          
          setProgress(task.progress || 0)
          
          if (task.status === 'completed') {
            clearInterval(interval)
            setDownloading(false)
            const result = task.result as { filePath?: string; fileName?: string; fileSize?: number }
            handleSetDownloadedFile({
              filePath: result.filePath || '',
              fileName: result.fileName || 'downloaded_file',
              fileSize: result.fileSize || 0
            })
          } else if (task.status === 'error') {
            clearInterval(interval)
            setDownloading(false)
            toast({
              title: '下载失败',
              description: task.message || '未知错误',
              variant: 'destructive',
            })
          }
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000)

    setTimeout(() => clearInterval(interval), 600000)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>视频下载</CardTitle>
          <CardDescription>
            支持 YouTube, Bilibili, Twitter 等主流视频平台
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* URL 输入 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('download.url')}</label>
            <div className="relative">
              <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="url"
                value={url}
                onChange={(e) => handleSetUrl(e.target.value)}
                placeholder={t('download.urlPlaceholder')}
                className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* 下载选项 */}
          <div className="space-y-4">
            {/* 仅下载音频选项 */}
            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
              <div>
                <p className="text-sm font-medium">仅下载音频</p>
                <p className="text-xs text-muted-foreground mt-1">
                  下载为 MP3 格式（320kbps）
                </p>
              </div>
              <input
                type="checkbox"
                checked={audioOnly}
                onChange={(e) => handleSetAudioOnly(e.target.checked)}
                className="w-5 h-5 rounded"
              />
            </div>

            {/* 视频质量选择 */}
            {!audioOnly && (
              <div className="space-y-2">
                <label className="text-sm font-medium">视频质量</label>
                <Select value={quality} onValueChange={handleSetQuality}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="best">最高质量</SelectItem>
                    <SelectItem value="1080p">1080p (推荐)</SelectItem>
                    <SelectItem value="720p">720p</SelectItem>
                    <SelectItem value="480p">480p</SelectItem>
                    <SelectItem value="360p">360p</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* 进度显示 */}
          {downloading && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                {t('download.downloading')} {progress}%
              </p>
            </div>
          )}

          {/* 下载按钮 */}
          <Button
            onClick={handleDownload}
            disabled={!url || downloading}
            className="w-full"
            size="lg"
          >
            <Download className="h-4 w-4 mr-2" />
            {downloading ? t('download.downloading') : (audioOnly ? '下载音频' : '下载视频')}
          </Button>

          {/* 下载完成 - 视频预览 */}
          {downloadedFile && !audioOnly && (
            <div className="space-y-3">
              <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">下载完成</p>
                    <p className="text-xs text-muted-foreground truncate">{downloadedFile.fileName}</p>
                    <p className="text-xs text-muted-foreground">
                      {(downloadedFile.fileSize / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      💡 右键点击视频播放器，选择&ldquo;视频另存为&rdquo;即可下载
                    </p>
                  </div>
                </div>
              </div>

              {/* 视频预览 */}
              <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
                <video
                  controls
                  controlsList="nodownload"
                  className="w-full h-full"
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/file`}
                >
                  您的浏览器不支持视频预览
                </video>
              </div>
            </div>
          )}

          {/* 下载完成 - 音频 */}
          {downloadedFile && audioOnly && (
            <div className="space-y-3">
              <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">下载完成</p>
                    <p className="text-xs text-muted-foreground truncate">{downloadedFile.fileName}</p>
                    <p className="text-xs text-muted-foreground">
                      {(downloadedFile.fileSize / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      💡 右键点击音频播放器，选择&ldquo;音频另存为&rdquo;即可下载
                    </p>
                  </div>
                </div>
              </div>

              {/* 音频预览 */}
              <audio
                controls
                controlsList="nodownload"
                className="w-full"
                src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/file`}
              />
            </div>
          )}

          {/* 支持的平台 */}
          <div className="text-xs text-muted-foreground space-y-1">
            <p className="font-medium">支持的平台：</p>
            <p>• YouTube, Bilibili, Twitter, Vimeo</p>
            <p>• TikTok, Instagram, Facebook</p>
            <p>• 以及其他 1000+ 视频网站</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
