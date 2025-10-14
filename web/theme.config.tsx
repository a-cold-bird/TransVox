import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'
import { useRouter } from 'next/router'

const config: DocsThemeConfig = {
  logo: () => {
    const { locale } = useRouter()
    return <span className="font-bold">{locale === 'zh-CN' ? 'TransVox 文档' : 'TransVox Docs'}</span>
  },
  i18n: [
    { locale: 'en', text: 'English' },
    { locale: 'zh-CN', text: '中文' },
  ],
  // 中文UI文本翻译
  editLink: {
    text: () => {
      const { locale } = useRouter()
      return locale === 'zh-CN' ? '在 GitHub 上编辑此页 →' : 'Edit this page on GitHub →'
    }
  },
  feedback: {
    content: () => {
      const { locale } = useRouter()
      return locale === 'zh-CN' ? '有疑问？给我们反馈 →' : 'Question? Give us feedback →'
    },
    labels: 'feedback'
  },
  toc: {
    title: () => {
      const { locale } = useRouter()
      return locale === 'zh-CN' ? '本页内容' : 'On This Page'
    },
    backToTop: true,
  },
  search: {
    placeholder: () => {
      const { locale } = useRouter()
      return locale === 'zh-CN' ? '搜索文档...' : 'Search documentation...'
    }
  },
  gitTimestamp: ({ timestamp }) => {
    const { locale } = useRouter()
    return (
      <>
        {locale === 'zh-CN' ? '最后更新于 ' : 'Last updated on '}
        {timestamp.toLocaleDateString(locale === 'zh-CN' ? 'zh-CN' : 'en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })}
      </>
    )
  },
  project: {
    link: 'https://github.com/a-cold-bird/TransVox',
  },
  docsRepositoryBase: 'https://github.com/a-cold-bird/TransVox/tree/main/web',
  footer: {
    text: '© 2025 TransVox. All rights reserved.',
  },
  useNextSeoProps() {
    return {
      titleTemplate: '%s – TransVox',
    }
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="TransVox Documentation" />
      <meta property="og:description" content="AI-Powered Video Translation & Dubbing Platform" />
      <link rel="icon" type="image/png" href="/asset/icon.png" />
      <link rel="shortcut icon" href="/favicon.ico" />
    </>
  ),
  primaryHue: 221,
  sidebar: {
    toggleButton: true,
  },
  navigation: {
    prev: true,
    next: true,
  },
  navbar: {
    extraContent: () => null,
  },
  darkMode: true,
  nextThemes: {
    defaultTheme: 'light',
  },
}

export default config

