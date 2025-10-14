'use client'

import React from 'react'
import ReactMarkdown, { Components } from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/hooks/useTranslation'
import type { DocContent } from '@/types/docs'
import type { Locale } from '@/lib/i18n'

interface DocsContentProps {
  content: DocContent
}

export function DocsContent({ content }: DocsContentProps) {
  const { locale } = useTranslation()
  const localizedContent = content[locale as Locale] || content.en

  return (
    <div className="flex-1 px-6 py-8 lg:px-12 lg:py-12">
      <article className="prose dark:prose-invert prose-zinc dark:prose-zinc max-w-none">
        {/* Header */}
        <div className="mb-8 pb-8 border-b border-border">
          <h1 className="text-3xl font-bold text-foreground mb-3">
            {localizedContent.title}
          </h1>
          {localizedContent.description && (
            <p className="text-base text-muted-foreground">
              {localizedContent.description}
            </p>
          )}
        </div>

        {/* Markdown Content */}
        <ReactMarkdown
          components={{
            h1: ({ children, ...props }) => (
              <h1 className="text-2xl font-bold text-foreground mt-10 mb-4" {...props}>
                {children}
              </h1>
            ),
            h2: ({ children, ...props }) => (
              <h2 className="text-xl font-bold text-foreground mt-8 mb-3" {...props}>
                {children}
              </h2>
            ),
            h3: ({ children, ...props }) => (
              <h3 className="text-lg font-semibold text-foreground mt-6 mb-2" {...props}>
                {children}
              </h3>
            ),
            p: ({ children, ...props }) => (
              <p className="text-foreground leading-7 mb-4" {...props}>
                {children}
              </p>
            ),
            a: ({ children, href, ...props }) => (
              <a
                href={href}
                className="text-primary hover:text-primary/80 underline transition-colors"
                {...props}
              >
                {children}
              </a>
            ),
            ul: ({ children, ...props }) => (
              <ul className="list-disc list-inside space-y-2 text-foreground mb-4" {...props}>
                {children}
              </ul>
            ),
            ol: ({ children, ...props }) => (
              <ol className="list-decimal list-inside space-y-2 text-foreground mb-4" {...props}>
                {children}
              </ol>
            ),
            li: ({ children, ...props }) => (
              <li className="text-foreground" {...props}>
                {children}
              </li>
            ),
            code: ({ inline, className, children, ...props }: any) => {
              const match = /language-(\w+)/.exec(className || '')
              return !inline && match ? (
                <div className="my-6 rounded-lg overflow-hidden border border-border">
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    className="!bg-muted !m-0"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <code
                  className={cn(
                    'px-1.5 py-0.5 rounded bg-muted text-primary text-sm font-mono border border-border',
                    className
                  )}
                  {...props}
                >
                  {children}
                </code>
              )
            },
            blockquote: ({ children, ...props }) => (
              <blockquote
                className="border-l-4 border-primary pl-4 py-2 my-6 bg-primary/5 text-muted-foreground italic"
                {...props}
              >
                {children}
              </blockquote>
            ),
            table: ({ children, ...props }) => (
              <div className="my-6 overflow-x-auto">
                <table className="w-full border-collapse border border-border" {...props}>
                  {children}
                </table>
              </div>
            ),
            thead: ({ children, ...props }) => (
              <thead className="bg-muted" {...props}>
                {children}
              </thead>
            ),
            th: ({ children, ...props }) => (
              <th className="border border-border px-4 py-2 text-left font-semibold text-foreground" {...props}>
                {children}
              </th>
            ),
            td: ({ children, ...props }) => (
              <td className="border border-border px-4 py-2 text-foreground" {...props}>
                {children}
              </td>
            ),
            hr: ({ ...props }) => (
              <hr className="my-8 border-t border-border" {...props} />
            ),
          }}
        >
          {localizedContent.content}
        </ReactMarkdown>
      </article>
    </div>
  )
}
