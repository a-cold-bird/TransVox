import React from 'react'
import { notFound } from 'next/navigation'
import { DocsContent } from '@/components/docs/DocsContent'
import { docsContent } from '@/data/docs/content'

export async function generateStaticParams() {
  return Object.keys(docsContent).map((slug) => ({
    slug: slug.split('/'),
  }))
}

export async function generateMetadata({ params }: { params: { slug: string[] } }) {
  const slugPath = Array.isArray(params.slug) ? params.slug.join('/') : params.slug
  const content = docsContent[slugPath]

  if (!content) {
    return {
      title: 'Not Found',
    }
  }

  return {
    title: `${content.en.title} - TransVox Documentation`,
    description: content.en.description,
  }
}

export default function DocSlugPage({ params }: { params: { slug: string[] } }) {
  const slugPath = Array.isArray(params.slug) ? params.slug.join('/') : params.slug
  const content = docsContent[slugPath]

  if (!content) {
    notFound()
  }

  return <DocsContent content={content} />
}
