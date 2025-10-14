'use client'

import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card } from '@/components/ui/card'
import { videoService } from '@/api/services'
import { useAppStore } from '@/store/useAppStore'
import { useTranslation } from '@/hooks/useTranslation'
import { formatFileSize } from '@/lib/utils'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import type { VideoFile, ProcessingStatus } from '@/types'

export function VideoUpload() {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const addVideo = useAppStore((state) => state.addVideo)
  const setCurrentVideo = useAppStore((state) => state.setCurrentVideo)
  const currentVideo = useAppStore((state) => state.currentVideo)

  const uploadFile = useCallback(async (file: File) => {
    if (!file) return

    setUploading(true)
    setUploadProgress(0)

    try {
      const response = await videoService.uploadVideo(
        file,
        (progress) => {
          setUploadProgress(progress)
        }
      )

      if (response.success && response.data) {
        const newVideo: VideoFile = {
          id: response.data.fileId,
          name: response.data.fileName,
          size: response.data.fileSize,
          path: response.data.filePath,
          status: 'idle' as ProcessingStatus,
          createdAt: new Date().toISOString(),
        }

        addVideo(newVideo)
        setCurrentVideo(newVideo)  // 自动设置为当前视频

        setSelectedFile(null)
        setUploadProgress(0)
      } else {
        toast({
          title: '上传失败',
          description: response.error || 'Upload failed',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Upload error:', error)
      toast({
        title: '上传失败',
        description: '发生错误，请查看控制台日志',
        variant: 'destructive',
      })
    } finally {
      setUploading(false)
    }
  }, [addVideo, setCurrentVideo, toast])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setSelectedFile(file)
      // 自动上传
      uploadFile(file)
    }
  }, [uploadFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  const handleUpload = async () => {
    if (!selectedFile) return
    await uploadFile(selectedFile)
  }

  const handleRemove = () => {
    setSelectedFile(null)
    setUploadProgress(0)
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* 视频预览区域 */}
        {currentVideo && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">📹 当前视频</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentVideo(null)}
                className="h-8"
              >
                <X className="h-4 w-4 mr-1" />
                清除
              </Button>
            </div>

            <div className="bg-black rounded-lg overflow-hidden aspect-video flex items-center justify-center">
              <video
                src={`http://localhost:8000/api/videos/preview/${currentVideo.id}`}
                controls
                className="w-full h-full object-contain"
                onError={(e) => {
                  console.error('Video preview error:', e)
                }}
              >
                您的浏览器不支持视频播放
              </video>
            </div>

            <div className="bg-muted/50 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <File className="h-4 w-4 text-primary" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{currentVideo.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(currentVideo.size)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 上传区域 */}
        {!currentVideo && (
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
              isDragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-primary/50',
              uploading && 'pointer-events-none opacity-50'
            )}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
              <div className="rounded-full bg-primary/10 p-4">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="text-lg font-medium">
                  {t('upload.dragDrop')}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {t('upload.orClick')}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  {t('upload.supported')}
                </p>
              </div>
            </div>
          </div>
        )}

        <AnimatePresence>
          {selectedFile && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-3"
            >
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-3 flex-1">
                  <File className="h-5 w-5 text-primary" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                </div>
                {!uploading && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleRemove}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>

              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} />
                  <p className="text-xs text-center text-muted-foreground">
                    {t('upload.uploading')} {uploadProgress}%
                  </p>
                </div>
              )}

              {!uploading && (
                <Button
                  onClick={handleUpload}
                  className="w-full"
                  size="lg"
                >
                  {t('upload.uploadVideo')}
                </Button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Card>
  )
}


