'use client'

import { useState, useEffect } from 'react'

type Theme = 'blue-purple'

type Appearance = 'light' | 'dark'

export function ThemeSwitcher() {
  const [currentTheme] = useState<Theme>('blue-purple')
  const [appearance, setAppearance] = useState<Appearance>('light')

  // 应用主题
  const applyTheme = (theme: Theme, appearanceMode: Appearance) => {
    const html = document.documentElement
    html.classList.remove('theme-blue-purple')
    html.classList.add(`theme-${theme}`)

    if (appearanceMode === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 初始化：默认使用暗色主题
  useEffect(() => {
    const savedAppearance = localStorage.getItem('appearance') as Appearance

    // 如果没有保存过，默认使用暗色主题
    const initialMode = savedAppearance || 'dark'

    setAppearance(initialMode)
    applyTheme('blue-purple', initialMode)
  }, [])

  // 切换亮色和暗色
  const toggleAppearance = () => {
    const newAppearance: Appearance = appearance === 'light' ? 'dark' : 'light'

    setAppearance(newAppearance)
    applyTheme(currentTheme, newAppearance)
    localStorage.setItem('appearance', newAppearance)
  }

  return (
    <button
      onClick={toggleAppearance}
      className="flex items-center justify-center w-9 h-9 rounded-md hover:bg-accent/50 transition-colors"
      title={appearance === 'light' ? '切换到暗色模式' : '切换到亮色模式'}
    >
      {appearance === 'light' ? (
        // 太阳图标 - 简单圆形加射线
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="5" fill="currentColor" className="text-gray-700 dark:text-gray-300" />
          <path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="text-gray-700 dark:text-gray-300" />
        </svg>
      ) : (
        // 月亮图标 - 简单月牙形
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
                fill="currentColor" className="text-gray-700 dark:text-gray-300" />
        </svg>
      )}
    </button>
  )
}
