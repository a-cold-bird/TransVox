'use client'

import React, { useState, useCallback } from 'react'
import { Film, Music, Download, X, Layers, Plus } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface AudioTrack {
  id: string
  file: File
  url: string
  name: string
}

interface MuxResult {
  video_path: string
  file_size: number
  file_size_mb: number
}

interface TaskResponse {
  status: string
  progress: number
  result?: MuxResult
}

export function AudioVideoMuxerTool() {
  const { toast } = useToast()
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoUrl, setVideoUrl] = useState<string>('')
  const [audioTracks, setAudioTracks] = useState<AudioTrack[]>([])
  const [muxing, setMuxing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [result, setResult] = useState<{
    video_path: string
    file_size: number
    file_size_mb: number
  } | null>(null)

  // 视频文件拖拽
  const onVideoDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      // 清理旧的URL
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl)
      }
      const url = URL.createObjectURL(file)
      setVideoFile(file)
      setVideoUrl(url)
      setResult(null)
      setTaskId(null)
    }
  }, [videoUrl])

  const { getRootProps: getVideoRootProps, getInputProps: getVideoInputProps, isDragActive: isVideoDragActive } = useDropzone({
    onDrop: onVideoDrop,
    accept: {
      'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm']
    },
    maxFiles: 1,
  })

  // 音频文件拖拽（支持多个）
  const onAudioDrop = useCallback((acceptedFiles: File[]) => {
    const newTracks: AudioTrack[] = acceptedFiles.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      url: URL.createObjectURL(file),
      name: file.name
    }))
    setAudioTracks(prev => [...prev, ...newTracks])
    setResult(null)
    setTaskId(null)
  }, [])

  const { getRootProps: getAudioRootProps, getInputProps: getAudioInputProps, isDragActive: isAudioDragActive } = useDropzone({
    onDrop: onAudioDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.aac']
    },
    multiple: true,
  })

  // 移除音频轨道
  const removeAudioTrack = (id: string) => {
    setAudioTracks(prev => {
      const track = prev.find(t => t.id === id)
      if (track) {
        URL.revokeObjectURL(track.url)
      }
      return prev.filter(t => t.id !== id)
    })
  }

  // 移除视频
  const removeVideo = () => {
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl)
    }
    setVideoFile(null)
    setVideoUrl('')
  }

  // 合成音视频
  const handleMux = async () => {
    if (!videoFile) {
      toast({
        title: '请先上传视频',
        description: '需要上传视频文件',
        variant: 'destructive'
      })
      return
    }

    if (audioTracks.length === 0) {
      toast({
        title: '请先上传音频',
        description: '需要至少上传一个音频文件',
        variant: 'destructive'
      })
      return
    }

    setMuxing(true)
    setProgress(0)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('video_file', videoFile)

      // 添加所有音频轨道
      audioTracks.forEach((track) => {
        formData.append('audio_files', track.file)
      })

      formData.append('output_filename', `muxed_${Date.now()}.mp4`)

      const response = await fetch(`${API_BASE_URL}/api/tools/mux-audio-video`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()

      if (data.success) {
        setTaskId(data.data.task_id)
        toast({
          title: '开始合成',
          description: `正在合成视频和${audioTracks.length}个音频轨道...`
        })
        pollMuxStatus(data.data.task_id)
      } else {
        toast({
          title: '合成失败',
          description: data.error,
          variant: 'destructive'
        })
        setMuxing(false)
      }
    } catch {
      toast({
        title: '网络错误',
        description: '无法连接到服务器',
        variant: 'destructive'
      })
      setMuxing(false)
    }
  }

  // 轮询任务状态
  const pollMuxStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/tools/download-result/${taskId}/status`)
        const data = await response.json()

        if (data.success && data.data) {
          const task = data.data as TaskResponse

          setProgress(task.progress || 0)

          if (task.status === 'completed' && task.result) {
            clearInterval(interval)
            setMuxing(false)
            setResult(task.result)
            toast({
              title: '合成完成',
              description: `视频文件已生成 (${task.result.file_size_mb}MB)`
            })
          } else if (task.status === 'error' || task.status === 'failed') {
            clearInterval(interval)
            setMuxing(false)
            toast({
              title: '合成失败',
              description: '处理过程中发生错误',
              variant: 'destructive'
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
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            音视频合成工具
          </CardTitle>
          <CardDescription>
            将视频和多个音频轨道合成为完整的视频文件，支持多音频混音
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 视频文件上传区域 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">视频文件</label>
            {!videoFile ? (
              <div {...getVideoRootProps()} className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isVideoDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              )}>
                <input {...getVideoInputProps()} />
                <Film className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">{isVideoDragActive ? '放开以上传' : '拖放视频文件到这里'}</p>
                <p className="text-xs text-muted-foreground mt-2">支持 MP4, MKV, AVI, MOV, WebM 格式</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <Film className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium truncate">{videoFile.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(videoFile.size / 1024 / 1024).toFixed(2)} MB - 视频
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={removeVideo}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* 视频预览 */}
                {videoUrl && (
                  <div className="relative aspect-video bg-black rounded-lg overflow-hidden border">
                    <video
                      controls
                      className="w-full h-full"
                      src={videoUrl}
                    >
                      您的浏览器不支持视频预览
                    </video>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 音频文件上传区域 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">音频轨道 ({audioTracks.length})</label>

            {/* 音频轨道列表 */}
            {audioTracks.length > 0 && (
              <div className="space-y-2 mb-3">
                {audioTracks.map((track, index) => (
                  <div key={track.id} className="border rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Music className="h-5 w-5 text-primary" />
                        <div>
                          <p className="text-sm font-medium">轨道 {index + 1}: {track.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {(track.file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeAudioTrack(track.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* 音频预览 */}
                    <audio
                      controls
                      className="w-full h-10"
                      src={track.url}
                    >
                      您的浏览器不支持音频预览
                    </audio>
                  </div>
                ))}
              </div>
            )}

            {/* 添加音频按钮 */}
            <div {...getAudioRootProps()} className={cn(
              "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
              isAudioDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
            )}>
              <input {...getAudioInputProps()} />
              <div className="flex items-center justify-center gap-2">
                <Plus className="h-5 w-5 opacity-50" />
                <Music className="h-5 w-5 opacity-50" />
              </div>
              <p className="text-sm mt-2">
                {isAudioDragActive ? '放开以添加音频' : audioTracks.length > 0 ? '继续添加音频轨道' : '拖放音频文件到这里'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                支持 MP3, WAV, M4A, FLAC, AAC 格式 • 可添加多个音频轨道
              </p>
            </div>
          </div>

          {/* 进度显示 */}
          {muxing && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                合成中... {progress}%
              </p>
            </div>
          )}

          {/* 开始按钮 */}
          <Button
            onClick={handleMux}
            disabled={!videoFile || audioTracks.length === 0 || muxing}
            className="w-full"
            size="lg"
          >
            <Layers className="h-4 w-4 mr-2" />
            开始合成
          </Button>

          {/* 提示信息 */}
          {!muxing && !result && (
            <div className="text-xs text-muted-foreground space-y-1">
              <p>• 视频编码将保持不变（快速复制）</p>
              <p>• 多个音频轨道将自动混音为单轨</p>
              <p>• 音频将重新编码为AAC格式（192kbps）</p>
              <p>• 合成速度很快，通常只需几秒钟</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 结果显示 */}
      {result && (
        <Card className="bg-green-50 border-green-200">
          <CardHeader>
            <CardTitle className="text-green-900">合成完成</CardTitle>
            <CardDescription className="text-green-700">
              视频已成功合成，可以预览和下载
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-green-200">
              <div className="flex items-center gap-3">
                <Film className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-900">合成视频</p>
                  <p className="text-xs text-green-700">
                    {result.file_size_mb}MB
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                asChild
                className="bg-white"
              >
                <a
                  href={`${API_BASE_URL}/api/tools/audio/${encodeURIComponent(result.video_path)}`}
                  download
                >
                  <Download className="h-4 w-4 mr-1" />
                  下载
                </a>
              </Button>
            </div>

            {/* 视频预览 */}
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden border border-green-200">
              <video
                controls
                className="w-full h-full"
                src={`${API_BASE_URL}/api/tools/audio/${encodeURIComponent(result.video_path)}`}
              >
                您的浏览器不支持视频预览
              </video>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
