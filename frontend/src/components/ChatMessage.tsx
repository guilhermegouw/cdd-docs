import { Message } from '../hooks/useChat'
import { MarkdownRenderer } from './MarkdownRenderer'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-header">
        <span className="role-label">{isUser ? 'You' : 'Assistant'}</span>
        {message.isStreaming && <span className="streaming-indicator">...</span>}
      </div>
      <div className="message-content">
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <MarkdownRenderer content={message.content} isStreaming={message.isStreaming} />
        )}
      </div>
      {message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          <span className="sources-label">Sources:</span>
          <ul>
            {message.sources.map((source, i) => (
              <li key={i}>
                <code>{source.file_path}</code> - {source.section}
                <span className="source-score">({(source.score * 100).toFixed(0)}%)</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
