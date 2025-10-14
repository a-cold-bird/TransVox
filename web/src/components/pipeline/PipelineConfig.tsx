'use client'

import React, { useState, useEffect } from 'react'
import { Play, Settings2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTranslation } from '@/hooks/useTranslation'
import type { Language, TTSEngine, PipelineConfig as PipelineConfigType } from '@/types'

interface PipelineConfigProps {
  videoPath: string
  onStart: (config: PipelineConfigType) => void
  disabled?: boolean
}

export function PipelineConfig({ videoPath, onStart, disabled }: PipelineConfigProps) {
  const { t } = useTranslation()
  const [sourceLanguage, setSourceLanguage] = useState<Language>('en')
  const [targetLanguage, setTargetLanguage] = useState<Language>('zh')
  const [ttsEngine, setTTSEngine] = useState<TTSEngine>('gptsovits')

  // 从设置中加载默认值
  useEffect(() => {
    const saved = localStorage.getItem('transvox-settings')
    if (saved) {
      try {
        const settings = JSON.parse(saved)
        if (settings.sourceLanguage) setSourceLanguage(settings.sourceLanguage)
        if (settings.targetLanguage) setTargetLanguage(settings.targetLanguage)
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
  }, [])

  const handleStart = () => {
    const config: PipelineConfigType = {
      videoFile: videoPath,
      outputDir: `output/${Date.now()}`,
      translation: {
        sourceLanguage,
        targetLanguage,
      },
      tts: {
        engine: ttsEngine,
      },
      subtitle: {
        mode: 'hardcode',
        position: 'bottom',
        fontSize: 24,
        fontColor: '#FFFFFF',
        outlineColor: '#000000',
        outlineWidth: 2,
        margin: 10,
      },
    }

    onStart(config)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="h-5 w-5" />
          {t('pipeline.title')}
        </CardTitle>
        <CardDescription>
          {t('pipeline.desc')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Translation Settings */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold">{t('pipeline.translation')}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('pipeline.sourceLanguage')}</label>
              <Select value={sourceLanguage} onValueChange={(v) => setSourceLanguage(v as Language)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">{t('languages.en')}</SelectItem>
                  <SelectItem value="zh">{t('languages.zh')}</SelectItem>
                  <SelectItem value="ja">{t('languages.ja')}</SelectItem>
                  <SelectItem value="ko">{t('languages.ko')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">{t('pipeline.targetLanguage')}</label>
              <Select value={targetLanguage} onValueChange={(v) => setTargetLanguage(v as Language)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">{t('languages.en')}</SelectItem>
                  <SelectItem value="zh">{t('languages.zh')}</SelectItem>
                  <SelectItem value="ja">{t('languages.ja')}</SelectItem>
                  <SelectItem value="ko">{t('languages.ko')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* TTS Settings */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold">{t('pipeline.tts')}</h3>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('pipeline.ttsEngine')}</label>
            <Select value={ttsEngine} onValueChange={(v) => setTTSEngine(v as TTSEngine)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gptsovits">GPT-SoVITS</SelectItem>
                <SelectItem value="indextts">IndexTTS</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Start Button */}
        <Button
          onClick={handleStart}
          disabled={disabled}
          className="w-full"
          size="lg"
        >
          <Play className="h-4 w-4 mr-2" />
          {t('pipeline.startPipeline')}
        </Button>
      </CardContent>
    </Card>
  )
}


