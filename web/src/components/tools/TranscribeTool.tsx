'use client'

import React, { useState, useCallback } from 'react'
import { FileText, Download, Upload } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useTranslation } from '@/hooks/useTranslation'
import { toolService } from '@/api/services'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

export function TranscribeTool() {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [language, setLanguage] = useState('auto')
  const [model, setModel] = useState('large-v3')
  const [enableDiarization, setEnableDiarization] = useState(true)
  const [transcribing, setTranscribing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [srtContent, setSrtContent] = useState<string>('')

  // 高级参数
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [beamSize, setBeamSize] = useState(5)
  const [temperature, setTemperature] = useState(0)
  const [vadThreshold, setVadThreshold] = useState(0.5)
  const [minSpeakers, setMinSpeakers] = useState(1)
  const [maxSpeakers, setMaxSpeakers] = useState(5)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      setResult(null)
      setError(null)
      setTaskId(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm'], 'audio/*': ['.mp3', '.wav', '.m4a', '.flac'] },
    maxFiles: 1,
  })

  const handleTranscribe = async () => {
    if (!file) return

    setTranscribing(true)
    setProgress(0)
    setResult(null)

    try {
      const response = await toolService.transcribeWithOptions(
        file,
        {
          language: language === 'auto' ? undefined : language,
          model,
          enableDiarization,
          beamSize,
          temperature,
          vadThreshold,
          minSpeakers,
          maxSpeakers,
        },
        (prog) => setProgress(prog)
      )

      if (response.success && response.data) {
        setTaskId(response.data.taskId)
        // 开始轮询任务状态
        pollTranscriptionStatus(response.data.taskId)
      } else {
        toast({
          title: '转录失败',
          description: response.error || '未知错误',
          variant: 'destructive',
        })
        setTranscribing(false)
      }
    } catch (error) {
      console.error('Transcription error:', error)
      toast({
        title: '转录失败',
        description: '请检查后端服务是否运行',
        variant: 'destructive',
      })
      setTranscribing(false)
    }
  }

  const pollTranscriptionStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await toolService.downloadResult(taskId, 'status')

        if (response.success && response.data) {
          const task = response.data as { status: string; progress: number; result?: string; message?: string }

          setProgress(task.progress || 0)

          if (task.status === 'completed') {
            clearInterval(interval)
            setTranscribing(false)
            setResult(task.result || `/api/tools/download-result/${taskId}/srt`)
            setError(null)

            // 加载SRT内容用于预览
            loadSrtContent(taskId)
          } else if (task.status === 'error') {
            clearInterval(interval)
            setTranscribing(false)
            setError(task.message || '转录失败')
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
    <div className="max-w-3xl mx-auto space-y-4">
      {/* 主要功能卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>语音转录 - WhisperX</CardTitle>
          <CardDescription>
            使用 WhisperX 高精度语音识别，支持说话人分离
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
                  <FileText className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setFile(null)}>
                  清除
                </Button>
              </div>
            )}
          </div>

          {/* 配置选项 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">音频语言</label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">自动检测</SelectItem>
                  <SelectItem value="en">{t('languages.en')}</SelectItem>
                  <SelectItem value="zh">{t('languages.zh')}</SelectItem>
                  <SelectItem value="ja">{t('languages.ja')}</SelectItem>
                  <SelectItem value="ko">{t('languages.ko')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">WhisperX 模型</label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tiny">Tiny (最快)</SelectItem>
                  <SelectItem value="base">Base (快速)</SelectItem>
                  <SelectItem value="small">Small (平衡)</SelectItem>
                  <SelectItem value="medium">Medium (准确)</SelectItem>
                  <SelectItem value="large-v2">Large-v2 (高精度)</SelectItem>
                  <SelectItem value="large-v3">Large-v3 (最高精度)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 说话人识别选项 - 精简版 */}
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div>
              <p className="text-sm font-medium">启用说话人识别</p>
              <p className="text-xs text-muted-foreground">识别并标注不同说话人（会添加 [speaker_X] 标签）</p>
            </div>
            <input
              type="checkbox"
              checked={enableDiarization}
              onChange={(e) => setEnableDiarization(e.target.checked)}
              className="w-5 h-5 rounded"
            />
          </div>

          {/* 进度显示 */}
          {transcribing && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                识别中... {progress}%
              </p>
            </div>
          )}

          {/* 开始按钮 */}
          <Button
            onClick={handleTranscribe}
            disabled={!file || transcribing}
            className="w-full"
            size="lg"
          >
            <FileText className="h-4 w-4 mr-2" />
            开始识别
          </Button>

          {/* 错误显示 */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-950 rounded-lg border border-red-200 dark:border-red-800">
              <div className="flex items-start gap-3">
                <div className="text-red-600 mt-0.5">✗</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-600">转录失败</p>
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
                      <p className="text-sm font-medium">字幕文件已生成</p>
                      <p className="text-xs text-muted-foreground">subtitle.srt</p>
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
          <div className="text-xs text-muted-foreground space-y-1">
            <p>• Large-v3 模型精度最高，但需要更长时间</p>
            <p>• 自动检测语言可能稍慢，建议手动选择语言</p>
            <p>• 说话人识别会在字幕中添加 [speaker_1], [speaker_2] 等标签</p>
          </div>
        </CardContent>
      </Card>

      {/* 高级参数卡片 - 独立在下方 */}
      <Card>
        <CardHeader>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full flex items-center justify-between text-left"
          >
            <div>
              <CardTitle className="text-base">高级参数</CardTitle>
              <CardDescription className="text-xs mt-1">
                调整识别精度和性能参数
              </CardDescription>
            </div>
            <span className="text-xs text-muted-foreground font-medium">
              {showAdvanced ? '▼ 收起' : '▶ 展开'}
            </span>
          </button>
        </CardHeader>

        {showAdvanced && (
          <CardContent className="space-y-4 pt-0">
            <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-xs text-blue-600 dark:text-blue-400">
                💡 这些参数会影响识别精度和速度，通常保持默认值即可获得最佳效果
              </p>
            </div>

            {/* Beam Size */}
            <div className="space-y-2">
              <label className="text-sm font-medium">束搜索大小 (Beam Size)</label>
              <input
                type="number"
                value={beamSize}
                onChange={(e) => setBeamSize(parseInt(e.target.value) || 5)}
                className="w-full px-3 py-2 border rounded-md text-sm"
                min="1"
                max="10"
              />
              <p className="text-xs text-muted-foreground">
                <strong>默认: 5</strong> | 同时探索多少条识别路径。值越大搜索越全面（精度↑速度↓），1=最快但易错，5=推荐平衡值
              </p>
            </div>

            {/* Temperature 和 VAD Threshold 并排 */}
            <div className="grid grid-cols-2 gap-4">
              {/* Temperature */}
              <div className="space-y-2">
                <label className="text-sm font-medium">采样温度</label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="flex-1"
                    min="0"
                    max="1"
                    step="0.1"
                  />
                  <span className="text-xs font-mono w-8 text-center">{temperature.toFixed(1)}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  随机性控制，0=确定性（推荐）
                </p>
              </div>

              {/* VAD Threshold */}
              <div className="space-y-2">
                <label className="text-sm font-medium">语音检测阈值</label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    value={vadThreshold}
                    onChange={(e) => setVadThreshold(parseFloat(e.target.value))}
                    className="flex-1"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span className="text-xs font-mono w-8 text-center">{vadThreshold.toFixed(2)}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  敏感度，降低可检测轻声片段
                </p>
              </div>
            </div>

            {/* 说话人数量范围 - 只在启用说话人识别时显示 */}
            {enableDiarization && (
              <div className="space-y-4 pt-2 border-t">
                <p className="text-sm font-medium">说话人数量范围</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-xs text-muted-foreground">最少说话人数</label>
                    <input
                      type="number"
                      value={minSpeakers}
                      onChange={(e) => setMinSpeakers(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                      min="1"
                      max={maxSpeakers}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-muted-foreground">最多说话人数</label>
                    <input
                      type="number"
                      value={maxSpeakers}
                      onChange={(e) => setMaxSpeakers(Math.max(minSpeakers, parseInt(e.target.value) || 5))}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                      min={minSpeakers}
                      max="10"
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  <strong>默认: 1-5人</strong> | 预估音频中的说话人数量范围，有助于提高说话人识别准确度
                </p>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  )
}

