import { apiClient } from './client'
import type {
  VideoFile,
  ProcessingTask,
  PipelineConfig,
  SubtitleConfig,
  TTSConfig,
  TranslationConfig,
  UploadResponse,
  TaskResponse,
} from '@/types'

export const videoService = {
  // Upload video
  async uploadVideo(file: File, onProgress?: (progress: number) => void) {
    return apiClient.upload<UploadResponse>('/api/upload/video', file, onProgress)
  },

  // Get all videos
  async getVideos() {
    return apiClient.get<VideoFile[]>('/api/videos')
  },

  // Get video by ID
  async getVideo(id: string) {
    return apiClient.get<VideoFile>(`/api/videos/${id}`)
  },

  // Delete video
  async deleteVideo(id: string) {
    return apiClient.delete(`/api/videos/${id}`)
  },
}

export const taskService = {
  // Get all tasks
  async getTasks(videoId?: string) {
    return apiClient.get<ProcessingTask[]>('/api/tasks', { videoId })
  },

  // Get task by ID
  async getTask(id: string) {
    return apiClient.get<ProcessingTask>(`/api/tasks/${id}`)
  },

  // Cancel task
  async cancelTask(id: string) {
    return apiClient.post(`/api/tasks/${id}/cancel`)
  },
}

export const pipelineService = {
  // Start full pipeline
  async startPipeline(config: PipelineConfig) {
    return apiClient.post<TaskResponse>('/api/pipeline/start', config)
  },

  // Get pipeline status
  async getPipelineStatus(taskId: string) {
    return apiClient.get<ProcessingTask>(`/api/pipeline/status/${taskId}`)
  },

  // Stop pipeline
  async stopPipeline(taskId: string) {
    return apiClient.post(`/api/pipeline/stop/${taskId}`)
  },

  // Get pipeline history
  async getHistory() {
    return apiClient.get<any[]>('/api/pipeline/history')
  },

  // Delete/clear a task
  async deleteTask(taskId: string) {
    return apiClient.delete(`/api/pipeline/clear/${taskId}`)
  },
}

export const audioService = {
  // Separate audio from video
  async separateAudio(videoPath: string) {
    return apiClient.post<TaskResponse>('/api/audio/separate', { videoPath })
  },

  // Separate vocals
  async separateVocals(audioPath: string) {
    return apiClient.post<TaskResponse>('/api/audio/separate-vocals', { audioPath })
  },
}

export const transcriptionService = {
  // Transcribe audio
  async transcribe(audioPath: string, language?: string) {
    return apiClient.post<TaskResponse>('/api/transcribe', { audioPath, language })
  },

  // Get transcription result
  async getTranscription(taskId: string) {
    return apiClient.get(`/api/transcribe/${taskId}`)
  },
}

export const translationService = {
  // Translate subtitle
  async translate(config: TranslationConfig & { subtitlePath: string }) {
    return apiClient.post<TaskResponse>('/api/translate', config)
  },

  // Get translation result
  async getTranslation(taskId: string) {
    return apiClient.get(`/api/translate/${taskId}`)
  },
}

export const ttsService = {
  // Generate TTS
  async generateTTS(config: TTSConfig & { subtitlePath: string; audioDir: string }) {
    return apiClient.post<TaskResponse>('/api/tts/generate', config)
  },

  // Get TTS result
  async getTTSResult(taskId: string) {
    return apiClient.get(`/api/tts/${taskId}`)
  },
}

export const subtitleService = {
  // Process subtitle (split lines)
  async processSubtitle(subtitlePath: string, maxLineChars: number = 40) {
    return apiClient.post<TaskResponse>('/api/subtitle/process', {
      subtitlePath,
      maxLineChars,
    })
  },

  // Embed subtitle to video
  async embedSubtitle(config: SubtitleConfig & { videoPath: string; subtitlePath: string }) {
    return apiClient.post<TaskResponse>('/api/subtitle/embed', config)
  },

  // Get subtitle content
  async getSubtitle(filePath: string) {
    return apiClient.get(`/api/subtitle/content`, { filePath })
  },
}

export const mergeService = {
  // Merge dubbed audio with video
  async mergeVideo(videoPath: string, audioPath: string, outputPath: string) {
    return apiClient.post<TaskResponse>('/api/merge', {
      videoPath,
      audioPath,
      outputPath,
    })
  },
}

export const downloadService = {
  // Download video from URL
  async downloadVideo(url: string, quality?: string) {
    return apiClient.post<TaskResponse>('/api/download/video', { url, quality })
  },

  // Get download status
  async getDownloadStatus(taskId: string) {
    return apiClient.get<ProcessingTask>(`/api/download/${taskId}`)
  },
}

export const toolService = {
  // Transcribe with options
  async transcribeWithOptions(file: File, options: {
    language?: string
    model?: string
    enableDiarization?: boolean
    beamSize?: number
    temperature?: number
    vadThreshold?: number
    minSpeakers?: number
    maxSpeakers?: number
  }, onProgress?: (progress: number) => void) {
    const formData = {
      language: options.language || 'auto',
      model: options.model || 'large-v3',
      enableDiarization: options.enableDiarization !== false ? 'true' : 'false',
      beamSize: options.beamSize || 5,
      temperature: options.temperature || 0.0,
      vadThreshold: options.vadThreshold || 0.5,
      minSpeakers: options.minSpeakers || 1,
      maxSpeakers: options.maxSpeakers || 5,
    }
    return apiClient.upload<TaskResponse>('/api/tools/transcribe', file, onProgress, formData)
  },

  // Separate audio (vocals/instrumental)
  async separateAudio(file: File, onProgress?: (progress: number) => void) {
    return apiClient.upload<TaskResponse>('/api/tools/separate-audio', file, onProgress)
  },

  // Translate subtitle
  async translateSubtitle(file: File, options: {
    targetLang: string
    contextPrompt?: string
    apiType?: string
    model?: string
  }, onProgress?: (progress: number) => void) {
    const formData = {
      targetLang: options.targetLang,
      contextPrompt: options.contextPrompt || '',
      apiType: options.apiType || 'gemini',
      model: options.model || '',
    }
    return apiClient.upload<TaskResponse>('/api/tools/translate', file, onProgress, formData)
  },

  // Download result file
  async downloadResult(taskId: string, fileType: string) {
    return apiClient.get(`/api/tools/download-result/${taskId}/${fileType}`)
  },
}

export const configService = {
  // Get user configuration
  async getConfig() {
    return apiClient.get<Record<string, any>>('/api/config')
  },

  // Update user configuration
  async updateConfig(config: Record<string, any>) {
    return apiClient.post<Record<string, any>>('/api/config', config)
  },

  // Reset configuration to default
  async resetConfig() {
    return apiClient.post<Record<string, any>>('/api/config/reset')
  },

  // Get available translation models
  async getTranslationModels(apiType?: string) {
    const params = apiType ? { api_type: apiType } : {}
    return apiClient.get<Record<string, any>>('/api/config/translation-models', params)
  },
}


