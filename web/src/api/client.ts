import axios, { AxiosInstance, AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 0, // No timeout - pipeline operations can take a long time
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if exists
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T = unknown>(url: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.get(url, { params })
      return response.data
    } catch (error: unknown) {
      return this.handleError<T>(error)
    }
  }

  async post<T = unknown>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.post(url, data)
      return response.data
    } catch (error: unknown) {
      return this.handleError<T>(error)
    }
  }

  async put<T = unknown>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.put(url, data)
      return response.data
    } catch (error: unknown) {
      return this.handleError<T>(error)
    }
  }

  async delete<T = unknown>(url: string): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.delete(url)
      return response.data
    } catch (error: unknown) {
      return this.handleError<T>(error)
    }
  }

  async upload<T = unknown>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    additionalData?: Record<string, string | number | boolean>
  ): Promise<ApiResponse<T>> {
    try {
      const formData = new FormData()
      formData.append('file', file)

      // 添加额外的表单数据
      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, String(value))
        })
      }

      const response: AxiosResponse<ApiResponse<T>> = await this.client.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        },
      })

      return response.data
    } catch (error: unknown) {
      return this.handleError<T>(error)
    }
  }

  private handleError<T = unknown>(error: unknown): ApiResponse<T> {
    console.error('API Error:', error)
    
    // Type guard for axios error
    if (this.isAxiosError(error)) {
      if (error.response) {
        return {
          success: false,
          error: error.response.data?.message || error.response.statusText,
          message: error.response.data?.error || 'Request failed',
        }
      } else if (error.request) {
        return {
          success: false,
          error: 'No response from server',
          message: 'Please check your connection',
        }
      }
    }
    
    // Handle generic errors
    const message = error instanceof Error ? error.message : 'Unknown error'
    return {
      success: false,
      error: message,
      message: 'An unexpected error occurred',
    }
  }

  private isAxiosError(error: unknown): error is { response?: { data?: { message?: string; error?: string }; statusText: string }; request?: unknown; message?: string } {
    return typeof error === 'object' && error !== null && ('response' in error || 'request' in error)
  }
}

export const apiClient = new ApiClient()

