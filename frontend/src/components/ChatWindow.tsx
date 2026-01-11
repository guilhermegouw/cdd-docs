import { useEffect, useRef } from 'react'
import { useChat } from '../hooks/useChat'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'

export function ChatWindow() {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Welcome to the CDD Docs Chat!</p>
            <p>I can answer questions about CDD's architecture, features, and usage. Try asking:</p>
            <ul>
              <li>How does the pub/sub system work?</li>
              <li>What tools are available to the agent?</li>
              <li>How is configuration managed?</li>
            </ul>
          </div>
        )}
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
      {error && <div className="error-banner">{error}</div>}
      <div className="input-container">
        <ChatInput onSend={sendMessage} disabled={isLoading} />
        {messages.length > 0 && (
          <button className="clear-button" onClick={clearMessages} disabled={isLoading}>
            Clear
          </button>
        )}
      </div>
    </div>
  )
}
