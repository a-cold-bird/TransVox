'use client'

import React from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { ArrowLeft, Github } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { ThemeSwitcher } from '@/components/ThemeSwitcher'
import { useTranslation } from '@/hooks/useTranslation'

export function DocsHeader() {
  const { t } = useTranslation()

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-background/95 backdrop-blur-sm border-b border-border">
      <div className="container mx-auto px-4 h-full flex items-center justify-between">
        {/* Left: Logo & Back */}
        <div className="flex items-center gap-3">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 text-foreground hover:opacity-80 transition-opacity group">
            <div className="w-9 h-9 rounded-lg bg-white dark:bg-white/95 flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
              <Image
                src="/asset/icon.png"
                alt="TransVox Logo"
                width={32}
                height={32}
                className="rounded-md"
              />
            </div>
            <span className="text-lg font-bold">TransVox</span>
          </Link>

          <div className="h-5 w-px bg-border/50" />

          {/* Back Button */}
          <Link href="/" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>{t('nav.backToHome')}</span>
          </Link>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* GitHub Link */}
          <Button variant="ghost" size="sm" asChild>
            <a
              href="https://github.com/a-cold-bird/TransVox"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground"
            >
              <Github className="h-4 w-4" />
            </a>
          </Button>

          <div className="h-6 w-px bg-border" />

          {/* Language Switcher */}
          <LanguageSwitcher />

          {/* Theme Switcher */}
          <ThemeSwitcher />
        </div>
      </div>
    </header>
  )
}
