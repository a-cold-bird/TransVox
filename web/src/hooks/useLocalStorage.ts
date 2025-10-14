'use client'

import { useState, useEffect } from 'react'

/**
 * 通用的持久化存储 Hook
 * 将状态保存到 localStorage，页面刷新后自动恢复
 *
 * @param key - localStorage 的键名
 * @param initialValue - 初始值
 * @returns [state, setState] - 与 useState 相同的 API
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  // 初始化状态
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue
    }

    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  // 更新状态并保存到 localStorage
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      // 允许传入函数（与 useState 一致）
      const valueToStore = value instanceof Function ? value(storedValue) : value

      setStoredValue(valueToStore)

      // 保存到 localStorage
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore))
      }
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }

  // 监听其他标签页的 localStorage 变化
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue) {
        try {
          setStoredValue(JSON.parse(e.newValue))
        } catch (error) {
          console.warn(`Error parsing storage event for key "${key}":`, error)
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [key])

  return [storedValue, setValue] as const
}
