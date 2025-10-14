'use client'

import React from 'react'
import { Download, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

interface VideoPreviewProps {
  videoUrl: string
  title?: string
  onClose?: () => void
}

export function VideoPreview({ videoUrl, title = '视频预览', onClose }: VideoPreviewProps) {
  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = videoUrl
    link.download = title + '.mp4'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <div className="flex items-center gap-2">
          {/* Download Button */}
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            下载
          </Button>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {/* 原生浏览器视频播放器 */}
        <div className="bg-black">
          <video
            src={videoUrl}
            controls
            className="w-full aspect-video"
            style={{ display: 'block' }}
          >
            您的浏览器不支持视频播放
          </video>
        </div>
      </CardContent>
    </Card>
  )
}
