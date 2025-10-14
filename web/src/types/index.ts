// Video processing types
export interface VideoFile {
  id: string
  name: string
  size: number
  duration?: number
  path: string
  status: ProcessingStatus
  createdAt: string
}

export type ProcessingStatus =
  | 'idle'
  | 'uploading'
  | 'processing'
  | 'completed'
  | 'error'
  | 'cancelled'

export interface ProcessingTask {
  id: string
  videoId: string
  type: TaskType
  status: ProcessingStatus
  progress: number
  message?: string
  result?: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export type TaskType =
  | 'separate_audio'
  | 'separate_vocals'
  | 'transcribe'
  | 'translate'
  | 'cut_audio'
  | 'tts'
  | 'merge'
  | 'embed_subtitle'

// Subtitle types
export interface Subtitle {
  id: string
  index: number
  startTime: string
  endTime: string
  text: string
}

export type SubtitleEmbedMode = 'hardcode' | 'soft' | 'external' | 'both'

export interface SubtitleConfig {
  mode: SubtitleEmbedMode
  language?: string
  fontSize?: number
  fontColor?: string
  outlineColor?: string
  outlineWidth?: number
  position?: 'top' | 'bottom'
  margin?: number
}

// TTS types
export type TTSEngine = 'gptsovits' | 'indextts'

export interface TTSConfig {
  engine: TTSEngine
  referenceAudio?: string
  referenceText?: string
  temperature?: number
  topP?: number
  topK?: number
}

// Translation types
export type Language = 'en' | 'zh' | 'ja' | 'ko'

export interface TranslationConfig {
  sourceLanguage: Language
  targetLanguage: Language
  apiKey?: string
}

// Pipeline types
export interface PipelineConfig {
  videoFile: string
  outputDir: string
  translation: TranslationConfig
  tts: TTSConfig
  subtitle: SubtitleConfig
  skipSteps?: TaskType[]
}

export interface PipelineProgress {
  currentStep: number
  totalSteps: number
  currentTask: TaskType
  progress: number
  message: string
}

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface UploadResponse {
  fileId: string
  fileName: string
  fileSize: number
  filePath: string
}

export interface TaskResponse {
  taskId: string
  status: ProcessingStatus
  message: string
}

