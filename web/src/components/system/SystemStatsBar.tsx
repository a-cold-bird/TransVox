'use client'

import React, { useState, useEffect } from 'react'
import { Activity, Cpu, HardDrive, Zap, Thermometer, ChevronDown, ChevronUp } from 'lucide-react'

interface GPUInfo {
  index: number
  name: string
  memory: {
    total_gb: number
    used_gb: number
    free_gb: number
    percent: number
  }
  utilization: number
  temperature: number
  power: {
    usage_w: number
    limit_w: number
  }
}

interface SystemStats {
  gpu_available: boolean
  gpus: GPUInfo[]
  system_memory: {
    total_gb: number
    used_gb: number
    available_gb: number
    percent: number
  }
}

export function SystemStatsBar() {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/system/stats')
      const result = await response.json()

      if (result.success && result.data) {
        setStats(result.data as SystemStats)
        setError(null)
      } else {
        setError(result.error || '获取系统状态失败')
      }
    } catch (err) {
      console.error('Failed to fetch system stats:', err)
      setError('无法连接到服务器')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 3000)
    return () => clearInterval(interval)
  }, [])

  // 根据百分比返回颜色类
  const getUsageColor = (percent: number) => {
    if (percent >= 90) return 'text-red-500'
    if (percent >= 70) return 'text-yellow-500'
    return 'text-green-500'
  }

  // 根据温度返回颜色类
  const getTempColor = (temp: number) => {
    if (temp >= 80) return 'text-red-500'
    if (temp >= 70) return 'text-yellow-500'
    return 'text-blue-500'
  }

  if (loading) {
    return (
      <div className="border-b bg-muted/30">
        <div className="container mx-auto px-4 py-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Activity className="h-4 w-4 animate-pulse" />
            <span>加载系统状态...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return null // 静默失败，不显示错误状态栏
  }

  if (!stats) {
    return null
  }

  // 提取GPU简短名称（去掉 NVIDIA GeForce 等前缀）
  const getShortGPUName = (fullName: string) => {
    return fullName
      .replace(/NVIDIA GeForce /gi, '')
      .replace(/AMD Radeon /gi, '')
      .replace(/Intel /gi, '')
      .trim()
  }

  return (
    <div className="border-b bg-muted/30">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center gap-8">
          {/* 左侧：GPU状态 */}
          {stats.gpu_available && stats.gpus.length > 0 && (
            <div className="flex items-center gap-6 flex-1">
              {stats.gpus.map((gpu) => (
                <React.Fragment key={gpu.index}>
                  {/* GPU显存 */}
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium text-muted-foreground">
                      GPU {getShortGPUName(gpu.name)}
                    </span>
                    <div className="flex flex-col gap-0.5 w-32">
                      <div className="relative h-1.5 bg-secondary rounded-full overflow-hidden">
                        <div
                          className={`absolute left-0 top-0 h-full transition-all duration-300 ${
                            gpu.memory.percent >= 90
                              ? 'bg-red-500'
                              : gpu.memory.percent >= 70
                              ? 'bg-yellow-500'
                              : 'bg-blue-500'
                          }`}
                          style={{ width: `${gpu.memory.percent}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-muted-foreground tabular-nums">
                        {gpu.memory.used_gb.toFixed(1)}/{gpu.memory.total_gb.toFixed(0)}GB
                      </span>
                    </div>
                  </div>

                  {/* GPU利用率 */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">利用率</span>
                    <span className={`text-xs font-medium tabular-nums ${getUsageColor(gpu.utilization)}`}>
                      {gpu.utilization}%
                    </span>
                  </div>

                  {/* 温度 */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">温度</span>
                    <span className={`text-xs font-medium tabular-nums ${getTempColor(gpu.temperature)}`}>
                      {gpu.temperature}°C
                    </span>
                  </div>

                  {/* 功耗 */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">功耗</span>
                    <span className="text-xs font-medium tabular-nums">
                      {gpu.power.usage_w}W
                    </span>
                  </div>
                </React.Fragment>
              ))}
            </div>
          )}

          {/* 右侧：系统内存 */}
          {stats.system_memory && Object.keys(stats.system_memory).length > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-muted-foreground">内存</span>
              <div className="flex flex-col gap-0.5 w-32">
                <div className="relative h-1.5 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={`absolute left-0 top-0 h-full transition-all duration-300 ${
                      stats.system_memory.percent >= 90
                        ? 'bg-red-500'
                        : stats.system_memory.percent >= 70
                        ? 'bg-yellow-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${stats.system_memory.percent}%` }}
                  />
                </div>
                <span className="text-[10px] text-muted-foreground tabular-nums">
                  {stats.system_memory.used_gb.toFixed(1)}/{stats.system_memory.total_gb.toFixed(0)}GB
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
