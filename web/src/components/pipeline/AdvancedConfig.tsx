'use client'

import React, { useState } from 'react'
import { Settings2, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface AdvancedConfigProps {
  config: Record<string, unknown>
  onChange: (config: Record<string, unknown>) => void
}

export function AdvancedConfig({ config, onChange }: AdvancedConfigProps) {
  const [expanded, setExpanded] = useState(false)

  const updateConfig = (key: string, value: unknown) => {
    onChange({ ...config, [key]: value })
  }

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            <CardTitle>高级设置</CardTitle>
          </div>
          {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </div>
        <CardDescription>
          自定义处理参数和输出选项
        </CardDescription>
      </CardHeader>
      
      {expanded && (
        <CardContent className="space-y-6 pt-0">
          {/* 音频处理 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">音频处理</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">音频采样率</label>
                <Select
                  value={(config.sampleRate as string) || '44100'}
                  onValueChange={(v) => updateConfig('sampleRate', v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="22050">22050 Hz</SelectItem>
                    <SelectItem value="44100">44100 Hz</SelectItem>
                    <SelectItem value="48000">48000 Hz</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">音频通道</label>
                <Select
                  value={(config.channels as string) || '2'}
                  onValueChange={(v) => updateConfig('channels', v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">单声道</SelectItem>
                    <SelectItem value="2">立体声</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* TTS 高级设置 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">TTS 参数</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Temperature</label>
                <input
                  type="number"
                  value={(config.temperature as number) || 1.0}
                  onChange={(e) => updateConfig('temperature', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="0.1"
                  max="2.0"
                  step="0.1"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Top P</label>
                <input
                  type="number"
                  value={(config.topP as number) || 0.8}
                  onChange={(e) => updateConfig('topP', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Top K</label>
                <input
                  type="number"
                  value={(config.topK as number) || 20}
                  onChange={(e) => updateConfig('topK', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="1"
                  max="100"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">批处理大小</label>
                <input
                  type="number"
                  value={(config.batchSize as number) || 4}
                  onChange={(e) => updateConfig('batchSize', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="1"
                  max="16"
                />
              </div>
            </div>
          </div>

          {/* 字幕处理 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">字幕处理</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">最大行字符数</label>
                <input
                  type="number"
                  value={(config.maxLineChars as number) || 40}
                  onChange={(e) => updateConfig('maxLineChars', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="20"
                  max="80"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">字幕字号</label>
                <input
                  type="number"
                  value={(config.subtitleFontSize as number) || 15}
                  onChange={(e) => updateConfig('subtitleFontSize', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="10"
                  max="40"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">AI 智能分行</p>
                <p className="text-xs text-muted-foreground">使用 AI 优化字幕换行</p>
              </div>
              <input
                type="checkbox"
                checked={(config.aiSplitLines as boolean) !== false}
                onChange={(e) => updateConfig('aiSplitLines', e.target.checked)}
                className="w-4 h-4"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">双语字幕</p>
                <p className="text-xs text-muted-foreground">同时显示原文和译文</p>
              </div>
              <input
                type="checkbox"
                checked={(config.bilingual as boolean) || false}
                onChange={(e) => updateConfig('bilingual', e.target.checked)}
                className="w-4 h-4"
              />
            </div>
          </div>

          {/* 视频编码 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">视频编码</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">视频编码器</label>
                <Select
                  value={(config.videoCodec as string) || 'libx264'}
                  onValueChange={(v) => updateConfig('videoCodec', v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="libx264">H.264 (兼容性好)</SelectItem>
                    <SelectItem value="libx265">H.265 (体积小)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">视频质量 (CRF)</label>
                <input
                  type="number"
                  value={(config.crf as number) || 23}
                  onChange={(e) => updateConfig('crf', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md"
                  min="0"
                  max="51"
                />
                <p className="text-xs text-muted-foreground">越小质量越好，推荐 18-28</p>
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
}

