'use client'

import React, { useState, useEffect } from 'react'
import { Activity, Cpu, HardDrive, Zap, Thermometer } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

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

export function SystemStatsCard() {
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
    // 初始加载
    fetchStats()

    // 每3秒刷新一次
    const interval = setInterval(fetchStats, 3000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          加载系统状态中...
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-destructive">
          {error}
        </CardContent>
      </Card>
    )
  }

  if (!stats) {
    return null
  }

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

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <CardTitle>系统监控</CardTitle>
        </div>
        <CardDescription>
          实时GPU和内存使用情况（每3秒刷新）
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 系统内存 */}
        {stats.system_memory && Object.keys(stats.system_memory).length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold">系统内存</h3>
            </div>

            <div className="space-y-2">
              {/* 进度条 */}
              <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className={`absolute left-0 top-0 h-full transition-all duration-300 ${
                    stats.system_memory.percent >= 90
                      ? 'bg-red-500'
                      : stats.system_memory.percent >= 70
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${stats.system_memory.percent}%` }}
                />
              </div>

              {/* 数值信息 */}
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  已用: {stats.system_memory.used_gb.toFixed(1)} GB / {stats.system_memory.total_gb.toFixed(1)} GB
                </span>
                <span className={`font-medium ${getUsageColor(stats.system_memory.percent)}`}>
                  {stats.system_memory.percent.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* GPU信息 */}
        {stats.gpu_available && stats.gpus.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold">GPU 状态</h3>
            </div>

            {stats.gpus.map((gpu) => (
              <div key={gpu.index} className="space-y-3 p-4 bg-secondary/30 rounded-lg">
                {/* GPU名称 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{gpu.name}</span>
                  <span className="text-xs text-muted-foreground">GPU {gpu.index}</span>
                </div>

                {/* 显存使用 */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>显存</span>
                    <span>{gpu.memory.used_gb.toFixed(1)} / {gpu.memory.total_gb.toFixed(1)} GB</span>
                  </div>
                  <div className="relative h-2 bg-background rounded-full overflow-hidden">
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
                </div>

                {/* GPU利用率、温度、功耗 */}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  {/* 利用率 */}
                  <div className="flex items-center gap-1.5">
                    <Activity className={`h-3.5 w-3.5 ${getUsageColor(gpu.utilization)}`} />
                    <div className="flex flex-col">
                      <span className="text-muted-foreground">利用率</span>
                      <span className={`font-medium ${getUsageColor(gpu.utilization)}`}>
                        {gpu.utilization}%
                      </span>
                    </div>
                  </div>

                  {/* 温度 */}
                  <div className="flex items-center gap-1.5">
                    <Thermometer className={`h-3.5 w-3.5 ${getTempColor(gpu.temperature)}`} />
                    <div className="flex flex-col">
                      <span className="text-muted-foreground">温度</span>
                      <span className={`font-medium ${getTempColor(gpu.temperature)}`}>
                        {gpu.temperature}°C
                      </span>
                    </div>
                  </div>

                  {/* 功耗 */}
                  <div className="flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-yellow-500" />
                    <div className="flex flex-col">
                      <span className="text-muted-foreground">功耗</span>
                      <span className="font-medium">
                        {gpu.power.usage_w}W
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-sm text-muted-foreground">
            未检测到GPU设备
          </div>
        )}
      </CardContent>
    </Card>
  )
}
