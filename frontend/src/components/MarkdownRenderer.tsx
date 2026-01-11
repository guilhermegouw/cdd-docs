import { useEffect, useRef, useId } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import mermaid from 'mermaid'

interface MarkdownRendererProps {
  content: string
}

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
})

interface CodeBlockProps {
  className?: string
  children?: React.ReactNode
}

function CodeBlock({ className, children }: CodeBlockProps) {
  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : ''
  const codeRef = useRef<HTMLDivElement>(null)
  const uniqueId = useId().replace(/:/g, '')

  useEffect(() => {
    if (language === 'mermaid' && codeRef.current && children) {
      const code = String(children).replace(/\n$/, '')

      mermaid.render(`mermaid-${uniqueId}`, code).then((result) => {
        if (codeRef.current) {
          codeRef.current.innerHTML = result.svg
        }
      }).catch((error) => {
        console.error('Mermaid render error:', error)
        if (codeRef.current) {
          codeRef.current.innerHTML = `<pre class="mermaid-error">Error rendering diagram: ${error.message}</pre>`
        }
      })
    }
  }, [language, children, uniqueId])

  if (language === 'mermaid') {
    return <div ref={codeRef} className="mermaid-container" />
  }

  return (
    <pre className={language ? `language-${language}` : undefined}>
      <code>{children}</code>
    </pre>
  )
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        code: ({ className, children, ...props }) => {
          const isInline = !className
          if (isInline) {
            return <code {...props}>{children}</code>
          }
          return <CodeBlock className={className}>{children}</CodeBlock>
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
