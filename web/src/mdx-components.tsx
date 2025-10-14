import type { MDXComponents } from 'mdx/types'
import { ReactNode } from 'react'

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    h1: ({ children }: { children?: ReactNode }) => (
      <h1 className="text-4xl font-bold mt-8 mb-4 text-foreground border-b pb-2">
        {children}
      </h1>
    ),
    h2: ({ children }: { children?: ReactNode }) => (
      <h2 className="text-3xl font-semibold mt-8 mb-4 text-foreground">
        {children}
      </h2>
    ),
    h3: ({ children }: { children?: ReactNode }) => (
      <h3 className="text-2xl font-semibold mt-6 mb-3 text-foreground">
        {children}
      </h3>
    ),
    h4: ({ children }: { children?: ReactNode }) => (
      <h4 className="text-xl font-semibold mt-4 mb-2 text-foreground">
        {children}
      </h4>
    ),
    p: ({ children }: { children?: ReactNode }) => (
      <p className="my-4 leading-7 text-muted-foreground">{children}</p>
    ),
    ul: ({ children }: { children?: ReactNode }) => (
      <ul className="my-4 ml-6 list-disc space-y-2">{children}</ul>
    ),
    ol: ({ children }: { children?: ReactNode }) => (
      <ol className="my-4 ml-6 list-decimal space-y-2">{children}</ol>
    ),
    li: ({ children }: { children?: ReactNode }) => (
      <li className="text-muted-foreground">{children}</li>
    ),
    blockquote: ({ children }: { children?: ReactNode }) => (
      <blockquote className="my-4 border-l-4 border-primary/50 pl-4 italic text-muted-foreground bg-muted/50 py-2">
        {children}
      </blockquote>
    ),
    code: ({ children, className }: { children?: ReactNode; className?: string }) => {
      const isInline = !className
      if (isInline) {
        return (
          <code className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono text-primary">
            {children}
          </code>
        )
      }
      return (
        <code className={className}>
          {children}
        </code>
      )
    },
    pre: ({ children }: { children?: ReactNode }) => (
      <pre className="my-4 overflow-x-auto rounded-lg bg-muted p-4 text-sm">
        {children}
      </pre>
    ),
    a: ({ href, children }: { href?: string; children?: ReactNode }) => (
      <a
        href={href}
        className="text-primary hover:text-primary/80 underline underline-offset-4"
        target={href?.startsWith('http') ? '_blank' : undefined}
        rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
      >
        {children}
      </a>
    ),
    table: ({ children }: { children?: ReactNode }) => (
      <div className="my-4 overflow-x-auto">
        <table className="w-full border-collapse border border-border">
          {children}
        </table>
      </div>
    ),
    th: ({ children }: { children?: ReactNode }) => (
      <th className="border border-border bg-muted px-4 py-2 text-left font-semibold">
        {children}
      </th>
    ),
    td: ({ children }: { children?: ReactNode }) => (
      <td className="border border-border px-4 py-2">{children}</td>
    ),
    hr: () => <hr className="my-8 border-border" />,
    ...components,
  }
}
