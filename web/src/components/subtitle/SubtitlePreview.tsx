'use client'

import React, { useState, useEffect } from 'react'
import { X, Download, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { motion } from 'framer-motion'

interface SubtitlePreviewProps {
  subtitlePath: string
  title?: string
  onClose?: () => void
}

export function SubtitlePreview({ subtitlePath, title = '翻译后的字幕', onClose }: SubtitlePreviewProps) {
  const [subtitleContent, setSubtitleContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    loadSubtitle()
  }, [subtitlePath])

  const loadSubtitle = async () => {
    setLoading(true)
    setError(null)

    try {
      // 从API加载字幕文件内容
      const response = await fetch(`http://localhost:8000/api/subtitle/${encodeURIComponent(subtitlePath)}`)

      if (!response.ok) {
        throw new Error('Failed to load subtitle')
      }

      const content = await response.text()
      setSubtitleContent(content)
    } catch (err) {
      console.error('Failed to load subtitle:', err)
      setError('无法加载字幕文件')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    // 创建一个blob并下载
    const blob = new Blob([subtitleContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = subtitlePath.split('/').pop() || 'subtitle.srt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="border-primary/50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <div>
                <CardTitle>{title}</CardTitle>
                <CardDescription>
                  {subtitlePath.split('/').pop()}
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              {!loading && !error && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCollapsed(!collapsed)}
                  >
                    {collapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDownload}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </>
              )}
              {onClose && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        {!collapsed && (
          <CardContent>
            {loading && (
              <div className="text-center py-8 text-muted-foreground">
                加载字幕中...
              </div>
            )}

            {error && (
              <div className="text-center py-8 text-destructive">
                {error}
              </div>
            )}

            {!loading && !error && subtitleContent && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                  <span>共 {subtitleContent.split('\n\n').filter(block => block.trim()).length} 条字幕</span>
                  <span>{(new Blob([subtitleContent]).size / 1024).toFixed(2)} KB</span>
                </div>

                <div className="max-h-[400px] overflow-y-auto rounded-md border bg-muted/30 p-4">
                  <pre className="text-sm whitespace-pre-wrap font-mono">
                    {subtitleContent}
                  </pre>
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </motion.div>
  )
}
