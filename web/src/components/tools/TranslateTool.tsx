'use client'

import React, { useState, useCallback } from 'react'
import { FileText, Download, Upload, Languages } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useTranslation } from '@/hooks/useTranslation'
import { toolService } from '@/api/services'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

interface TranslationTaskResponse {
  status: string
  progress: number
  result?: string
  message?: string
}

export function TranslateTool() {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [targetLang, setTargetLang] = useState('en')
  const [apiType, setApiType] = useState('gemini')
  const [contextPrompt, setContextPrompt] = useState('')
  const [translating, setTranslating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [srtContent, setSrtContent] = useState<string>('')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      // 验证文件格式
      if (!file.name.endsWith('.srt')) {
        setError('仅支持 SRT 格式字幕文件')
        return
      }
      setFile(file)
      setResult(null)
      setError(null)
      setTaskId(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/plain': ['.srt'] },
    maxFiles: 1,
  })

  const handleTranslate = async () => {
    if (!file) return

    setTranslating(true)
    setProgress(0)
    setResult(null)

    try {
      const response = await toolService.translateSubtitle(
        file,
        {
          targetLang,
          contextPrompt,
          apiType,
        },
        (prog) => setProgress(prog)
      )

      if (response.success && response.data) {
        setTaskId(response.data.taskId)
        // 开始轮询任务状态
        pollTranslationStatus(response.data.taskId)
      } else {
        toast({
          title: '翻译失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
        setTranslating(false)
      }
    } catch (error) {
      console.error('Translation error:', error)
      toast({
        title: '翻译失败',
        description: '请检查后端服务是否运行',
        variant: 'destructive',
      })
      setTranslating(false)
    }
  }

  const pollTranslationStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await toolService.downloadResult(taskId, 'status')

        if (response.success && response.data) {
          const task = response.data as TranslationTaskResponse

          setProgress(task.progress || 0)

          if (task.status === 'completed') {
            clearInterval(interval)
            setTranslating(false)
            setResult(task.result || `/api/tools/download-result/${taskId}/srt`)
            setError(null)

            // 加载SRT内容用于预览
            loadSrtContent(taskId)
          } else if (task.status === 'error') {
            clearInterval(interval)
            setTranslating(false)
            setError(task.message || '翻译失败')
          }
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000)

    // 5分钟后停止轮询
    setTimeout(() => clearInterval(interval), 300000)
  }

  const loadSrtContent = async (taskId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/srt`)
      if (response.ok) {
        const content = await response.text()
        setSrtContent(content)
      }
    } catch (error) {
      console.error('Failed to load SRT content:', error)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Languages className="h-5 w-5" />
            字幕翻译
          </CardTitle>
          <CardDescription>
            使用 AI 翻译字幕文件，支持自定义翻译上下文
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 文件上传区域 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">上传字幕文件</label>
            {!file ? (
              <div {...getRootProps()} className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              )}>
                <input {...getInputProps()} />
                <Upload className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">{isDragActive ? '放开以上传' : '拖放 SRT 字幕文件到这里'}</p>
                <p className="text-xs text-muted-foreground mt-2">仅支持 .srt 格式</p>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setFile(null)}>
                  清除
                </Button>
              </div>
            )}
          </div>

          {/* 翻译配置 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">目标语言</label>
              <Select value={targetLang} onValueChange={setTargetLang}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="zh">{t('languages.zh')}</SelectItem>
                  <SelectItem value="en">{t('languages.en')}</SelectItem>
                  <SelectItem value="ja">{t('languages.ja')}</SelectItem>
                  <SelectItem value="ko">{t('languages.ko')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">翻译 API</label>
              <Select value={apiType} onValueChange={setApiType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gemini">Gemini (推荐)</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 翻译上下文 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">翻译上下文（可选）</label>
            <Textarea
              value={contextPrompt}
              onChange={(e) => setContextPrompt(e.target.value)}
              placeholder="在此输入翻译上下文信息，例如：&#10;- 源语言和大致内容&#10;- 专有名词（人名、地名、术语等）&#10;- 特定的翻译要求&#10;&#10;示例：这是一部关于人工智能的科技纪录片。人名：Geoffrey Hinton（杰弗里·辛顿），专业术语：neural network（神经网络）、deep learning（深度学习）"
              className="min-h-[120px] resize-none"
            />
            <p className="text-xs text-muted-foreground">
              提供上下文信息可以让 AI 更准确地翻译专有名词和术语
            </p>
          </div>

          {/* 进度显示 */}
          {translating && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                翻译中... {progress}%
              </p>
            </div>
          )}

          {/* 开始按钮 */}
          <Button
            onClick={handleTranslate}
            disabled={!file || translating}
            className="w-full"
            size="lg"
          >
            <Languages className="h-4 w-4 mr-2" />
            开始翻译
          </Button>

          {/* 错误显示 */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-950 rounded-lg border border-red-200 dark:border-red-800">
              <div className="flex items-start gap-3">
                <div className="text-red-600 mt-0.5">✗</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-600">翻译失败</p>
                  <p className="text-xs text-muted-foreground mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* 结果显示 */}
          {result && (
            <div className="space-y-3">
              <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium">翻译完成</p>
                      <p className="text-xs text-muted-foreground">translated.srt</p>
                    </div>
                  </div>
                  <Button
                    onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/tools/download-result/${taskId}/srt`, '_blank')}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    下载
                  </Button>
                </div>

                {/* SRT内容预览 */}
                <div className="mt-3 p-3 bg-background/50 rounded border max-h-60 overflow-y-auto">
                  <pre className="text-xs font-mono whitespace-pre-wrap">
                    {srtContent || '正在加载字幕内容...'}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* 提示信息 */}
          <div className="text-xs text-muted-foreground space-y-1 border-t pt-4">
            <p className="font-medium mb-2">使用提示：</p>
            <p>• 在翻译上下文中说明源语言可以提高翻译质量</p>
            <p>• 提供专有名词的原文和翻译可以确保一致性</p>
            <p>• Gemini API 速度更快，OpenAI 翻译质量略高</p>
            <p>• 翻译时会自动保留说话人标签（[speaker_X]）</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
