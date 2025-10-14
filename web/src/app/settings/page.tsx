'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Save } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { useTranslation } from '@/hooks/useTranslation'
import Link from 'next/link'
import { useToast } from '@/hooks/use-toast'

interface Settings {
  apiKey: string
  apiBaseUrl: string
  translationProvider: string
  translationApiKey: string
  translationBaseUrl: string
  autoNumbering: boolean
  outputDir: string
  sourceLanguage: string
  targetLanguage: string
  availableModels: string[]
}

// API Response Types
interface GeminiModelInfo {
  name: string
  displayName?: string
}

interface GeminiModelsResponse {
  models: GeminiModelInfo[]
}

interface OpenAIModelInfo {
  id: string
  object: string
  created?: number
}

interface OpenAIModelsResponse {
  data: OpenAIModelInfo[]
  object: string
}

export default function SettingsPage() {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [settings, setSettings] = useState<Settings>({
    apiKey: '',
    apiBaseUrl: 'http://localhost:8000',
    translationProvider: 'gemini',
    translationApiKey: '',
    translationBaseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    autoNumbering: true,
    outputDir: './output',
    sourceLanguage: 'en',
    targetLanguage: 'zh',
    availableModels: ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-2.0-flash-thinking-exp'],
  })
  const [saved, setSaved] = useState(false)
  const [detectingModels, setDetectingModels] = useState(false)
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash')

  useEffect(() => {
    // 从后端加载配置
    const loadConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config')
        const result = await response.json()

        if (result.success && result.data) {
          const config = result.data

          // 转换后端配置格式到前端格式
          const loadedSettings: Settings = {
            apiKey: '',
            apiBaseUrl: 'http://localhost:8000',
            translationProvider: config.translation?.api_type || 'gemini',
            translationApiKey: config.api?.gemini_api_key || config.api?.openai_api_key || '',
            translationBaseUrl: config.api?.gemini_base_url || config.api?.openai_base_url ||
                                (config.translation?.api_type === 'gemini'
                                  ? 'https://generativelanguage.googleapis.com/v1beta'
                                  : 'https://api.openai.com/v1'),
            autoNumbering: true,
            outputDir: './output',
            sourceLanguage: config.translation?.source_lang || 'auto',
            targetLanguage: config.translation?.target_lang || 'zh',
            availableModels: ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-2.0-flash-thinking-exp'],
          }

          setSettings(loadedSettings)
          setSelectedModel(config.translation?.model || 'gemini-2.5-flash')
        }
      } catch (error) {
        console.error('Load config error:', error)
        // 如果后端加载失败，尝试从 localStorage 加载
        const saved = localStorage.getItem('transvox-settings')
        if (saved) {
          setSettings(JSON.parse(saved))
        }
      }
    }

    loadConfig()
  }, [])

  const handleSave = async () => {
    try {
      // 先获取当前配置，保留语言设置
      const currentConfigResponse = await fetch('http://localhost:8000/api/config')
      const currentConfigResult = await currentConfigResponse.json()
      const currentConfig = currentConfigResult.success ? currentConfigResult.data : {}

      // 构建符合后端格式的配置对象，保留原有的语言设置
      const configData = {
        api: {
          gemini_api_key: settings.translationProvider === 'gemini' ? settings.translationApiKey : '',
          gemini_base_url: settings.translationProvider === 'gemini' ? settings.translationBaseUrl : '',
          openai_api_key: settings.translationProvider === 'openai' ? settings.translationApiKey : '',
          openai_base_url: settings.translationProvider === 'openai' ? settings.translationBaseUrl : '',
        },
        translation: {
          api_type: settings.translationProvider,
          model: selectedModel,
          // 保留原有的语言设置，不要覆盖
          source_lang: currentConfig.translation?.source_lang || 'auto',
          target_lang: currentConfig.translation?.target_lang || 'zh',
        },
      }

      // 调用后端API保存配置
      const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configData),
      })

      const result = await response.json()

      if (result.success) {
        // 同时保存到localStorage
        localStorage.setItem('transvox-settings', JSON.stringify(settings))
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
        toast({
          title: '保存成功',
          description: '配置已保存到服务器',
        })
      } else {
        toast({
          title: '保存失败',
          description: result.error || '未知错误',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Save config error:', error)
      toast({
        title: '保存失败',
        description: error instanceof Error ? error.message : '网络错误',
        variant: 'destructive',
      })
    }
  }

  const handleReset = () => {
    const defaultSettings: Settings = {
      apiKey: '',
      apiBaseUrl: 'http://localhost:8000',
      translationProvider: 'gemini',
      translationApiKey: '',
      translationBaseUrl: 'https://generativelanguage.googleapis.com/v1beta',
      autoNumbering: true,
      outputDir: './output',
      sourceLanguage: 'en',
      targetLanguage: 'zh',
      availableModels: ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-2.0-flash-thinking-exp'],
    }
    setSettings(defaultSettings)
    localStorage.setItem('transvox-settings', JSON.stringify(defaultSettings))
  }

  const handleDetectModels = async () => {
    setDetectingModels(true)
    try {
      // 移除末尾的斜杠
      const baseUrl = settings.translationBaseUrl.replace(/\/+$/, '')

      // 智能检测：是否已经包含版本号路径（如 /v1, /v1beta, /v2 等）
      const hasVersionPath = /\/v\d+[a-z]*$/i.test(baseUrl)
      const modelsPath = hasVersionPath ? '/models' : '/v1/models'

      if (settings.translationProvider === 'gemini') {
        // Gemini API 模型列表检测
        const url = `${baseUrl}${modelsPath}?key=${settings.translationApiKey}`
        console.log('检测 URL:', url, `(智能拼接: ${hasVersionPath ? '已有版本号，仅添加/models' : '无版本号，添加/v1/models'})`)

        const response = await fetch(url)
        if (response.ok) {
          const data: GeminiModelsResponse = await response.json()
          const models = data.models
            ?.filter((m) => m.name.includes('gemini'))
            .map((m) => m.name.replace('models/', '')) || []

          if (models.length > 0) {
            setSettings({ ...settings, availableModels: models })
            toast({
              title: '检测成功',
              description: `找到 ${models.length} 个可用模型`,
            })
          } else {
            toast({
              title: '未检测到模型',
              description: '未检测到 Gemini 模型',
              variant: 'destructive',
            })
          }
        } else {
          const errorText = await response.text()
          console.error('API 响应错误:', response.status, errorText)
          toast({
            title: '检测失败',
            description: `API 返回 ${response.status}，请检查 Base URL 和 API Key`,
            variant: 'destructive',
          })
        }
      } else if (settings.translationProvider === 'openai') {
        // OpenAI-like API 模型列表检测
        const url = `${baseUrl}${modelsPath}`
        console.log('检测 URL:', url, `(智能拼接: ${hasVersionPath ? '已有版本号，仅添加/models' : '无版本号，添加/v1/models'})`)

        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${settings.translationApiKey}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data: OpenAIModelsResponse = await response.json()
          const models = data.data?.map((m) => m.id) || []

          if (models.length > 0) {
            setSettings({ ...settings, availableModels: models })
            toast({
              title: '检测成功',
              description: `找到 ${models.length} 个可用模型`,
            })
          } else {
            toast({
              title: '未检测到模型',
              description: '未检测到可用模型',
              variant: 'destructive',
            })
          }
        } else {
          const errorText = await response.text()
          console.error('API 响应错误:', response.status, errorText)
          toast({
            title: '检测失败',
            description: `API 返回 ${response.status}，请检查 Base URL 和 API Key`,
            variant: 'destructive',
          })
        }
      }
    } catch (error) {
      console.error('Model detection error:', error)
      toast({
        title: '网络错误',
        description: error instanceof Error ? error.message : '未知错误',
        variant: 'destructive',
      })
    } finally {
      setDetectingModels(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <header className="border-b bg-background/95 backdrop-blur">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Button variant="ghost" asChild>
            <Link href="/" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              {t('nav.backToHome')}
            </Link>
          </Button>
          <h1 className="text-lg font-semibold">{t('settings.title')}</h1>
          <LanguageSwitcher />
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* API 设置 - 已删除，TransVox 后端 API 配置无实际用途 */}
            {/* <Card>
              <CardHeader>
                <CardTitle>{t('settings.api')}</CardTitle>
                <CardDescription>配置 API 连接信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('settings.apiKey')}</label>
                  <input
                    type="password"
                    value={settings.apiKey}
                    onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
                    placeholder="输入 API Key"
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('settings.baseUrl')}</label>
                  <input
                    type="url"
                    value={settings.apiBaseUrl}
                    onChange={(e) => setSettings({ ...settings, apiBaseUrl: e.target.value })}
                    placeholder="http://localhost:8000"
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </CardContent>
            </Card> */}

            {/* 翻译设置 */}
            <Card>
              <CardHeader>
                <CardTitle>{t('settings.translation')}</CardTitle>
                <CardDescription>翻译 API 和模型配置</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('settings.provider')}</label>
                  <Select
                    value={settings.translationProvider}
                    onValueChange={(value) => setSettings({ ...settings, translationProvider: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gemini">Gemini API（推荐）</SelectItem>
                      <SelectItem value="openai">OpenAI-like API</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {(settings.translationProvider === 'gemini' || settings.translationProvider === 'openai') && (
                  <>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">API Key</label>
                      <input
                        type="password"
                        value={settings.translationApiKey}
                        onChange={(e) => setSettings({ ...settings, translationApiKey: e.target.value })}
                        placeholder={settings.translationProvider === 'gemini' ? 'Google Gemini API Key' : 'OpenAI API Key'}
                        className="w-full px-3 py-2 border rounded-md"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">API Base URL</label>
                      <input
                        type="url"
                        value={settings.translationBaseUrl}
                        onChange={(e) => setSettings({ ...settings, translationBaseUrl: e.target.value })}
                        placeholder={settings.translationProvider === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' : 'https://api.openai.com/v1'}
                        className="w-full px-3 py-2 border rounded-md"
                      />
                      <p className="text-xs text-muted-foreground">
                        {settings.translationProvider === 'gemini'
                          ? '可以包含版本号（如 /v1beta）或不包含，系统会智能拼接'
                          : '可以包含版本号（如 /v1）或不包含，系统会智能拼接'}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium">翻译模型</label>
                        <Button
                          onClick={handleDetectModels}
                          disabled={!settings.translationApiKey || detectingModels}
                          variant="outline"
                          size="sm"
                        >
                          {detectingModels ? '检测中...' : '检测可用模型'}
                        </Button>
                      </div>
                      <Select
                        value={selectedModel}
                        onValueChange={setSelectedModel}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {settings.availableModels.map((model) => (
                            <SelectItem key={model} value={model}>
                              {model}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        点击&ldquo;检测可用模型&rdquo;按钮从 API 端点获取最新模型列表
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* 项目设置 - 已隐藏，相关配置已移至 workspace */}
            {/* <Card>
              <CardHeader>
                <CardTitle>{t('settings.project')}</CardTitle>
                <CardDescription>项目输出和文件管理</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('settings.outputDir')}</label>
                  <input
                    type="text"
                    value={settings.outputDir}
                    onChange={(e) => setSettings({ ...settings, outputDir: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{t('settings.autoNumbering')}</p>
                    <p className="text-xs text-muted-foreground">
                      {t('settings.autoNumberingDesc')}
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.autoNumbering}
                    onChange={(e) => setSettings({ ...settings, autoNumbering: e.target.checked })}
                    className="w-4 h-4"
                  />
                </div>
              </CardContent>
            </Card> */}

            {/* 保存按钮 */}
            <div className="flex gap-4">
              <Button onClick={handleSave} className="flex-1" size="lg">
                <Save className="h-4 w-4 mr-2" />
                {t('settings.save')}
              </Button>
              <Button onClick={handleReset} variant="outline" size="lg">
                {t('settings.reset')}
              </Button>
            </div>

            {saved && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center text-sm text-green-600"
              >
                {t('settings.saved')}
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}

