// 文档系统类型定义

export interface DocNavItem {
  title: string
  href?: string
  icon?: string
  items?: DocNavItem[]
  badge?: string
}

export interface DocSection {
  title: string
  items: DocNavItem[]
}

export interface DocContent {
  en: {
    title: string
    description: string
    content: string
    toc?: TOCItem[]
  }
  zh: {
    title: string
    description: string
    content: string
    toc?: TOCItem[]
  }
}

export interface TOCItem {
  id: string
  title: string
  level: number
}
