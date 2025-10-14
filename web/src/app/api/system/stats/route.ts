import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    // 代理请求到后端API
    // 使用127.0.0.1而不是localhost，避免IPv6问题
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'
    const url = `${backendUrl}/api/system/stats`

    console.log('[System Stats API] Fetching from:', url)

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // 不缓存，每次都获取最新数据
      cache: 'no-store',
    })

    if (!response.ok) {
      console.error('[System Stats API] Backend returned:', response.status, response.statusText)
      throw new Error(`Backend API returned ${response.status}`)
    }

    const data = await response.json()
    console.log('[System Stats API] Success:', data.success)
    return NextResponse.json(data)
  } catch (error) {
    console.error('[System Stats API] Error:', error)
    // 返回空数据而不是错误，前端会静默处理
    return NextResponse.json({
      success: true,
      data: {
        gpu_available: false,
        gpus: [],
        system_memory: {
          total_gb: 0,
          used_gb: 0,
          available_gb: 0,
          percent: 0,
        },
      },
    })
  }
}
