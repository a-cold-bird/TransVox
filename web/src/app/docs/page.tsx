import React from 'react'
import { DocsContent } from '@/components/docs/DocsContent'
import { docsContent } from '@/data/docs/content'

export const metadata = {
  title: 'Introduction - TransVox Documentation',
  description: 'Learn how to use TransVox for AI-powered video translation and voice cloning',
}

export default function DocsPage() {
  const content = docsContent['index']

  if (!content) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zinc-400">Documentation not found</p>
      </div>
    )
  }

  return <DocsContent content={content} />
}
