'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { ThemeSwitcher } from '@/components/ThemeSwitcher'
import { useTranslation } from '@/hooks/useTranslation'
import { Icon } from '@/components/ui/icon'
import Link from 'next/link'

export default function HomePage() {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background/95 to-background/90 animated-gradient-bg relative overflow-hidden">
      {/* 背景装饰 - 主题色渐变模糊圆圈 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-3xl" />
        <div className="absolute top-1/3 -left-40 w-96 h-96 bg-gradient-to-tr from-primary/5 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gradient-to-tl from-accent/5 to-transparent rounded-full blur-3xl" />
      </div>

      {/* 完整导航栏 */}
      <header className="border-b border-border/50 bg-background/95 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <img src="/asset/icon.png" alt="TransVox" className="h-8 w-8 rounded-lg" />
            <span className="text-xl font-bold bg-gradient-to-r from-foreground via-foreground/80 to-foreground/60 bg-clip-text text-transparent">
              TransVox
            </span>
          </Link>

          {/* 导航链接 */}
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/workspace" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {t('nav.workspace')}
            </Link>
            <Link href="/tools" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {t('tools.title')}
            </Link>
            <Link href="/settings" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {t('settings.title')}
            </Link>
            <Link href="/docs" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {t('nav.docs')}
            </Link>
            <LanguageSwitcher />
            <ThemeSwitcher />
            <Button asChild size="sm" className="ml-2">
              <Link href="/workspace">
                {t('nav.getStarted')}
                <Icon icon="arrow-right" className="ml-2 h-3.5 w-3.5" />
              </Link>
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero 区域 */}
      <section className="relative pt-24 pb-16 px-6">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            {/* 标题 */}
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-6 leading-tight">
              <span className="block bg-gradient-to-r from-foreground via-foreground/90 to-foreground/70 bg-clip-text text-transparent">
                {t('home.title')}
              </span>
              <span className="block bg-gradient-to-r from-primary via-primary/80 to-accent bg-clip-text text-transparent mt-2">
                {t('home.subtitle')}
              </span>
            </h1>

            {/* 描述 */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              {t('home.description')}
            </p>

            {/* 按钮组 */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Button asChild size="lg" className="px-8">
                <Link href="/workspace">
                  <Icon icon="rocket" className="mr-2 h-5 w-5" />
                  {t('home.startTranslating')}
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="px-8">
                <Link href="/docs">
                  <Icon icon="book" className="mr-2 h-5 w-5" />
                  {t('home.viewDocs')}
                </Link>
              </Button>
            </div>

            {/* 特性标签 */}
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              {['zeroShot', 'multiLang', 'autoSubtitle', 'aiDub', 'oneClick'].map((tag) => (
                <span
                  key={tag}
                  className="px-4 py-2 rounded-lg bg-card/50 border border-border/50 text-muted-foreground backdrop-blur-sm"
                >
                  {t(`home.tags.${tag}`)}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* 核心功能 */}
      <section className="relative py-20 px-6">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-foreground via-foreground/90 to-foreground/70 bg-clip-text text-transparent">
                {t('home.features')}
              </span>
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              {t('home.featuresDesc')}
            </p>
          </motion.div>

          {/* 功能卡片 */}
          <div className="grid md:grid-cols-2 gap-8">
            {/* 声音克隆 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="p-8 rounded-2xl bg-card/50 border border-border/50 backdrop-blur-sm hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all"
            >
              <div className="w-14 h-14 rounded-lg bg-primary/10 flex items-center justify-center mb-6">
                <Icon icon="microphone" className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-2xl font-bold mb-3">{t('features.voiceClone.title')}</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                {t('features.voiceClone.desc')}
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.voiceClone.feature1')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.voiceClone.feature2')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.voiceClone.feature3')}
                </li>
              </ul>
            </motion.div>

            {/* 多语言翻译 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="p-8 rounded-2xl bg-card/50 border border-border/50 backdrop-blur-sm hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all"
            >
              <div className="w-14 h-14 rounded-lg bg-primary/10 flex items-center justify-center mb-6">
                <Icon icon="language" className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-2xl font-bold mb-3">{t('features.multiLang.title')}</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                {t('features.multiLang.desc')}
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.multiLang.feature1')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.multiLang.feature2')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.multiLang.feature3')}
                </li>
              </ul>
            </motion.div>

            {/* 自动字幕 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="p-8 rounded-2xl bg-card/50 border border-border/50 backdrop-blur-sm hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all"
            >
              <div className="w-14 h-14 rounded-lg bg-primary/10 flex items-center justify-center mb-6">
                <Icon icon="file-lines" className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-2xl font-bold mb-3">{t('features.subtitle.title')}</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                {t('features.subtitle.desc')}
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.subtitle.feature1')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.subtitle.feature2')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.subtitle.feature3')}
                </li>
              </ul>
            </motion.div>

            {/* 智能处理 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="p-8 rounded-2xl bg-card/50 border border-border/50 backdrop-blur-sm hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all"
            >
              <div className="w-14 h-14 rounded-lg bg-primary/10 flex items-center justify-center mb-6">
                <Icon icon="wand-magic-sparkles" className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-2xl font-bold mb-3">{t('features.autoProcess.title')}</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                {t('features.autoProcess.desc')}
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.autoProcess.feature1')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.autoProcess.feature2')}
                </li>
                <li className="flex items-center gap-2">
                  <Icon icon="check" className="h-4 w-4 text-primary flex-shrink-0" />
                  {t('features.autoProcess.feature3')}
                </li>
              </ul>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 工作流程 */}
      <section className="relative py-20 px-6 bg-muted/20">
        <div className="container mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-foreground via-foreground/90 to-foreground/70 bg-clip-text text-transparent">
                {t('home.workflow')}
              </span>
            </h2>
            <p className="text-lg text-muted-foreground">
              {t('home.workflowDesc')}
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                titleKey: 'home.step1.title',
                descKey: 'home.step1.desc',
                icon: 'upload',
              },
              {
                step: '02',
                titleKey: 'home.step2.title',
                descKey: 'home.step2.desc',
                icon: 'gear',
              },
              {
                step: '03',
                titleKey: 'home.step3.title',
                descKey: 'home.step3.desc',
                icon: 'download',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                <div className="p-8 rounded-2xl bg-card/50 border border-border/50 backdrop-blur-sm hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Icon icon={item.icon} className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="text-sm font-mono text-primary mb-1">{item.step}</div>
                      <h3 className="text-xl font-bold mb-2">{t(item.titleKey)}</h3>
                    </div>
                  </div>
                  <p className="text-muted-foreground leading-relaxed">{t(item.descKey)}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-20 px-6">
        <div className="container mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="p-12 rounded-2xl bg-gradient-to-br from-primary/90 via-primary/80 to-accent/90 text-primary-foreground text-center border border-primary/20 shadow-2xl"
          >
            <h2 className="text-4xl font-bold mb-4">{t('home.readyTitle')}</h2>
            <p className="text-lg opacity-90 mb-8 max-w-2xl mx-auto">
              {t('home.readyDesc')}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg" className="px-8 bg-gray-900 text-white hover:bg-gray-800 shadow-lg font-semibold">
                <Link href="/workspace">
                  <Icon icon="rocket" className="mr-2 h-5 w-5" />
                  {t('home.startTranslating')}
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-12 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <img src="/asset/icon.png" alt="TransVox" className="h-8 w-8 rounded-lg opacity-80" />
              <span className="text-lg font-bold text-foreground/80">TransVox</span>
            </div>

            <p className="text-sm text-muted-foreground text-center">
              © 2025 TransVox. AI-Powered Video Translation Platform.
            </p>

            <div className="flex items-center gap-6">
              <Link href="/docs" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                {t('nav.docs')}
              </Link>
              <Link href="/tools" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                {t('tools.title')}
              </Link>
              <Link href="/workspace" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                {t('nav.workspace')}
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
