'use client'

import React, { useState, useEffect } from 'react'
import { Save, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { configService } from '@/api/services'
import { useToast } from '@/hooks/use-toast'

interface UserConfig {
  api: {
    gemini_api_key: string
    gemini_base_url: string
    openai_api_key: string
    openai_base_url: string
  }
  translation: {
    api_type: string
    model: string
    source_lang: string
    target_lang: string
  }
  tts: {
    engine: string
  }
  output: {
    save_srt: boolean
  }
}

// 定义每个TTS引擎支持的语言
const TTS_LANGUAGE_SUPPORT = {
  indextts: {
    name: 'IndexTTS',
    description: '推荐，快速高质量',
    languages: ['zh', 'en'],
  },
  gptsovits: {
    name: 'GPT-SoVITS',
    description: '支持更多语言',
    languages: ['zh', 'en', 'ja', 'ko'],
  },
}

// 语言显示名称
const LANGUAGE_NAMES: Record<string, string> = {
  auto: '自动检测',
  zh: '中文',
  en: '英文',
  ja: '日文',
  ko: '韩文',
}

export function UserConfigPanel() {
  const { toast } = useToast()
  const [config, setConfig] = useState<UserConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  // 加载配置
  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const result = await configService.getConfig()

      if (result.success && result.data) {
        setConfig(result.data as UserConfig)
      } else {
        console.error('Failed to load config:', result.error)
      }
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!config) return

    setSaving(true)
    try {
      const result = await configService.updateConfig(config)

      if (result.success) {
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
        toast({
          title: '保存成功',
          description: '配置已保存',
        })
      } else {
        toast({
          title: '保存失败',
          description: result.error || '未知错误',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to save config:', error)
      toast({
        title: '保存失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('确定要重置为默认配置吗？')) return

    setSaving(true)
    try {
      const result = await configService.resetConfig()

      if (result.success && result.data) {
        setConfig(result.data as UserConfig)
        toast({
          title: '重置成功',
          description: '已重置为默认配置',
        })
      } else {
        toast({
          title: '重置失败',
          description: result.error || '未知错误',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to reset config:', error)
      toast({
        title: '重置失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const updateConfig = (path: string[], value: string | boolean) => {
    if (!config) return

    const newConfig = JSON.parse(JSON.stringify(config)) as UserConfig
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let current: Record<string, any> = newConfig

    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]]
    }

    current[path[path.length - 1]] = value
    setConfig(newConfig)
  }

  // 当TTS引擎改变时，检查并调整目标语言
  const handleTTSEngineChange = (newEngine: string) => {
    if (!config) return

    updateConfig(['tts', 'engine'], newEngine)

    // 检查当前目标语言是否被新引擎支持
    const supportedLanguages = TTS_LANGUAGE_SUPPORT[newEngine as keyof typeof TTS_LANGUAGE_SUPPORT]?.languages || []
    const currentTargetLang = config.translation.target_lang

    // 如果当前目标语言不被支持，自动切换到第一个支持的语言
    if (!supportedLanguages.includes(currentTargetLang)) {
      const defaultLang = supportedLanguages[0] || 'zh'
      updateConfig(['translation', 'target_lang'], defaultLang)

      toast({
        title: '语言已自动调整',
        description: `${TTS_LANGUAGE_SUPPORT[newEngine as keyof typeof TTS_LANGUAGE_SUPPORT]?.name} 不支持 ${LANGUAGE_NAMES[currentTargetLang]}，已切换到 ${LANGUAGE_NAMES[defaultLang]}`,
      })
    }
  }

  // 获取当前TTS引擎支持的语言
  const getSupportedLanguages = () => {
    if (!config) return ['zh', 'en']
    const engine = config.tts.engine as keyof typeof TTS_LANGUAGE_SUPPORT
    return TTS_LANGUAGE_SUPPORT[engine]?.languages || ['zh', 'en']
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          加载配置中...
        </CardContent>
      </Card>
    )
  }

  if (!config) {
    return null
  }

  const supportedLanguages = getSupportedLanguages()

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={() => setCollapsed(!collapsed)}>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>工作流配置</CardTitle>
            <CardDescription>
              配置TTS引擎、翻译语言等默认设置
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm">
            {collapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>

      {!collapsed && (
        <CardContent className="space-y-6">
          {/* TTS 设置 - 放在最前面 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">TTS 引擎</h3>

            <div className="space-y-2">
              <label className="text-sm font-medium">选择引擎</label>
              <Select
                value={config.tts.engine}
                onValueChange={handleTTSEngineChange}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="indextts">IndexTTS</SelectItem>
                  <SelectItem value="gptsovits">GPT-SoVITS</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                当前引擎支持：{supportedLanguages.map(lang => LANGUAGE_NAMES[lang]).join('、')}
              </p>
            </div>
          </div>

          {/* 翻译设置 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">翻译设置</h3>
            <p className="text-xs text-muted-foreground">
              翻译引擎和模型请在 <a href="/settings" className="text-primary hover:underline">全局设置</a> 中配置
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">源语言</label>
                <Select
                  value={config.translation.source_lang}
                  onValueChange={(value) => updateConfig(['translation', 'source_lang'], value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">自动检测</SelectItem>
                    {supportedLanguages.map((lang) => (
                      <SelectItem key={lang} value={lang}>
                        {LANGUAGE_NAMES[lang]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">目标语言</label>
                <Select
                  value={config.translation.target_lang}
                  onValueChange={(value) => updateConfig(['translation', 'target_lang'], value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {supportedLanguages.map((lang) => (
                      <SelectItem key={lang} value={lang}>
                        {LANGUAGE_NAMES[lang]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* 输出设置 */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">输出设置</h3>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">保存 SRT 字幕文件</p>
                <p className="text-xs text-muted-foreground">
                  翻译后的字幕文件
                </p>
              </div>
              <input
                type="checkbox"
                checked={config.output.save_srt}
                onChange={(e) => updateConfig(['output', 'save_srt'], e.target.checked)}
                className="w-4 h-4"
              />
            </div>
          </div>

          {/* 保存按钮 */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="flex-1"
            >
              <Save className="h-4 w-4 mr-2" />
              {saving ? '保存中...' : '保存配置'}
            </Button>
            <Button
              onClick={handleReset}
              variant="outline"
              disabled={saving}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              重置
            </Button>
          </div>

          {saved && (
            <div className="text-center text-sm text-green-600 animate-in fade-in">
              配置已保存
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
