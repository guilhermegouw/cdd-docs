import { useEffect, useRef, useId, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import mermaid from 'mermaid'

interface MarkdownRendererProps {
  content: string
  isStreaming?: boolean
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
  isStreaming?: boolean
}

function CodeBlock({ className, children, isStreaming }: CodeBlockProps) {
  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : ''
  const codeRef = useRef<HTMLDivElement>(null)
  const uniqueId = useId().replace(/:/g, '')
  const [rendered, setRendered] = useState(false)

  useEffect(() => {
    // Only render mermaid when not streaming to avoid partial diagram errors
    if (language === 'mermaid' && codeRef.current && children && !isStreaming && !rendered) {
      const code = String(children).replace(/\n$/, '')

      mermaid.render(`mermaid-${uniqueId}`, code).then((result) => {
        if (codeRef.current) {
          codeRef.current.innerHTML = result.svg
          setRendered(true)
        }
      }).catch((error) => {
        console.error('Mermaid render error:', error)
        // On error, keep showing the raw code (don't setRendered)
        // so users can still see the diagram source
      })
    }
  }, [language, children, uniqueId, isStreaming, rendered])

  if (language === 'mermaid') {
    return (
      <div className="mermaid-container">
        {/* Always render the target div for mermaid */}
        <div ref={codeRef} />
        {/* Show code while streaming or before render completes */}
        {(isStreaming || !rendered) && (
          <pre style={{ background: 'transparent', color: '#666', margin: 0 }}>
            <code>{children}</code>
          </pre>
        )}
      </div>
    )
  }

  return (
    <pre className={language ? `language-${language}` : undefined}>
      <code>{children}</code>
    </pre>
  )
}

export function MarkdownRenderer({ content, isStreaming }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        // Let CodeBlock handle all wrapping - don't add extra pre
        pre: ({ children }) => <>{children}</>,
        code: ({ className, children, ...props }) => {
          const isInline = !className
          if (isInline) {
            return <code {...props}>{children}</code>
          }
          return <CodeBlock className={className} isStreaming={isStreaming}>{children}</CodeBlock>
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
