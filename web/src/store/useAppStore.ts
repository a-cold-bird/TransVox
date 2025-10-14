import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { VideoFile, ProcessingTask, PipelineProgress } from '@/types'

// Subtitle Editor Types
export interface Subtitle {
  id: string
  index: number
  startTime: string
  endTime: string
  startSeconds: number
  endSeconds: number
  text: string
}

export interface SubtitleStyleSettings {
  fontFamily: string
  fontSize: number
  fontColor: string
  bgColor: string
  bgOpacity: number
  outlineColor: string
  outlineWidth: number
  bold: boolean
  italic: boolean
  alignment: 'left' | 'center' | 'right'
}

interface AppState {
  // Videos
  videos: VideoFile[]
  currentVideo: VideoFile | null
  setVideos: (videos: VideoFile[]) => void
  setCurrentVideo: (video: VideoFile | null) => void
  addVideo: (video: VideoFile) => void
  removeVideo: (videoId: string) => void

  // Tasks
  tasks: ProcessingTask[]
  currentTask: ProcessingTask | null
  setTasks: (tasks: ProcessingTask[]) => void
  setCurrentTask: (task: ProcessingTask | null) => void
  addTask: (task: ProcessingTask) => void
  updateTask: (taskId: string, updates: Partial<ProcessingTask>) => void
  removeTask: (taskId: string) => void

  // Pipeline
  pipelineProgress: PipelineProgress | null
  setPipelineProgress: (progress: PipelineProgress | null) => void
  isPipelineRunning: boolean
  setIsPipelineRunning: (running: boolean) => void
  completedVideoPath: string | null
  setCompletedVideoPath: (path: string | null) => void
  translatedSubtitlePath: string | null
  setTranslatedSubtitlePath: (path: string | null) => void
  currentTaskId: string | null
  setCurrentTaskId: (taskId: string | null) => void
  pipelineError: { title: string; message: string; details?: string } | null
  setPipelineError: (error: { title: string; message: string; details?: string } | null) => void

  // UI State
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void

  // Tools State
  activeToolTab: 'download' | 'subtitleEditor' | 'audioSeparator' | 'transcribe' | 'translate' | 'workbench' | 'audioVideoMuxer'
  setActiveToolTab: (tab: 'download' | 'subtitleEditor' | 'audioSeparator' | 'transcribe' | 'translate' | 'workbench' | 'audioVideoMuxer') => void
  subtitleEditorState: {
    subtitles: Subtitle[]
    videoUrl: string
    styleSettings: SubtitleStyleSettings
  }
  setSubtitleEditorState: (state: { subtitles?: Subtitle[]; videoUrl?: string; styleSettings?: Partial<SubtitleStyleSettings> }) => void
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // Videos
        videos: [],
        currentVideo: null,
        setVideos: (videos) => set({ videos }),
        setCurrentVideo: (video) => set({ currentVideo: video }),
        addVideo: (video) =>
          set((state) => ({ videos: [...state.videos, video] })),
        removeVideo: (videoId) =>
          set((state) => ({
            videos: state.videos.filter((v) => v.id !== videoId),
            currentVideo:
              state.currentVideo?.id === videoId ? null : state.currentVideo,
          })),

        // Tasks
        tasks: [],
        currentTask: null,
        setTasks: (tasks) => set({ tasks }),
        setCurrentTask: (task) => set({ currentTask: task }),
        addTask: (task) =>
          set((state) => ({ tasks: [...state.tasks, task] })),
        updateTask: (taskId, updates) =>
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.id === taskId ? { ...t, ...updates } : t
            ),
            currentTask:
              state.currentTask?.id === taskId
                ? { ...state.currentTask, ...updates }
                : state.currentTask,
          })),
        removeTask: (taskId) =>
          set((state) => ({
            tasks: state.tasks.filter((t) => t.id !== taskId),
            currentTask:
              state.currentTask?.id === taskId ? null : state.currentTask,
          })),

        // Pipeline
        pipelineProgress: null,
        setPipelineProgress: (progress) => set({ pipelineProgress: progress }),
        isPipelineRunning: false,
        setIsPipelineRunning: (running) => set({ isPipelineRunning: running }),
        completedVideoPath: null,
        setCompletedVideoPath: (path) => set({ completedVideoPath: path }),
        translatedSubtitlePath: null,
        setTranslatedSubtitlePath: (path) => set({ translatedSubtitlePath: path }),
        currentTaskId: null,
        setCurrentTaskId: (taskId) => set({ currentTaskId: taskId }),
        pipelineError: null,
        setPipelineError: (error) => set({ pipelineError: error }),

        // UI State
        sidebarOpen: true,
        setSidebarOpen: (open) => set({ sidebarOpen: open }),
        theme: 'system',
        setTheme: (theme) => set({ theme }),

        // Tools State
        activeToolTab: 'subtitleEditor',
        setActiveToolTab: (tab) => set({ activeToolTab: tab }),
        subtitleEditorState: {
          subtitles: [],
          videoUrl: '',
          styleSettings: {
            fontFamily: 'Arial',
            fontSize: 18,
            fontColor: '#FFFFFF',
            bgColor: '#000000',
            bgOpacity: 0.8,
            outlineColor: '#000000',
            outlineWidth: 1,
            bold: false,
            italic: false,
            alignment: 'center',
          },
        },
        setSubtitleEditorState: (newState) =>
          set((state) => ({
            subtitleEditorState: {
              ...state.subtitleEditorState,
              ...newState,
              styleSettings: newState.styleSettings
                ? { ...state.subtitleEditorState.styleSettings, ...newState.styleSettings }
                : state.subtitleEditorState.styleSettings,
            },
          })),
      }),
      {
        name: 'transvox-storage',
        partialize: (state) => ({
          // 持久化视频和任务状态
          videos: state.videos,
          currentVideo: state.currentVideo,

          // 持久化 pipeline 状态
          isPipelineRunning: state.isPipelineRunning,
          pipelineProgress: state.pipelineProgress,
          completedVideoPath: state.completedVideoPath,
          translatedSubtitlePath: state.translatedSubtitlePath,
          currentTaskId: state.currentTaskId,

          // 持久化 UI 状态
          theme: state.theme,
          sidebarOpen: state.sidebarOpen,

          // 持久化工具箱状态
          activeToolTab: state.activeToolTab,
          subtitleEditorState: state.subtitleEditorState,
        }),
      }
    )
  )
)


