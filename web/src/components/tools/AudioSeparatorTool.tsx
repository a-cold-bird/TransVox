'use client'

import React, { useState, useCallback } from 'react'
import { Music, Mic2, Download, Upload, X, Video } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { toolService } from '@/api/services'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

export function AudioSeparatorTool() {
  const { toast } = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [fileType, setFileType] = useState<'video' | 'audio' | null>(null)
  const [separating, setSeparating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [results, setResults] = useState<{
    vocals?: string
    instrumental?: string
    videoOnly?: string
  }>({})

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const droppedFile = acceptedFiles[0]
      setFile(droppedFile)
      setFileType(droppedFile.type.startsWith('video') ? 'video' : 'audio')
      setResults({})
      setTaskId(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 
      'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.aac']
    },
    maxFiles: 1,
  })

  const handleSeparate = async () => {
    if (!file) return

    setSeparating(true)
    setProgress(0)
    setResults({})

    try {
      const response = await toolService.separateAudio(
        file,
        (prog) => setProgress(prog)
      )

      if (response.success && response.data) {
        setTaskId(response.data.taskId)
        // 开始轮询任务状态
        pollSeparationStatus(response.data.taskId)
      } else {
        toast({
          title: '分离失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
        setSeparating(false)
      }
    } catch (error) {
      console.error('Separation error:', error)
      toast({
        title: '分离失败',
        description: '请检查后端服务是否运行',
        variant: 'destructive',
      })
      setSeparating(false)
    }
  }

  const pollSeparationStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await toolService.downloadResult(taskId, 'status')
        
        if (response.success && response.data) {
          const task = response.data as { status: string; progress: number; result?: Record<string, string> }
          
          setProgress(task.progress || 0)
          
          if (task.status === 'completed' && task.result) {
            clearInterval(interval)
            setSeparating(false)
            setResults({
              vocals: task.result.vocals || `/api/tools/download-result/${taskId}/vocals`,
              instrumental: task.result.instrumental || `/api/tools/download-result/${taskId}/instrumental`,
              videoOnly: fileType === 'video' ? task.result.videoOnly || `/api/tools/download-result/${taskId}/video` : undefined,
            })
          } else if (task.status === 'error') {
            clearInterval(interval)
            setSeparating(false)
            toast({
              title: '分离失败',
              description: '处理过程中发生错误',
              variant: 'destructive',
            })
          }
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000)

    // 10分钟后停止轮询
    setTimeout(() => clearInterval(interval), 600000)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>音频分离 - MSST</CardTitle>
          <CardDescription>
            分离人声和背景音乐，支持视频和音频文件
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 文件上传区域 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">上传文件</label>
            {!file ? (
              <div {...getRootProps()} className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              )}>
                <input {...getInputProps()} />
                <Upload className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">{isDragActive ? '放开以上传' : '拖放视频或音频文件到这里'}</p>
                <p className="text-xs text-muted-foreground mt-2">支持 MP4, MKV, MP3, WAV 等格式</p>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  {fileType === 'video' ? (
                    <Video className="h-5 w-5 text-primary" />
                  ) : (
                    <Music className="h-5 w-5 text-primary" />
                  )}
                  <div>
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB - {fileType === 'video' ? '视频' : '音频'}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => { setFile(null); setFileType(null); }}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* 进度显示 */}
          {separating && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                分离中... {progress}%
              </p>
            </div>
          )}

          {/* 开始按钮 */}
          <Button
            onClick={handleSeparate}
            disabled={!file || separating}
            className="w-full"
            size="lg"
          >
            <Music className="h-4 w-4 mr-2" />
            开始分离
          </Button>

          {/* 提示信息 */}
          {!separating && !results.vocals && (
            <div className="text-xs text-muted-foreground space-y-1">
              <p>• 上传视频文件会自动提取音频进行分离</p>
              <p>• 分离需要一定时间，具体取决于文件大小</p>
              <p>• 分离后可下载人声、背景音乐和无声视频</p>
            </div>
          )}
        </CardContent>
      </Card>

      {(results.vocals || results.instrumental) && (
        <Card>
          <CardHeader>
            <CardTitle>分离结果</CardTitle>
            <CardDescription>预览和下载分离后的音频文件</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {results.vocals && (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3 flex-1">
                    <Mic2 className="h-5 w-5 text-primary" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">人声音轨</p>
                      <p className="text-xs text-muted-foreground">vocals.wav</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/vocals`, '_blank')}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      下载
                    </Button>
                  </div>
                </div>
                {/* 音频预览 */}
                <audio 
                  controls 
                  className="w-full"
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/vocals`}
                />
              </div>
            )}

            {results.instrumental && (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3 flex-1">
                    <Music className="h-5 w-5 text-primary" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">背景音乐</p>
                      <p className="text-xs text-muted-foreground">instrumental.wav</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/instrumental`, '_blank')}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      下载
                    </Button>
                  </div>
                </div>
                {/* 音频预览 */}
                <audio 
                  controls 
                  className="w-full"
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/instrumental`}
                />
              </div>
            )}

            {results.videoOnly && (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3 flex-1">
                    <Video className="h-5 w-5 text-primary" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">无声视频</p>
                      <p className="text-xs text-muted-foreground">video_only.mp4</p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/videoOnly`, '_blank')}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    下载
                  </Button>
                </div>
                {/* 视频预览 */}
                <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
                  <video 
                    controls 
                    className="w-full h-full"
                    src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/videoOnly`}
                  >
                    您的浏览器不支持视频预览
                  </video>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}


