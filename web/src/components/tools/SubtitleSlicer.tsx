'use client'

import React, { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { Icon } from '@/components/ui/icon'

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export function SubtitleSlicer() {
  const { toast } = useToast()
  const [srtFile, setSrtFile] = useState<File | null>(null)
  const [mediaFile, setMediaFile] = useState<File | null>(null)
  const [mediaFileUrl, setMediaFileUrl] = useState<string>('')
  const [subtitles, setSubtitles] = useState<SubtitleSegment[]>([])
  const [segments, setSegments] = useState<VideoSegment[]>([])
  const [ttsSegments, setTtsSegments] = useState<TTSSegment[]>([])
  const [processingTask, setProcessingTask] = useState<string | null>(null)
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [playingAudio, setPlayingAudio] = useState<string | null>(null)
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null)
  const [audioProgress, setAudioProgress] = useState<{ [key: string]: number }>({})
  const [audioDurations, setAudioDurations] = useState<{ [key: string]: number }>({})
  const [mergedAudio, setMergedAudio] = useState<{
    audio_path: string
    file_size: number
    file_size_mb: number
    duration_sec: number
    segment_count: number
  } | null>(null)
  const [isMerging, setIsMerging] = useState(false)
  const [generatingTTSIndex, setGeneratingTTSIndex] = useState<number | null>(null)  // 正在生成TTS的片段索引

  // TTS 配置
  const [ttsEngine, setTtsEngine] = useState<'indextts' | 'gptsovits'>('indextts')
  const [promptLang, setPromptLang] = useState<'zh' | 'en' | 'ja' | 'ko'>('en')  // 输入语言（参考音频语言）- 默认英文
  const [textLang, setTextLang] = useState<'zh' | 'en' | 'ja' | 'ko' | 'auto'>('auto')  // 输出语言（目标语言）- 默认auto

  // 音频播放器组件
  const AudioPlayer = ({ audioPath, duration, label }: { audioPath: string; duration: number; label: string }) => {
    const isPlaying = playingAudio === audioPath
    const progress = audioProgress[audioPath] || 0
    const totalDuration = audioDurations[audioPath] || duration

    const formatTime = (seconds: number) => {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const handlePlay = (e: React.MouseEvent) => {
      e.stopPropagation()
      playAudio(audioPath, 'segment')
    }

    const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation()
      if (!currentAudio || playingAudio !== audioPath) return

      const rect = e.currentTarget.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const percentage = clickX / rect.width
      const newTime = percentage * totalDuration

      currentAudio.currentTime = newTime
      setAudioProgress(prev => ({ ...prev, [audioPath]: newTime }))
    }

    return (
      <div className="flex items-center gap-2 w-full">
        <button
          onClick={handlePlay}
          className="p-1 hover:bg-muted rounded flex-shrink-0 transition-colors"
          title={isPlaying ? "暂停" : `播放${label}`}
        >
          {isPlaying ? (
            <Icon icon="pause" className="h-3 w-3 text-foreground" />
          ) : (
            <Icon icon="play" className="h-3 w-3 text-foreground" />
          )}
        </button>

        <div className="flex-1 flex items-center gap-2">
          <div
            className="flex-1 h-1 bg-muted rounded-full cursor-pointer relative group"
            onClick={handleProgressClick}
          >
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${(progress / totalDuration) * 100}%` }}
            />
            <div
              className="absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-primary rounded-full shadow transition-all"
              style={{ left: `${(progress / totalDuration) * 100}%`, transform: 'translate(-50%, -50%)' }}
            />
          </div>

          <span className="text-xs text-muted-foreground flex-shrink-0 w-10 text-right">
            {formatTime(progress)}/{formatTime(totalDuration)}
          </span>
        </div>
      </div>
    )
  }

  // 处理SRT文件上传
  const handleSrtUpload = useCallback(async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/upload-srt`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        setSubtitles(data.data.subtitles)
        toast({
          title: "SRT文件上传成功",
          description: `已解析 ${data.data.subtitles.length} 条字幕`
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
  }, [toast])

  // 处理媒体文件上传
  const handleMediaUpload = useCallback(async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/upload-media`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        toast({
          title: "媒体文件上传成功",
          description: "文件已准备就绪"
        })
      } else {
        toast({
          title: "媒体文件上传失败",
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
  }, [toast])

  // SRT文件拖拽
  const onSrtDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      if (file.name.endsWith('.srt')) {
        setSrtFile(file)
        handleSrtUpload(file)
      } else {
        toast({
          title: '文件格式错误',
          description: '请上传.srt格式的字幕文件',
          variant: 'destructive'
        })
      }
    }
  }, [handleSrtUpload, toast])

  const { getRootProps: getSrtRootProps, getInputProps: getSrtInputProps, isDragActive: isSrtDragActive } = useDropzone({
    onDrop: onSrtDrop,
    accept: { 'application/x-subrip': ['.srt'] },
    maxFiles: 1,
  })

  // 媒体文件拖拽
  const onMediaDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setMediaFile(file)
      const url = URL.createObjectURL(file)
      setMediaFileUrl(url)
      handleMediaUpload(file)
    }
  }, [handleMediaUpload])

  const { getRootProps: getMediaRootProps, getInputProps: getMediaInputProps, isDragActive: isMediaDragActive } = useDropzone({
    onDrop: onMediaDrop,
    accept: {
      'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.aac']
    },
    maxFiles: 1,
  })

  
  const isVideoFile = (file: File) => {
    return file.type.startsWith('video/') ||
           ['.mp4', '.avi', '.mov', '.mkv', '.webm'].some(ext =>
             file.name.toLowerCase().endsWith(ext))
  }

  // 提取视频/音频片段
  const extractSegments = async () => {
    if (!srtFile || !mediaFile) {
      toast({
        title: "请先上传文件",
        description: "需要同时上传SRT文件和媒体文件",
        variant: "destructive"
      })
      return
    }

    setProcessingTask('extract')
    setProgress(0)
    try {
      const formData = new FormData()
      if (srtFile) formData.append('srt_file', srtFile)
      if (mediaFile) formData.append('media_file', mediaFile)
      formData.append('subtitles', JSON.stringify(subtitles))

      const response = await fetch(`${API_BASE_URL}/api/tools/extract-segments`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        setTaskId(data.data.task_id)
        toast({
          title: "开始提取片段",
          description: "正在后台处理中..."
        })
        pollTaskStatus(data.data.task_id, 'extract')
      } else {
        toast({
          title: "提取片段失败",
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
  const generateBatchTTS = async () => {
    if (subtitles.length === 0) {
      toast({
        title: "请先上传SRT文件",
        description: "需要字幕文件才能生成TTS",
        variant: "destructive"
      })
      return
    }

    if (segments.length === 0) {
      toast({
        title: "请先提取音频切片",
        description: "音频切片是生成TTS的必需语音参考，请先提取音频切片",
        variant: "destructive"
      })
      return
    }

    // 检查每个字幕是否都有对应的音频切片
    const missingSegments = subtitles.filter(subtitle =>
      !segments.find(seg => seg.index === subtitle.index)
    )

    if (missingSegments.length > 0) {
      toast({
        title: "缺少音频切片",
        description: `字幕片段 ${missingSegments.map(s => s.index).join(', ')} 缺少对应的音频切片，无法生成TTS`,
        variant: "destructive"
      })
      return
    }

    setProcessingTask('tts')
    setProgress(0)
    try {
      const formData = new FormData()
      formData.append('engine', ttsEngine)
      formData.append('subtitles', JSON.stringify(subtitles))
      formData.append('segments_json', JSON.stringify(segments))

      // GPT-SoVITS 需要额外的语言参数
      if (ttsEngine === 'gptsovits') {
        formData.append('prompt_lang', promptLang)
        formData.append('text_lang', textLang)
      }

      const response = await fetch(`${API_BASE_URL}/api/tools/generate-tts`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        setTaskId(data.data.task_id)
        const engineName = ttsEngine === 'indextts' ? 'IndexTTS' : 'GPT-SoVITS'
        toast({
          title: "开始生成TTS",
          description: `正在使用 ${engineName} 为 ${subtitles.length} 个字幕片段生成TTS语音...`
        })
        pollTaskStatus(data.data.task_id, 'tts')
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

  // 生成单个TTS
  const generateSingleTTS = async (segmentIndex: number) => {
    // 检查是否有对应的音频切片
    const segment = segments.find(s => s.index === segmentIndex)
    if (!segment) {
      toast({
        title: "缺少音频切片",
        description: `片段 ${segmentIndex} 缺少对应的音频切片，无法生成TTS`,
        variant: "destructive"
      })
      return
    }

    // 立即设置loading状态
    setGeneratingTTSIndex(segmentIndex)

    try {
      const formData = new FormData()
      formData.append('segment_index', segmentIndex.toString())
      formData.append('subtitles', JSON.stringify(subtitles))
      formData.append('segments_json', JSON.stringify(segments))
      formData.append('engine', ttsEngine)

      // GPT-SoVITS 需要额外的语言参数
      if (ttsEngine === 'gptsovits') {
        formData.append('prompt_lang', promptLang)
        formData.append('text_lang', textLang)
      }

      const response = await fetch(`${API_BASE_URL}/api/tools/regenerate-tts`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        const engineName = ttsEngine === 'indextts' ? 'IndexTTS' : 'GPT-SoVITS'
        toast({
          title: "开始生成TTS",
          description: `片段 ${segmentIndex} 正在使用 ${engineName} 处理中...`
        })
        pollTaskStatus(data.data.task_id, 'regenerate')
      } else {
        setGeneratingTTSIndex(null)  // 失败时清除loading状态
        toast({
          title: "生成TTS失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      setGeneratingTTSIndex(null)  // 出错时清除loading状态
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    }
  }

  // 重新生成单个TTS
  const regenerateSingleTTS = async (segmentIndex: number) => {
    // 立即设置loading状态
    setGeneratingTTSIndex(segmentIndex)

    try {
      const formData = new FormData()
      formData.append('segment_index', segmentIndex.toString())
      formData.append('subtitles', JSON.stringify(subtitles))
      formData.append('segments_json', JSON.stringify(segments))
      formData.append('engine', ttsEngine)

      // GPT-SoVITS 需要额外的语言参数
      if (ttsEngine === 'gptsovits') {
        formData.append('prompt_lang', promptLang)
        formData.append('text_lang', textLang)
      }

      const response = await fetch(`${API_BASE_URL}/api/tools/regenerate-tts`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        const engineName = ttsEngine === 'indextts' ? 'IndexTTS' : 'GPT-SoVITS'
        toast({
          title: "开始重新生成TTS",
          description: `片段 ${segmentIndex} 正在使用 ${engineName} 处理中...`
        })
        pollTaskStatus(data.data.task_id, 'regenerate')
      } else {
        setGeneratingTTSIndex(null)  // 失败时清除loading状态
        toast({
          title: "重新生成TTS失败",
          description: data.error,
          variant: "destructive"
        })
      }
    } catch (error) {
      setGeneratingTTSIndex(null)  // 出错时清除loading状态
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
    }
  }

  // 合并TTS音频
  const mergeTTSAudio = async () => {
    if (ttsSegments.length === 0) {
      toast({
        title: "请先生成TTS",
        description: "需要生成TTS音频后才能合并",
        variant: "destructive"
      })
      return
    }

    // 检查是否有已完成的TTS
    const completedSegments = ttsSegments.filter(t => t.status === 'completed')
    if (completedSegments.length === 0) {
      toast({
        title: "没有可合并的TTS",
        description: "请等待TTS生成完成",
        variant: "destructive"
      })
      return
    }

    setIsMerging(true)
    setProcessingTask('merge')
    setProgress(0)

    try {
      const formData = new FormData()
      formData.append('subtitles', JSON.stringify(subtitles))
      formData.append('tts_segments', JSON.stringify(ttsSegments))
      formData.append('output_filename', `merged_tts_${Date.now()}.wav`)

      const response = await fetch(`${API_BASE_URL}/api/tools/merge-tts-audio`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()

      if (data.success) {
        setTaskId(data.data.task_id)
        toast({
          title: "开始合并TTS音频",
          description: `正在合并 ${completedSegments.length} 个TTS音频切片...`
        })
        pollTaskStatus(data.data.task_id, 'merge')
      } else {
        toast({
          title: "合并TTS音频失败",
          description: data.error,
          variant: "destructive"
        })
        setIsMerging(false)
        setProcessingTask(null)
      }
    } catch (error) {
      toast({
        title: "网络错误",
        description: "无法连接到服务器",
        variant: "destructive"
      })
      setIsMerging(false)
      setProcessingTask(null)
    }
  }

  // 轮询任务状态
  const pollTaskStatus = async (taskId: string, taskType: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/tools/download-result/${taskId}/status`)
        const data = await response.json()

        if (data.success && data.data) {
          const task = data.data as { status: string; progress: number; result?: Record<string, any> }

          setProgress(task.progress || 0)

          // 实时更新TTS片段（即使任务未完成）
          if (taskType === 'tts' && task.result?.tts_segments) {
            setTtsSegments(task.result.tts_segments)
          }

          // 当regenerate任务开始处理时，清除loading状态
          if (taskType === 'regenerate' && task.status === 'processing') {
            setGeneratingTTSIndex(null)
          }

          if (task.status === 'completed' && task.result) {
            clearInterval(interval)
            setProcessingTask(null)
            setGeneratingTTSIndex(null)  // 完成时清除loading状态

            if (taskType === 'extract' && task.result.segments) {
              setSegments(task.result.segments)
            } else if (taskType === 'tts' && task.result.tts_segments) {
              setTtsSegments(task.result.tts_segments)
            } else if (taskType === 'regenerate' && task.result?.tts_segment) {
              // 更新或添加单个TTS片段
              const ttsSegment = task.result.tts_segment
              setTtsSegments(prev => {
                const existingIndex = prev.findIndex(t => t.index === ttsSegment.index)
                if (existingIndex >= 0) {
                  // 更新已存在的
                  return prev.map(t => t.index === ttsSegment.index ? ttsSegment : t)
                } else {
                  // 添加新的
                  return [...prev, ttsSegment]
                }
              })
            } else if (taskType === 'merge' && task.result) {
              // 合并完成
              const mergeResult = task.result as {
                audio_path: string
                file_size: number
                file_size_mb: number
                duration_sec: number
                segment_count: number
              }
              setMergedAudio(mergeResult)
              setIsMerging(false)
              toast({
                title: "TTS音频合并完成",
                description: `已合并 ${mergeResult.segment_count} 个切片，总时长 ${mergeResult.duration_sec.toFixed(1)}秒`
              })
            }
          } else if (task.status === 'error' || task.status === 'failed') {
            clearInterval(interval)
            setProcessingTask(null)
            setIsMerging(false)
            setGeneratingTTSIndex(null)  // 失败时清除loading状态
            toast({
              title: '处理失败',
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <Icon icon="circle-check" className="h-4 w-4 text-green-500 dark:text-green-400" />
      case 'processing':
        return <Icon icon="spinner" spin className="h-4 w-4 text-blue-500 dark:text-blue-400" />
      case 'failed':
        return <Icon icon="circle-xmark" className="h-4 w-4 text-red-500 dark:text-red-400" />
      default:
        return <Icon icon="clock" className="h-4 w-4 text-muted-foreground/50" />
    }
  }

  // 播放音频
  const playAudio = async (audioPath: string, type: 'segment' | 'tts') => {
    try {
      // 如果正在播放同一个音频，则停止
      if (playingAudio === audioPath && currentAudio) {
        currentAudio.pause()
        currentAudio.currentTime = 0
        setPlayingAudio(null)
        setCurrentAudio(null)
        setAudioProgress(prev => ({ ...prev, [audioPath]: 0 }))
        return
      }

      // 停止之前的音频（如果有）
      if (currentAudio) {
        currentAudio.pause()
        currentAudio.currentTime = 0
      }

      setPlayingAudio(audioPath)

      // 构建音频URL - 需要通过API访问服务器上的文件
      const audioUrl = `${API_BASE_URL}/api/tools/audio/${encodeURIComponent(audioPath)}`

      // 创建音频对象并播放
      const audio = new Audio(audioUrl)
      setCurrentAudio(audio)

      // 音频加载完成，获取时长
      audio.onloadedmetadata = () => {
        setAudioDurations(prev => ({ ...prev, [audioPath]: audio.duration }))
      }

      // 更新播放进度
      audio.ontimeupdate = () => {
        setAudioProgress(prev => ({ ...prev, [audioPath]: audio.currentTime }))
      }

      audio.onended = () => {
        setPlayingAudio(null)
        setCurrentAudio(null)
        setAudioProgress(prev => ({ ...prev, [audioPath]: 0 }))
      }

      audio.onerror = (error) => {
        console.error('音频播放失败:', error)
        setPlayingAudio(null)
        setCurrentAudio(null)
        toast({
          title: '播放失败',
          description: '无法播放音频文件',
          variant: 'destructive'
        })
      }

      await audio.play()
    } catch (error) {
      console.error('播放音频时出错:', error)
      setPlayingAudio(null)
      setCurrentAudio(null)
      toast({
        title: '播放失败',
        description: '无法播放音频文件',
        variant: 'destructive'
      })
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>字幕切片与TTS工具</CardTitle>
          <CardDescription>
            上传SRT字幕和媒体文件，按时间戳切片并生成TTS语音
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* SRT文件上传区域 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">字幕文件</label>
            {!srtFile ? (
              <div {...getSrtRootProps()} className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isSrtDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              )}>
                <input {...getSrtInputProps()} />
                <Icon icon="file-lines" className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">{isSrtDragActive ? '放开以上传' : '拖放SRT字幕文件到这里'}</p>
                <p className="text-xs text-muted-foreground mt-2">支持 .srt 格式</p>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <Icon icon="file-lines" className="h-5 w-5 text-primary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium truncate">{srtFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(srtFile.size / 1024).toFixed(2)} KB - SRT字幕
                      {subtitles.length > 0 && (
                        <span className="ml-2 text-green-600">({subtitles.length} 条字幕)</span>
                      )}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => {
                  setSrtFile(null)
                  setSubtitles([])
                }}>
                  <Icon icon="xmark" className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* 媒体文件上传区域 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">媒体文件</label>
            {!mediaFile ? (
              <div {...getMediaRootProps()} className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isMediaDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              )}>
                <input {...getMediaInputProps()} />
                <Icon icon="file-video" className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">{isMediaDragActive ? '放开以上传' : '拖放视频或音频文件到这里'}</p>
                <p className="text-xs text-muted-foreground mt-2">支持 MP4, AVI, MOV, MP3, WAV 等格式</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    {isVideoFile(mediaFile) ? (
                      <Icon icon="file-video" className="h-5 w-5 text-primary" />
                    ) : (
                      <Icon icon="file-audio" className="h-5 w-5 text-primary" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium truncate">{mediaFile.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(mediaFile.size / 1024 / 1024).toFixed(2)} MB - {isVideoFile(mediaFile) ? '视频' : '音频'}
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => {
                    setMediaFile(null)
                    setMediaFileUrl('')
                    // 清理URL对象
                    if (mediaFileUrl) {
                      URL.revokeObjectURL(mediaFileUrl)
                    }
                  }}>
                    <Icon icon="xmark" className="h-4 w-4" />
                  </Button>
                </div>

                {/* 媒体预览 */}
                {mediaFileUrl && (
                  <div className="border rounded-lg overflow-hidden">
                    {isVideoFile(mediaFile) ? (
                      <div className="relative aspect-video bg-black">
                        <video
                          controls
                          className="w-full h-full"
                          src={mediaFileUrl}
                        >
                          您的浏览器不支持视频预览
                        </video>
                      </div>
                    ) : (
                      <audio
                        controls
                        className="w-full"
                        src={mediaFileUrl}
                      >
                        您的浏览器不支持音频预览
                      </audio>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 进度显示 */}
          {processingTask && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                {processingTask === 'extract' ? '提取片段中...' :
                 processingTask === 'tts' ? '生成TTS中...' :
                 processingTask === 'merge' ? '合并TTS音频中...' : '处理中...'} {progress}%
              </p>
            </div>
          )}

          {/* TTS 配置 */}
          {subtitles.length > 0 && (
            <div className="p-4 bg-primary/5 dark:bg-primary/10 rounded-lg border border-primary/20 space-y-3">
              <div className="text-sm font-medium text-foreground">TTS 引擎配置</div>

              {/* 引擎选择 - 下拉框 */}
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground font-medium">TTS 引擎</label>
                <select
                  value={ttsEngine}
                  onChange={(e) => setTtsEngine(e.target.value as 'indextts' | 'gptsovits')}
                  className="w-full py-2 px-3 rounded-md text-sm bg-background border border-input text-foreground font-medium focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="indextts">IndexTTS - 零样本语音克隆（中文/英文）</option>
                  <option value="gptsovits">GPT-SoVITS - 多语言支持（中文/英文/日文/韩文）</option>
                </select>
              </div>

              {/* GPT-SoVITS 语言配置 */}
              {ttsEngine === 'gptsovits' && (
                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border">
                  {/* 输入语言 */}
                  <div className="space-y-2">
                    <label className="text-xs text-muted-foreground font-medium">输入语言（参考音频）</label>
                    <select
                      value={promptLang}
                      onChange={(e) => setPromptLang(e.target.value as 'zh' | 'en' | 'ja' | 'ko')}
                      className="w-full py-2 px-3 rounded-md text-sm bg-background border border-input text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="en">English</option>
                      <option value="zh">中文</option>
                      <option value="ja">日本語</option>
                      <option value="ko">한국어</option>
                    </select>
                  </div>

                  {/* 输出语言 */}
                  <div className="space-y-2">
                    <label className="text-xs text-muted-foreground font-medium">输出语言（目标语言）</label>
                    <select
                      value={textLang}
                      onChange={(e) => setTextLang(e.target.value as 'zh' | 'en' | 'ja' | 'ko' | 'auto')}
                      className="w-full py-2 px-3 rounded-md text-sm bg-background border border-input text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="auto">自动检测</option>
                      <option value="en">English</option>
                      <option value="zh">中文</option>
                      <option value="ja">日本語</option>
                      <option value="ko">한국어</option>
                    </select>
                  </div>
                </div>
              )}

              <div className="text-xs text-muted-foreground">
                {ttsEngine === 'indextts' ? (
                  '✨ IndexTTS: 零样本语音克隆，自动检测语言'
                ) : (
                  '✨ GPT-SoVITS: 无参考文本模式，使用音频切片作为语音参考'
                )}
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="space-y-4">
            <div className="flex gap-4">
              <Button
                onClick={extractSegments}
                disabled={!srtFile || !mediaFile || processingTask === 'extract'}
                className="flex-1"
              >
                {processingTask === 'extract' ? (
                  <Icon icon="spinner" spin className="h-4 w-4 mr-2" />
                ) : (
                  <Icon icon="scissors" className="h-4 w-4 mr-2" />
                )}
                提取片段
              </Button>
              <Button
                onClick={() => generateBatchTTS()}
                disabled={!srtFile || subtitles.length === 0 || segments.length === 0 || processingTask === 'tts'}
                variant="outline"
                className="flex-1"
                title={segments.length === 0 ? "需要先提取音频切片作为语音参考" : "使用音频切片批量生成TTS语音"}
              >
                {processingTask === 'tts' ? (
                  <Icon icon="spinner" spin className="h-4 w-4 mr-2" />
                ) : (
                  <Icon icon="layer-group" className="h-4 w-4 mr-2" />
                )}
                批量生成
              </Button>
            </div>

            {/* 合并TTS音频按钮 */}
            {ttsSegments.length > 0 && (
              <Button
                onClick={mergeTTSAudio}
                disabled={isMerging || processingTask === 'merge'}
                variant="secondary"
                className="w-full"
              >
                {isMerging ? (
                  <Icon icon="spinner" spin className="h-4 w-4 mr-2" />
                ) : (
                  <Icon icon="code-merge" className="h-4 w-4 mr-2" />
                )}
                合并TTS音频
              </Button>
            )}

            {/* 合并结果显示 */}
            {mergedAudio && (
              <Card className="bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Icon icon="circle-check" className="h-5 w-5 text-green-600 dark:text-green-400" />
                      <div>
                        <p className="text-sm font-medium text-green-900 dark:text-green-100">合并音频已生成</p>
                        <p className="text-xs text-green-700 dark:text-green-300">
                          {mergedAudio.segment_count} 个切片 · {mergedAudio.file_size_mb}MB · {mergedAudio.duration_sec.toFixed(1)}秒
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => playAudio(mergedAudio.audio_path, 'segment')}
                        className="bg-background hover:bg-muted"
                      >
                        {playingAudio === mergedAudio.audio_path ? (
                          <Icon icon="pause" className="h-4 w-4 mr-1" />
                        ) : (
                          <Icon icon="play" className="h-4 w-4 mr-1" />
                        )}
                        播放
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        asChild
                        className="bg-background hover:bg-muted"
                      >
                        <a
                          href={`${API_BASE_URL}/api/tools/audio/${encodeURIComponent(mergedAudio.audio_path)}`}
                          download
                        >
                          <Icon icon="download" className="h-4 w-4 mr-1" />
                          下载
                        </a>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>

      
      {/* 字幕片段表格 */}
      {subtitles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon icon="font" className="h-5 w-5" />
              字幕片段对比表
              <span className="text-sm font-normal text-muted-foreground">
                ({subtitles.length} 条片段)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-2 text-foreground">#</th>
                    <th className="text-left p-2 text-foreground">时间</th>
                    <th className="text-left p-2 text-foreground">字幕内容</th>
                    <th className="text-center p-2 text-foreground">音频切片</th>
                    <th className="text-center p-2 text-foreground">
                      TTS语音
                      <div className="text-xs text-muted-foreground font-normal">
                        使用音频切片作为语音参考
                      </div>
                    </th>
                    <th className="text-center p-2 text-foreground">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {subtitles.map((subtitle) => {
                    const segment = segments.find(s => s.index === subtitle.index)
                    const ttsSegment = ttsSegments.find(t => t.index === subtitle.index)

                    return (
                      <tr
                        key={subtitle.index}
                        className={cn(
                          "border-b border-border hover:bg-muted/50 transition-colors",
                          selectedSegment === subtitle.index && "bg-primary/5"
                        )}
                        onClick={() => setSelectedSegment(subtitle.index)}
                      >
                        <td className="p-2">
                          <div className="flex items-center gap-1">
                            <span className="font-medium text-foreground">{subtitle.index}</span>
                            {subtitle.speaker && (
                              <span className="text-xs bg-muted px-1 rounded text-muted-foreground">
                                {subtitle.speaker}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-2 text-xs text-muted-foreground">
                          <div>{subtitle.start_time}</div>
                          <div>→ {subtitle.end_time}</div>
                        </td>
                        <td className="p-2 max-w-xs">
                          <p className="text-xs line-clamp-2 text-foreground">{subtitle.content}</p>
                        </td>
                        <td className="p-2">
                          {segment ? (
                            <div className="flex flex-col items-start gap-2 p-2">
                              <div className="flex items-center gap-2 w-full">
                                <Icon icon="circle-check" className="h-3 w-3 text-green-500 dark:text-green-400 flex-shrink-0" />
                                <span className="text-xs text-muted-foreground">
                                  {(segment.file_size / 1024).toFixed(1)}KB
                                </span>
                              </div>
                              <AudioPlayer
                                audioPath={segment.file_path}
                                duration={segment.duration}
                                label="切片"
                              />
                            </div>
                          ) : (
                            <div className="flex justify-center">
                              <Icon icon="circle-xmark" className="h-4 w-4 text-muted-foreground/30" />
                            </div>
                          )}
                        </td>
                        <td className="p-2">
                          {ttsSegment ? (
                            <div className="flex flex-col items-start gap-2 p-2">
                              <div className="flex items-center gap-2 w-full">
                                {getStatusIcon(ttsSegment.status)}
                                <span className="text-xs text-muted-foreground">
                                  {(ttsSegment.file_size / 1024).toFixed(1)}KB
                                </span>
                              </div>
                              {ttsSegment.status === 'completed' && (
                                <AudioPlayer
                                  audioPath={ttsSegment.audio_path}
                                  duration={ttsSegment.duration}
                                  label="TTS"
                                />
                              )}
                            </div>
                          ) : (
                            <div className="flex justify-center">
                              <Icon icon="clock" className="h-4 w-4 text-muted-foreground/30" />
                            </div>
                          )}
                        </td>
                        <td className="p-2">
                          <div className="flex items-center justify-center gap-1">
                            {/* 没有音频切片时的提示 */}
                            {!segment && (
                              <div className="text-xs text-muted-foreground/50 italic" title="需要先提取音频切片">
                                需要切片
                              </div>
                            )}

                            {/* 正在生成TTS的加载状态 */}
                            {generatingTTSIndex === subtitle.index && (
                              <div className="flex items-center gap-1.5 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-300 dark:border-blue-700">
                                <Icon icon="spinner" spin className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                                <span className="text-xs text-blue-600 dark:text-blue-400">生成中...</span>
                              </div>
                            )}

                            {/* 生成TTS按钮 - 当有音频切片但没有TTS且不在生成中时显示 */}
                            {!ttsSegment && segment && generatingTTSIndex !== subtitle.index && (
                              <button
                                className="p-1.5 hover:bg-green-100 dark:hover:bg-green-900/30 rounded border border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20 transition-colors"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  generateSingleTTS(subtitle.index)
                                }}
                                title="生成TTS"
                              >
                                <Icon icon="arrows-rotate" className="h-3 w-3 text-green-600 dark:text-green-400" />
                              </button>
                            )}

                            {/* TTS处理中（后端返回的处理状态）*/}
                            {ttsSegment && ttsSegment.status === 'processing' && generatingTTSIndex !== subtitle.index && (
                              <div className="flex items-center gap-1">
                                <Icon icon="spinner" spin className="h-3 w-3 text-blue-500 dark:text-blue-400" />
                                <span className="text-xs text-blue-600 dark:text-blue-400">处理中</span>
                              </div>
                            )}

                            {/* TTS已完成 - 显示重新生成和下载按钮（不在生成中时才显示）*/}
                            {ttsSegment && ttsSegment.status === 'completed' && generatingTTSIndex !== subtitle.index && (
                              <>
                                <button
                                  className="p-1 hover:bg-muted rounded transition-colors"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    regenerateSingleTTS(subtitle.index)
                                  }}
                                  title="重新生成TTS"
                                >
                                  <Icon icon="arrows-rotate" className="h-3 w-3 text-muted-foreground" />
                                </button>
                                <a
                                  href={`${API_BASE_URL}/api/tools/audio/${encodeURIComponent(ttsSegment.audio_path)}`}
                                  download
                                  className="p-1 hover:bg-primary/10 dark:hover:bg-primary/20 rounded transition-colors"
                                  onClick={(e) => e.stopPropagation()}
                                  title="下载TTS音频"
                                >
                                  <Icon icon="download" className="h-3 w-3 text-primary" />
                                </a>
                              </>
                            )}

                            {/* TTS失败 - 显示重试按钮（不在生成中时才显示）*/}
                            {ttsSegment && ttsSegment.status === 'failed' && generatingTTSIndex !== subtitle.index && (
                              <button
                                className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded border border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 transition-colors"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  regenerateSingleTTS(subtitle.index)
                                }}
                                title="重试生成TTS"
                              >
                                <Icon icon="arrows-rotate" className="h-3 w-3 text-red-600 dark:text-red-400" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* 统计信息 */}
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex justify-around text-xs text-muted-foreground">
                <div className="text-center">
                  <div className="font-medium text-sm text-foreground">{segments.length}</div>
                  <div>已提取切片</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-sm text-foreground">
                    {ttsSegments.filter(t => t.status === 'completed').length}
                  </div>
                  <div>已完成TTS</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-sm text-foreground">
                    {ttsSegments.filter(t => t.status === 'failed').length}
                  </div>
                  <div>TTS失败</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-sm text-foreground">
                    {ttsSegments.filter(t => t.status === 'processing').length}
                  </div>
                  <div>处理中</div>
                </div>
              </div>

              {/* TTS语音来源说明 */}
              <div className="mt-4 p-3 bg-primary/5 dark:bg-primary/10 rounded-lg border border-primary/20">
                <div className="text-sm font-medium text-foreground mb-2">TTS语音说明：</div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <div><span className="font-medium text-foreground">语音克隆：</span>每个TTS语音都使用对应的原始音频切片作为语音参考，完美保持原说话人的音色、语速和情感特征</div>
                  <div><span className="font-medium text-foreground">⚠️ 重要：</span>音频切片是生成TTS的必需条件，如果缺少对应的音频切片，该片段将无法生成TTS语音</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}