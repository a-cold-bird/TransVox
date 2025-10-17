'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Download, Plus, Trash2, FileText, Play, Pause, X } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/useAppStore'

interface SubtitleEntry {
  id: string
  index: number
  startTime: string
  endTime: string
  startSeconds: number
  endSeconds: number
  text: string
}

// 缓动函数：easeInOutCubic - 两端慢中间快（用于字幕列表滚动）
const easeInOutCubic = (t: number): number => {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2
}

export function SubtitleEditorTool() {
  // 从store获取持久化状态
  const subtitleEditorState = useAppStore((state) => state.subtitleEditorState)
  const setSubtitleEditorState = useAppStore((state) => state.setSubtitleEditorState)

  // 持久化状态 - 从store初始化
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>(subtitleEditorState.subtitles || [])
  const [videoUrl, setVideoUrl] = useState(subtitleEditorState.videoUrl || '')
  const [styleSettings, setStyleSettings] = useState(subtitleEditorState.styleSettings || {
    fontFamily: 'Arial',
    fontSize: 18,
    fontColor: '#FFFFFF',
    bgColor: '#000000',
    bgOpacity: 0.8,
    outlineColor: '#000000',
    outlineWidth: 1,
    bold: false,
    italic: false,
    alignment: 'center' as 'left' | 'center' | 'right',
  })

  // 非持久化状态（页面刷新后重置）
  const [history, setHistory] = useState<SubtitleEntry[][]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [exportFormat, setExportFormat] = useState<'srt' | 'vtt' | 'ass'>('srt')
  const [selectedSubId, setSelectedSubId] = useState<string | null>(null)
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const [isDraggingTimeline, setIsDraggingTimeline] = useState(false)
  const [lastCurrentSubId, setLastCurrentSubId] = useState<string | null>(null)
  const [viewWindowSeconds, setViewWindowSeconds] = useState(18) // 默认视窗18秒

  const videoRef = useRef<HTMLVideoElement>(null)
  const timelineRef = useRef<HTMLDivElement>(null)
  const timelineContainerRef = useRef<HTMLDivElement>(null)
  const subtitleListRef = useRef<HTMLDivElement>(null)
  const videoContainerRef = useRef<HTMLDivElement>(null)
  const subtitleScrollAnimationRef = useRef<number | null>(null)
  const lastScrolledSubIdRef = useRef<string | null>(null)
  const [timelineWidth, setTimelineWidth] = useState<number>(1000) // 缓存时间轴宽度

  // 视频拖拽上传
  const onVideoDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setVideoUrl(URL.createObjectURL(acceptedFiles[0]))
    }
  }, [])

  const { getRootProps: getVideoRootProps, getInputProps: getVideoInputProps, isDragActive: isVideoDragActive } = useDropzone({
    onDrop: onVideoDrop,
    accept: { 'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm'] },
    maxFiles: 1,
  })

  const timeToSeconds = useCallback((timeStr: string): number => {
    try {
      const parts = timeStr.split(':')
      const [hours, minutes] = parts.slice(0, 2).map(Number)
      const seconds = parseFloat(parts[2].replace(',', '.'))
      return hours * 3600 + minutes * 60 + seconds
    } catch {
      return 0
    }
  }, [])

  const parseSRT = useCallback((content: string): SubtitleEntry[] => {
    const blocks = content.trim().split(/\n\s*\n/)
    return blocks.filter(block => block.trim()).map((block, index) => {
      const lines = block.trim().split('\n')
      const timeLine = lines.find(line => line.includes('-->'))
      const [startTime = '00:00:00,000', endTime = '00:00:00,000'] = timeLine?.split('-->').map(s => s.trim()) || []
      const textLines = lines.slice(lines.indexOf(timeLine || '') + 1)
      const text = textLines.join('\n')
      
      return {
        id: `sub-${Date.now()}-${index}`,
        index: index + 1,
        startTime,
        endTime,
        startSeconds: timeToSeconds(startTime),
        endSeconds: timeToSeconds(endTime),
        text,
      }
    })
  }, [timeToSeconds])

  const handleFileImport = useCallback((file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      const parsed = parseSRT(content)
      setSubtitles(parsed)
    }
    reader.readAsText(file)
  }, [parseSRT])

  // 持久化同步：将subtitles同步到store
  useEffect(() => {
    setSubtitleEditorState({ subtitles })
  }, [subtitles, setSubtitleEditorState])

  // 持久化同步：将videoUrl同步到store
  useEffect(() => {
    setSubtitleEditorState({ videoUrl })
  }, [videoUrl, setSubtitleEditorState])

  // 持久化同步：将styleSettings同步到store
  useEffect(() => {
    setSubtitleEditorState({ styleSettings })
  }, [styleSettings, setSubtitleEditorState])

  // 字幕拖拽上传
  const onSubtitleDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      handleFileImport(acceptedFiles[0])
    }
  }, [handleFileImport])

  const { getRootProps: getSubtitleRootProps, getInputProps: getSubtitleInputProps, isDragActive: isSubtitleDragActive } = useDropzone({
    onDrop: onSubtitleDrop,
    accept: { 'text/*': ['.srt', '.vtt', '.ass'] },
    maxFiles: 1,
  })

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleTimeUpdate = () => setCurrentTime(video.currentTime)
    const handleLoadedMetadata = () => setDuration(video.duration)
    const handlePlay = () => setPlaying(true)
    const handlePause = () => setPlaying(false)

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
    }
  }, [videoUrl])

  // 监听时间轴容器尺寸变化，缓存宽度以优化性能
  useEffect(() => {
    const timeline = timelineRef.current
    if (!timeline) return

    // 初始化宽度
    setTimelineWidth(timeline.offsetWidth)

    // 使用ResizeObserver监听尺寸变化
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setTimelineWidth(entry.target.clientWidth)
      }
    })

    resizeObserver.observe(timeline)

    return () => {
      resizeObserver.disconnect()
    }
  }, [duration, viewWindowSeconds])

  // 自动滚动时间轴，保持当前时间指针在固定位置（优化版：直接设置，无卡顿）
  useEffect(() => {
    if (!timelineContainerRef.current || !duration || isDraggingTimeline) return

    const container = timelineContainerRef.current
    const containerWidth = container.offsetWidth
    const pointerPosition = 100 // 指针固定在左侧100px处

    // 计算时间轴总宽度（基于视窗秒数）
    const totalWidth = containerWidth * (duration / viewWindowSeconds)
    const targetScrollPosition = (currentTime / duration) * totalWidth - pointerPosition
    const safeScrollPosition = Math.max(0, Math.min(targetScrollPosition, totalWidth - containerWidth))

    // 直接设置滚动位置，不使用动画，实现最流畅的跟随
    container.scrollLeft = safeScrollPosition
  }, [currentTime, duration, viewWindowSeconds, isDraggingTimeline])

  // 监听当前字幕变化，自动选中并滚动列表（优化版：使用RAF替代setTimeout）
  useEffect(() => {
    const currentSub = subtitles.find(sub =>
      currentTime >= sub.startSeconds && currentTime <= sub.endSeconds
    )

    // 如果当前字幕改变了
    if (currentSub && currentSub.id !== lastCurrentSubId) {
      setLastCurrentSubId(currentSub.id)
      setSelectedSubId(currentSub.id)

      // 防止重复滚动到同一个字幕
      if (lastScrolledSubIdRef.current === currentSub.id) {
        return
      }
      lastScrolledSubIdRef.current = currentSub.id

      // 取消之前的滚动动画
      if (subtitleScrollAnimationRef.current !== null) {
        cancelAnimationFrame(subtitleScrollAnimationRef.current)
      }

      // 使用requestAnimationFrame确保DOM已更新
      subtitleScrollAnimationRef.current = requestAnimationFrame(() => {
        const element = document.getElementById(`subtitle-${currentSub.id}`)
        if (element && subtitleListRef.current) {
          const container = subtitleListRef.current
          const elementRect = element.getBoundingClientRect()
          const containerRect = container.getBoundingClientRect()

          // 计算元素相对于容器的位置
          const elementTop = element.offsetTop
          const elementHeight = elementRect.height
          const containerHeight = containerRect.height
          const containerScrollTop = container.scrollTop

          // 计算目标滚动位置（让元素居中）
          const targetScrollTop = elementTop - containerHeight / 2 + elementHeight / 2

          // 获取当前滚动位置和距离
          const distance = targetScrollTop - containerScrollTop

          // 如果距离很小，不滚动
          if (Math.abs(distance) < 10) {
            subtitleScrollAnimationRef.current = null
            return
          }

          // 使用缓动动画实现平滑滚动
          const startScrollTop = containerScrollTop
          const startTime = performance.now()
          const animationDuration = 300 // 300ms动画

          const animateScroll = (currentTimeStamp: number) => {
            const elapsed = currentTimeStamp - startTime
            const progress = Math.min(elapsed / animationDuration, 1)

            // 使用easeInOutCubic缓动
            const easedProgress = easeInOutCubic(progress)
            const newScrollTop = startScrollTop + distance * easedProgress

            container.scrollTop = newScrollTop

            if (progress < 1) {
              subtitleScrollAnimationRef.current = requestAnimationFrame(animateScroll)
            } else {
              subtitleScrollAnimationRef.current = null
            }
          }

          subtitleScrollAnimationRef.current = requestAnimationFrame(animateScroll)
        } else {
          subtitleScrollAnimationRef.current = null
        }
      })
    } else if (!currentSub) {
      setLastCurrentSubId(null)
      lastScrolledSubIdRef.current = null
    }

    // 清理函数
    return () => {
      if (subtitleScrollAnimationRef.current !== null) {
        cancelAnimationFrame(subtitleScrollAnimationRef.current)
        subtitleScrollAnimationRef.current = null
      }
    }
  }, [currentTime, subtitles, lastCurrentSubId])

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (playing) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
    }
  }

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Z 撤销
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault()
        if (historyIndex > 0) {
          setHistoryIndex(historyIndex - 1)
          setSubtitles(history[historyIndex - 1])
        }
      }
      // Ctrl+Y 或 Ctrl+Shift+Z 恢复
      if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'z')) {
        e.preventDefault()
        if (historyIndex < history.length - 1) {
          setHistoryIndex(historyIndex + 1)
          setSubtitles(history[historyIndex + 1])
        }
      }
      // Space 播放/暂停（仅当不在输入框中）
      if (e.code === 'Space' && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault()
        if (videoRef.current) {
          if (playing) {
            videoRef.current.pause()
          } else {
            videoRef.current.play()
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [historyIndex, playing, history])

  // 保存历史记录
  const saveHistory = (newSubtitles: SubtitleEntry[]) => {
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push(newSubtitles)
    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)
    setSubtitles(newSubtitles)
  }

  // 撤销
  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1)
      setSubtitles(history[historyIndex - 1])
    }
  }

  // 恢复
  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1)
      setSubtitles(history[historyIndex + 1])
    }
  }

  const secondsToTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    const ms = Math.floor((s % 1) * 1000)
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${Math.floor(s).toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`
  }

  const exportSubtitles = () => {
    let content = ''
    
    if (exportFormat === 'srt') {
      content = subtitles.map(sub => 
        `${sub.index}\n${sub.startTime} --> ${sub.endTime}\n${sub.text}\n`
      ).join('\n')
    } else if (exportFormat === 'vtt') {
      content = 'WEBVTT\n\n' + subtitles.map(sub => 
        `${sub.index}\n${sub.startTime.replace(',', '.')} --> ${sub.endTime.replace(',', '.')}\n${sub.text}\n`
      ).join('\n')
    } else {
      content = generateASS(subtitles)
    }

    const blob = new Blob([content], { type: 'text/plain; charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `subtitle.${exportFormat}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const generateASS = (subs: SubtitleEntry[]) => {
    const header = `[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, Italic, Alignment
Style: Default,Arial,20,&HFFFFFF&,&H000000&,0,0,2

[Events]
Format: Layer, Start, End, Style, Text
`
    const events = subs.map(sub => {
      return `Dialogue: 0,${sub.startTime.replace(',', '.')},${sub.endTime.replace(',', '.')},Default,,0,0,0,,${sub.text.replace(/\n/g, '\\N')}`
    }).join('\n')

    return header + events
  }

  const addSubtitle = () => {
    const startSeconds = currentTime
    const endSeconds = currentTime + 3
    
    const newSub: SubtitleEntry = {
      id: `sub-${Date.now()}`,
      index: subtitles.length + 1,
      startTime: secondsToTime(startSeconds),
      endTime: secondsToTime(endSeconds),
      startSeconds,
      endSeconds,
      text: '',
    }
    const newList = [...subtitles, newSub].sort((a, b) => a.startSeconds - b.startSeconds).map((sub, idx) => ({
      ...sub,
      index: idx + 1
    }))
    saveHistory(newList)
    setSelectedSubId(newSub.id)
  }

  const deleteSubtitle = (id: string) => {
    const newList = subtitles.filter(sub => sub.id !== id).map((sub, index) => ({
      ...sub,
      index: index + 1,
    }))
    saveHistory(newList)
    if (selectedSubId === id) setSelectedSubId(null)
  }

  const updateSubtitle = (id: string, field: keyof SubtitleEntry, value: string) => {
    const newList = subtitles.map(sub => {
      if (sub.id !== id) return sub
      
      const updated = { ...sub, [field]: value }
      
      if (field === 'startTime') {
        updated.startSeconds = timeToSeconds(value)
      } else if (field === 'endTime') {
        updated.endSeconds = timeToSeconds(value)
      }
      
      return updated
    })
    setSubtitles(newList)
  }

  const saveSubtitleEdit = () => {
    saveHistory([...subtitles])
  }

  const removeSpeakerTags = () => {
    const newList = subtitles.map(sub => ({
      ...sub,
      text: sub.text.replace(/\[speaker_\d+\]\s*/g, '').trim()
    }))
    saveHistory(newList)
  }

  const jumpToTime = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds
    }
  }

  // 拖动时间轴滚动（优化性能，使用 requestAnimationFrame）
  const handleTimelineDragScroll = (startX: number, startScrollLeft: number) => {
    setIsDraggingTimeline(true)
    
    // 暂停视频
    if (videoRef.current && playing) {
      videoRef.current.pause()
    }
    
    let animationFrameId: number | null = null
    
    const handleMove = (moveEvent: MouseEvent) => {
      if (!timelineContainerRef.current || !timelineRef.current) return
      
      // 取消之前的动画帧
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId)
      }
      
      // 使用 requestAnimationFrame 优化性能
      animationFrameId = requestAnimationFrame(() => {
        if (!timelineContainerRef.current || !timelineRef.current) return
        
        const deltaX = startX - moveEvent.clientX // 反向滚动
        const newScrollLeft = Math.max(0, startScrollLeft + deltaX)
        timelineContainerRef.current.scrollLeft = newScrollLeft
        
        // 根据滚动位置计算对应的时间
        const pointerPosition = 100
        const totalWidth = timelineRef.current.offsetWidth
        const currentScrollTime = ((newScrollLeft + pointerPosition) / totalWidth) * duration
        
        // 更新视频时间
        if (videoRef.current) {
          videoRef.current.currentTime = Math.max(0, Math.min(duration, currentScrollTime))
        }
      })
    }
    
    const handleUp = () => {
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId)
      }
      
      setIsDraggingTimeline(false)
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleUp)
      
      // 滚动字幕列表到当前字幕
      setTimeout(() => {
        const currentSub = subtitles.find(sub => 
          currentTime >= sub.startSeconds && currentTime <= sub.endSeconds
        )
        if (currentSub) {
          setSelectedSubId(currentSub.id)
          const element = document.getElementById(`subtitle-${currentSub.id}`)
          if (element && subtitleListRef.current) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }
      }, 100)
    }
    
    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleUp)
  }

  // 统一的字幕拖拽处理函数（修复版：正确保存最新鼠标位置）
  const startSubtitleDrag = (subtitle: SubtitleEntry, type: 'start' | 'end' | 'move', startX: number) => {
    const startTimeValue = type === 'start' ? subtitle.startSeconds : type === 'end' ? subtitle.endSeconds : subtitle.startSeconds
    const initialStartSeconds = subtitle.startSeconds
    const initialEndSeconds = subtitle.endSeconds

    // 立即设置拖拽状态
    setDraggingId(subtitle.id)

    // 使用 RAF 节流 - 保存最新的鼠标位置
    let rafId: number | null = null
    let latestClientX = startX // 保存最新的鼠标X坐标

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!timelineRef.current) return

      // 保存最新的鼠标位置
      latestClientX = moveEvent.clientX

      // 如果已经有RAF在执行，跳过
      if (rafId !== null) return

      rafId = requestAnimationFrame(() => {
        rafId = null

        // 使用最新的鼠标位置计算
        const deltaX = latestClientX - startX
        const deltaSeconds = (deltaX / timelineWidth) * duration

        let newStartSeconds = initialStartSeconds
        let newEndSeconds = initialEndSeconds

        if (type === 'start') {
          newStartSeconds = Math.max(0, Math.min(startTimeValue + deltaSeconds, initialEndSeconds - 0.1))
        } else if (type === 'end') {
          newEndSeconds = Math.max(initialStartSeconds + 0.1, Math.min(duration, startTimeValue + deltaSeconds))
        } else {
          // move: 整体移动
          newStartSeconds = Math.max(0, initialStartSeconds + deltaSeconds)
          newEndSeconds = Math.min(duration, initialEndSeconds + deltaSeconds)
          // 确保不超出边界
          if (newStartSeconds === 0) {
            newEndSeconds = initialEndSeconds - initialStartSeconds
          }
          if (newEndSeconds === duration) {
            newStartSeconds = duration - (initialEndSeconds - initialStartSeconds)
          }
        }

        // 使用RAF节流更新
        setSubtitles(prev => prev.map(sub => {
          if (sub.id !== subtitle.id) return sub
          return {
            ...sub,
            startSeconds: newStartSeconds,
            endSeconds: newEndSeconds,
            startTime: secondsToTime(newStartSeconds),
            endTime: secondsToTime(newEndSeconds),
          }
        }))
      })
    }

    const handleMouseUp = () => {
      // 清理RAF
      if (rafId !== null) {
        cancelAnimationFrame(rafId)
      }

      setDraggingId(null)

      // 使用函数式更新保存最新的state到历史记录
      setSubtitles(currentSubtitles => {
        saveHistory([...currentSubtitles])
        return currentSubtitles
      })

      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  const currentSubtitle = subtitles.find(
    sub => currentTime >= sub.startSeconds && currentTime <= sub.endSeconds
  )

  return (
    <div className="space-y-4">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex gap-2 flex-wrap">
          <div {...getSubtitleRootProps()}>
            <input {...getSubtitleInputProps()} />
            <Button variant="outline" className={cn(isSubtitleDragActive && 'border-primary bg-primary/5')}>
              <Upload className="h-4 w-4 mr-2" />
              {isSubtitleDragActive ? '放开以导入' : '导入字幕'}
            </Button>
          </div>
          {videoUrl && (
            <Button variant="outline" onClick={() => setVideoUrl('')} size="sm">
              <X className="h-4 w-4 mr-2" />
              清除视频
            </Button>
          )}
          {subtitles.length > 0 && (
            <Button variant="outline" onClick={() => saveHistory([])} size="sm">
              <X className="h-4 w-4 mr-2" />
              清空字幕
            </Button>
          )}
          <div className="flex gap-1">
            <Button variant="outline" onClick={undo} disabled={historyIndex <= 0} title="撤销 (Ctrl+Z)" size="sm">
              ↶ 撤销
            </Button>
            <Button variant="outline" onClick={redo} disabled={historyIndex >= history.length - 1} title="恢复 (Ctrl+Y)" size="sm">
              ↷ 恢复
            </Button>
          </div>
        </div>

        <div className="flex gap-2 items-center flex-wrap">
          <span className="text-sm text-muted-foreground">
            {subtitles.length} 条字幕
          </span>
          <Select value={exportFormat} onValueChange={(value: 'srt' | 'vtt' | 'ass') => setExportFormat(value)}>
            <SelectTrigger className="w-24 h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="srt">SRT</SelectItem>
              <SelectItem value="vtt">VTT</SelectItem>
              <SelectItem value="ass">ASS</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={exportSubtitles} disabled={subtitles.length === 0}>
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_400px] gap-4">
        {/* 左侧：视频和时间轴 */}
        <div className="space-y-3">
          {/* 视频播放器 */}
          <Card>
            <CardContent className="p-3">
              {!videoUrl ? (
                <div {...getVideoRootProps()} className={cn(
                  "aspect-video bg-black rounded-lg overflow-hidden cursor-pointer",
                  isVideoDragActive && "ring-2 ring-primary"
                )}>
                  <input {...getVideoInputProps()} />
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="text-center text-muted-foreground">
                      <Upload className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>拖放视频文件到这里</p>
                      <p className="text-sm mt-2">或点击选择文件</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div ref={videoContainerRef} className="relative aspect-video bg-black rounded-lg overflow-hidden">
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    className="w-full h-full cursor-pointer"
                    onClick={togglePlayPause}
                  />
                  {/* 字幕叠加 */}
                  {currentSubtitle && (
                    <div 
                      className="absolute bottom-16 left-0 right-0 px-8 pointer-events-none"
                      style={{ textAlign: styleSettings.alignment }}
                    >
                      <div 
                        className="inline-block px-6 py-3 rounded-lg"
                             style={{
                               fontFamily: styleSettings.fontFamily,
                               fontSize: `${styleSettings.fontSize}px`,
                               color: styleSettings.fontColor,
                               backgroundColor: styleSettings.bgOpacity > 0 
                                 ? `${styleSettings.bgColor}${Math.round(styleSettings.bgOpacity * 255).toString(16).padStart(2, '0')}` 
                                 : 'transparent',
                               fontWeight: styleSettings.bold ? 'bold' : 'normal',
                               fontStyle: styleSettings.italic ? 'italic' : 'normal',
                               textShadow: `
                                 ${styleSettings.outlineWidth}px ${styleSettings.outlineWidth}px 0 ${styleSettings.outlineColor},
                                 -${styleSettings.outlineWidth}px -${styleSettings.outlineWidth}px 0 ${styleSettings.outlineColor},
                                 ${styleSettings.outlineWidth}px -${styleSettings.outlineWidth}px 0 ${styleSettings.outlineColor},
                                 -${styleSettings.outlineWidth}px ${styleSettings.outlineWidth}px 0 ${styleSettings.outlineColor}
                               `,
                               lineHeight: '1.4',
                             }}
                      >
                        {currentSubtitle.text.split('\n').map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* 播放控制覆盖层 */}
                  {!playing && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-16 h-16 bg-black/50 rounded-full flex items-center justify-center">
                        <Play className="h-8 w-8 text-white ml-1" />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 播放控制栏 */}
              {videoUrl && (
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="ghost" onClick={togglePlayPause}>
                      {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    </Button>
                    <span className="text-sm font-mono text-muted-foreground">
                      {new Date(currentTime * 1000).toISOString().substr(11, 8)} / {new Date(duration * 1000).toISOString().substr(11, 8)}
                    </span>
                  </div>

                  {/* 进度条 */}
                  <input
                    type="range"
                    min={0}
                    max={duration || 0}
                    step={0.1}
                    value={currentTime}
                    onChange={(e) => jumpToTime(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* 字幕时间轴 */}
          {videoUrl && duration > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">字幕时间轴</CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">视窗:</span>
                    <Select
                      value={viewWindowSeconds.toString()}
                      onValueChange={(value) => setViewWindowSeconds(parseInt(value))}
                    >
                      <SelectTrigger className="h-7 w-20 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="5">5秒</SelectItem>
                        <SelectItem value="10">10秒</SelectItem>
                        <SelectItem value="15">15秒</SelectItem>
                        <SelectItem value="18">18秒</SelectItem>
                        <SelectItem value="20">20秒</SelectItem>
                        <SelectItem value="30">30秒</SelectItem>
                        <SelectItem value="45">45秒</SelectItem>
                        <SelectItem value="60">60秒</SelectItem>
                        <SelectItem value="90">90秒</SelectItem>
                        <SelectItem value="120">120秒</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 pb-3">
                <div className="relative">
                  {/* 固定的时间指针 - 精简设计 */}
                  <div
                    className="absolute left-[100px] top-0 bottom-0 w-[2px] bg-red-500 z-30 pointer-events-none"
                    style={{ height: '75px', boxShadow: '0 0 6px rgba(239, 68, 68, 0.5)' }}
                  >
                    {/* 顶部时间显示标签 */}
                    <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-red-500 text-white px-1.5 py-0.5 rounded text-[9px] font-mono whitespace-nowrap shadow-md">
                      {new Date(currentTime * 1000).toISOString().substr(11, 8)}
                    </div>
                    {/* 顶部小三角 */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[5px] border-t-red-500" />
                  </div>

                  {/* 可滚动的时间轴容器 - 优化版 */}
                  <div
                    ref={timelineContainerRef}
                    className="relative h-[75px] overflow-x-auto overflow-y-hidden border rounded-lg bg-gradient-to-b from-background to-muted/20 cursor-grab active:cursor-grabbing"
                    style={{ scrollbarWidth: 'thin' }}
                    onMouseDown={(e) => {
                      const target = e.target as HTMLElement
                      // 只有点击空白区域才能拖动滚动
                      if (target === timelineContainerRef.current || target === timelineRef.current) {
                        e.preventDefault()
                        handleTimelineDragScroll(e.clientX, timelineContainerRef.current?.scrollLeft || 0)
                      }
                    }}
                  >
                    <div
                      ref={timelineRef}
                      className="relative h-full"
                      style={{ 
                        width: `${Math.max((duration / viewWindowSeconds) * 100, 100)}%`,
                        minWidth: '100%'
                      }}
                    >
                      {/* 时间刻度线 - 每秒精确刻度 + 智能标签 */}
                      {Array.from({ length: Math.ceil(duration) + 1 }).map((_, i) => {
                        const position = (i / duration) * 100

                        // 根据视窗大小智能显示时间标签
                        // 视窗<=20秒：每2秒显示，21-60秒：每5秒显示，>60秒：每10秒显示
                        let labelInterval = 5
                        if (viewWindowSeconds <= 20) {
                          labelInterval = 2
                        } else if (viewWindowSeconds > 60) {
                          labelInterval = 10
                        }

                        const showLabel = i % labelInterval === 0
                        const isMajor = showLabel

                        return (
                          <div
                            key={i}
                            className={cn(
                              "absolute top-0 pointer-events-none",
                              isMajor
                                ? "border-l-[1.5px] border-muted-foreground/50 h-7"
                                : "border-l border-muted-foreground/20 h-2.5"
                            )}
                            style={{ left: `${position}%` }}
                          >
                            {showLabel && (
                              <span className="absolute top-0.5 left-1.5 text-[8px] text-foreground/70 font-mono bg-background/90 px-0.5 rounded-sm whitespace-nowrap">
                                {Math.floor(i / 60)}:{(i % 60).toString().padStart(2, '0')}
                              </span>
                            )}
                          </div>
                        )
                      })}

                      {/* 字幕条区域 - 单行显示 */}
                      <div className="absolute inset-0 top-8">
                        {subtitles.map((subtitle) => {
                          const left = (subtitle.startSeconds / duration) * 100
                          const width = ((subtitle.endSeconds - subtitle.startSeconds) / duration) * 100
                          const isActive = currentTime >= subtitle.startSeconds && currentTime <= subtitle.endSeconds
                          const isSelected = selectedSubId === subtitle.id
                          
                          // 计算显示的文本，根据实际宽度截断（使用缓存的宽度）
                          const pixelWidth = (width / 100) * timelineWidth
                          const maxChars = Math.floor(pixelWidth / 7)
                          const displayText = subtitle.text.replace(/\n/g, ' ').trim()
                          const truncatedText = displayText.length > maxChars
                            ? displayText.substring(0, Math.max(maxChars - 3, 1)) + '...'
                            : displayText

                          // 是否显示编号（宽度足够时）
                          const showIndex = pixelWidth > 30

                          return (
                            <div
                              key={subtitle.id}
                              className={cn(
                                "absolute top-1/2 -translate-y-1/2 h-7 rounded-md cursor-move",
                                "border border-white/40 backdrop-blur-sm",
                                "transition-all duration-100 ease-out",
                                isActive && "ring-2 ring-red-400 shadow-[0_2px_8px_rgba(248,113,113,0.5)] h-8 z-20",
                                isSelected && "ring-2 ring-blue-400 shadow-[0_2px_8px_rgba(59,130,246,0.4)] z-20",
                                draggingId === subtitle.id && "!transition-none opacity-90 shadow-lg cursor-grabbing",
                                !isActive && !isSelected && "hover:h-8 hover:shadow-sm hover:border-white/60"
                              )}
                              style={{
                                left: `${left}%`,
                                width: `${width}%`,
                                minWidth: '8px',
                                background: isActive
                                  ? 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary)/0.9) 100%)'
                                  : isSelected
                                    ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
                                    : 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
                                boxShadow: isActive
                                  ? '0 2px 8px rgba(248, 113, 113, 0.4), inset 0 1px 0 rgba(255,255,255,0.15)'
                                  : isSelected
                                    ? '0 2px 6px rgba(59, 130, 246, 0.3), inset 0 1px 0 rgba(255,255,255,0.15)'
                                    : '0 1px 3px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.1)',
                              }}
                              onMouseDown={(e) => {
                                // 防止事件冒泡导致多选
                                e.preventDefault()
                                e.stopPropagation()
                                
                                const target = e.target as HTMLElement
                                // 如果点击的是resize handle，不处理
                                if (target.classList.contains('cursor-ew-resize')) {
                                  return
                                }
                                
                                const clickX = e.clientX
                                let moved = false
                                
                                const onMove = (moveEvent: MouseEvent) => {
                                  const distance = Math.abs(moveEvent.clientX - clickX)
                                  if (distance > 3) {
                                    moved = true
                                    // 移除事件监听，开始拖拽
                                    document.removeEventListener('mousemove', onMove)
                                    document.removeEventListener('mouseup', onUp)
                                    startSubtitleDrag(subtitle, 'move', clickX)
                                  }
                                }
                                
                                const onUp = () => {
                                  document.removeEventListener('mousemove', onMove)
                                  document.removeEventListener('mouseup', onUp)
                                  
                                  if (!moved) {
                                    // 纯点击 - 选中并跳转
                                    setSelectedSubId(subtitle.id)
                                    jumpToTime(subtitle.startSeconds)
                                    // 滚动字幕列表
                                    setTimeout(() => {
                                      const element = document.getElementById(`subtitle-${subtitle.id}`)
                                      if (element && subtitleListRef.current) {
                                        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
                                      }
                                    }, 50)
                                  }
                                }
                                
                                document.addEventListener('mousemove', onMove)
                                document.addEventListener('mouseup', onUp)
                              }}
                            >
                              {/* 左边缘拖拽手柄 - B站风格：精致简洁 */}
                              <div
                                className="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize bg-white/0 hover:bg-white/30 active:bg-white/40 transition-colors z-10 group"
                                onMouseDown={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  startSubtitleDrag(subtitle, 'start', e.clientX)
                                }}
                              >
                                <div className="absolute left-0.5 top-1/2 -translate-y-1/2 w-0.5 h-3 bg-white/50 rounded-full group-hover:h-4 group-hover:bg-white/80 transition-all" />
                              </div>

                              {/* 字幕文本和编号 - B站风格：编号更显眼 */}
                              <div className="absolute inset-0 flex items-center px-1.5 overflow-hidden pointer-events-none">
                                {/* 编号标签 - 独立色块，更加显眼 */}
                                <div className={cn(
                                  "flex-shrink-0 px-1.5 py-0.5 rounded-sm font-mono font-bold text-[11px] leading-none",
                                  "shadow-sm",
                                  isActive
                                    ? "bg-red-500/90 text-white"
                                    : isSelected
                                      ? "bg-blue-500/90 text-white"
                                      : "bg-black/60 text-white/95"
                                )}>
                                  #{subtitle.index}
                                </div>
                                {/* 字幕文本 */}
                                {showIndex && pixelWidth > 50 && (
                                  <span className="ml-1.5 text-[10px] text-white/95 font-medium truncate">
                                    {truncatedText}
                                  </span>
                                )}
                              </div>

                              {/* 右边缘拖拽手柄 - B站风格：精致简洁 */}
                              <div
                                className="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize bg-white/0 hover:bg-white/30 active:bg-white/40 transition-colors z-10 group"
                                onMouseDown={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  startSubtitleDrag(subtitle, 'end', e.clientX)
                                }}
                              >
                                <div className="absolute right-0.5 top-1/2 -translate-y-1/2 w-0.5 h-3 bg-white/50 rounded-full group-hover:h-4 group-hover:bg-white/80 transition-all" />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 时间刻度说明 */}
                <div className="flex justify-between items-center mt-1.5 text-xs text-muted-foreground">
                  <span>拖动字幕条调整时间，拖动边缘调整起止点</span>
                  <span className="font-mono">总时长: {new Date(duration * 1000).toISOString().substr(11, 8)}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 右侧：字幕列表和样式设置 */}
        <div className="space-y-4">
          <Card className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>字幕列表</CardTitle>
                  <CardDescription className="mt-1.5">点击跳转并编辑</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    onClick={removeSpeakerTags} 
                    disabled={subtitles.length === 0}
                    size="sm"
                    title="移除所有 [speaker_X] 标签"
                  >
                    <X className="h-3 w-3 mr-1" />
                    清除[speaker]
                  </Button>
                  <Button variant="outline" onClick={addSubtitle} disabled={!videoUrl} size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    添加
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="overflow-hidden">
              <div
                ref={subtitleListRef}
                className="max-h-[350px] overflow-y-auto space-y-2 pr-2"
              >
              {subtitles.length === 0 ? (
                <div {...getSubtitleRootProps()} className={cn(
                  "flex flex-col items-center justify-center h-full border-2 border-dashed rounded-lg p-8",
                  isSubtitleDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25"
                )}>
                  <input {...getSubtitleInputProps()} />
                  <FileText className="h-12 w-12 mb-4 opacity-50" />
                  <p className="text-muted-foreground">拖放字幕文件到这里</p>
                  <p className="text-sm text-muted-foreground mt-2">支持 SRT, VTT, ASS 格式</p>
                </div>
              ) : (
                <AnimatePresence>
                  {subtitles.map((subtitle) => {
                    const isActive = currentTime >= subtitle.startSeconds && currentTime <= subtitle.endSeconds
                    const isSelected = selectedSubId === subtitle.id

                    return (
                      <motion.div
                        key={subtitle.id}
                        id={`subtitle-${subtitle.id}`}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className={cn(
                          "border rounded-lg p-3 transition-all cursor-pointer hover:shadow-md",
                          isActive && "border-primary bg-primary/5 shadow-md",
                          isSelected && "ring-2 ring-blue-500"
                        )}
                        onClick={() => {
                          setSelectedSubId(subtitle.id)
                          jumpToTime(subtitle.startSeconds)
                        }}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <span className="text-xs font-mono font-semibold text-muted-foreground">
                            #{subtitle.index.toString().padStart(3, '0')}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteSubtitle(subtitle.id)
                            }}
                          >
                            <Trash2 className="h-3 w-3 text-destructive" />
                          </Button>
                        </div>

                        <div className="grid grid-cols-2 gap-1 mb-2">
                          <input
                            type="text"
                            value={subtitle.startTime}
                            onChange={(e) => {
                              e.stopPropagation()
                              updateSubtitle(subtitle.id, 'startTime', e.target.value)
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="px-2 py-1 text-xs font-mono border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                            placeholder="00:00:00,000"
                          />
                          <input
                            type="text"
                            value={subtitle.endTime}
                            onChange={(e) => {
                              e.stopPropagation()
                              updateSubtitle(subtitle.id, 'endTime', e.target.value)
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="px-2 py-1 text-xs font-mono border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                            placeholder="00:00:00,000"
                          />
                        </div>

                        <textarea
                          value={subtitle.text}
                          onChange={(e) => {
                            e.stopPropagation()
                            updateSubtitle(subtitle.id, 'text', e.target.value)
                          }}
                          onBlur={saveSubtitleEdit}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-2 py-1.5 text-sm border rounded min-h-[60px] focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                          placeholder="输入字幕文本..."
                        />
                      </motion.div>
                    )
                  })}
                </AnimatePresence>
              )}
              </div>
            </CardContent>
          </Card>

          {/* 样式设置 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">字幕样式</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium">字体</label>
                  <Select
                    value={styleSettings.fontFamily}
                    onValueChange={(value) => setStyleSettings({ ...styleSettings, fontFamily: value })}
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Arial">Arial</SelectItem>
                      <SelectItem value="Microsoft YaHei">微软雅黑</SelectItem>
                      <SelectItem value="LXGW WenKai">霞鹜文楷</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium">字号</label>
                  <input
                    type="number"
                    value={styleSettings.fontSize}
                    onChange={(e) => setStyleSettings({ ...styleSettings, fontSize: parseInt(e.target.value) || 24 })}
                    className="w-full h-8 px-2 border rounded-md text-xs"
                    min="12"
                    max="60"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium">颜色</label>
                  <div className="flex gap-1">
                    <input
                      type="color"
                      value={styleSettings.fontColor}
                      onChange={(e) => setStyleSettings({ ...styleSettings, fontColor: e.target.value })}
                      className="w-8 h-8 rounded border cursor-pointer"
                    />
                    <input
                      type="text"
                      value={styleSettings.fontColor}
                      onChange={(e) => setStyleSettings({ ...styleSettings, fontColor: e.target.value })}
                      className="flex-1 h-8 px-2 border rounded text-[10px] font-mono"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium">描边</label>
                  <div className="flex gap-1">
                    <input
                      type="color"
                      value={styleSettings.outlineColor}
                      onChange={(e) => setStyleSettings({ ...styleSettings, outlineColor: e.target.value })}
                      className="w-8 h-8 rounded border cursor-pointer"
                    />
                    <input
                      type="number"
                      value={styleSettings.outlineWidth}
                      onChange={(e) => setStyleSettings({ ...styleSettings, outlineWidth: parseInt(e.target.value) || 1 })}
                      className="flex-1 h-8 px-2 border rounded text-xs"
                      min="0"
                      max="10"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium">背景色</label>
                  <div className="flex gap-1">
                    <input
                      type="color"
                      value={styleSettings.bgColor}
                      onChange={(e) => setStyleSettings({ ...styleSettings, bgColor: e.target.value })}
                      className="w-8 h-8 rounded border cursor-pointer"
                    />
                    <input
                      type="range"
                      value={styleSettings.bgOpacity}
                      onChange={(e) => setStyleSettings({ ...styleSettings, bgOpacity: parseFloat(e.target.value) })}
                      className="flex-1"
                      min="0"
                      max="1"
                      step="0.1"
                      title={`透明度: ${Math.round(styleSettings.bgOpacity * 100)}%`}
                    />
                    <span className="text-[10px] text-muted-foreground w-8">{Math.round(styleSettings.bgOpacity * 100)}%</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={styleSettings.bold}
                    onChange={(e) => setStyleSettings({ ...styleSettings, bold: e.target.checked })}
                    className="w-3.5 h-3.5"
                  />
                  粗体
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={styleSettings.italic}
                    onChange={(e) => setStyleSettings({ ...styleSettings, italic: e.target.checked })}
                    className="w-3.5 h-3.5"
                  />
                  斜体
                </label>
                <Select
                  value={styleSettings.alignment}
                  onValueChange={(value: 'left' | 'center' | 'right') => setStyleSettings({ ...styleSettings, alignment: value })}
                >
                  <SelectTrigger className="h-7 text-xs w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="left">左</SelectItem>
                    <SelectItem value="center">中</SelectItem>
                    <SelectItem value="right">右</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

