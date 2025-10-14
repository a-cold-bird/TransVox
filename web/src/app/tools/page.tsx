'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { useTranslation } from '@/hooks/useTranslation'
import { VideoDownloadTool } from '@/components/tools/VideoDownloadTool'
import { SubtitleEditorTool } from '@/components/tools/SubtitleEditorTool'
import { AudioSeparatorTool } from '@/components/tools/AudioSeparatorTool'
import { TranscribeTool } from '@/components/tools/TranscribeTool'
import { TranslateTool } from '@/components/tools/TranslateTool'
import { SubtitleSlicer } from '@/components/tools/SubtitleSlicer'
import { AudioVideoMuxerTool } from '@/components/tools/AudioVideoMuxerTool'
import { useAppStore } from '@/store/useAppStore'
import { Icon } from '@/components/ui/icon'
import Link from 'next/link'

type ToolTab = 'download' | 'subtitleEditor' | 'audioSeparator' | 'transcribe' | 'translate' | 'workbench' | 'audioVideoMuxer'

export default function ToolsPage() {
  const { t } = useTranslation()
  const activeTab = useAppStore((state) => state.activeToolTab)
  const setActiveTab = useAppStore((state) => state.setActiveToolTab)

  const tools = [
    {
      id: 'subtitleEditor' as ToolTab,
      icon: 'file-lines',
      title: t('tools.subtitleEditor'),
      color: 'text-green-500',
    },
    {
      id: 'audioSeparator' as ToolTab,
      icon: 'music',
      title: t('tools.audioSeparator'),
      color: 'text-orange-500',
    },
    {
      id: 'transcribe' as ToolTab,
      icon: 'microphone',
      title: t('tools.transcribe'),
      color: 'text-pink-500',
    },
    {
      id: 'translate' as ToolTab,
      icon: 'language',
      title: t('tools.translate'),
      color: 'text-purple-500',
    },
    {
      id: 'workbench' as ToolTab,
      icon: 'video',
      title: '字幕切片&TTS',
      color: 'text-indigo-500',
    },
    {
      id: 'audioVideoMuxer' as ToolTab,
      icon: 'layer-group',
      title: '音视频合成',
      color: 'text-cyan-500',
    },
    {
      id: 'download' as ToolTab,
      icon: 'download',
      title: t('tools.download'),
      color: 'text-blue-500',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 relative overflow-hidden">
      {/* 背景装饰 - 简化 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Button variant="ghost" asChild>
            <Link href="/" className="gap-2">
              <Icon icon="arrow-left" className="h-4 w-4" />
              {t('nav.backToHome')}
            </Link>
          </Button>
          <div className="flex items-center gap-3">
            <img src="/asset/icon.png" alt="TransVox" className="h-6 w-6 rounded" />
            <h1 className="text-lg font-semibold text-primary">
              {t('tools.title')}
            </h1>
          </div>
          <LanguageSwitcher />
        </div>

        {/* 工具导航栏 - 简化特效 */}
        <div className="border-t">
          <div className="container mx-auto px-4">
            <nav className="flex gap-2 overflow-x-auto py-3 scrollbar-hide">
              {tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTab(tool.id)}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg transition-colors whitespace-nowrap
                    ${activeTab === tool.id
                      ? 'bg-primary text-primary-foreground font-medium'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'}
                  `}
                >
                  <Icon icon={tool.icon} className="h-4 w-4" />
                  <span>{tool.title}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* 工具内容区域 */}
      <div className="container mx-auto px-4 py-8 relative">
        {/* 使用 CSS 控制显示/隐藏，而不是卸载组件 */}
        <motion.div
          className={activeTab === 'download' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <VideoDownloadTool />
        </motion.div>

        <motion.div
          className={activeTab === 'subtitleEditor' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <SubtitleEditorTool />
        </motion.div>

        <motion.div
          className={activeTab === 'audioSeparator' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <AudioSeparatorTool />
        </motion.div>

        <motion.div
          className={activeTab === 'transcribe' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <TranscribeTool />
        </motion.div>

        <motion.div
          className={activeTab === 'translate' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <TranslateTool />
        </motion.div>

        <motion.div
          className={activeTab === 'workbench' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <SubtitleSlicer />
        </motion.div>

        <motion.div
          className={activeTab === 'audioVideoMuxer' ? 'block' : 'hidden'}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <AudioVideoMuxerTool />
        </motion.div>
      </div>
    </div>
  )
}

