import { useState, useCallback, useRef } from 'react'
import { Source, streamMessage } from '../api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  isStreaming?: boolean
}

interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  error: string | null
  sendMessage: (question: string) => void
  clearMessages: () => void
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sessionIdRef = useRef<string | undefined>(undefined)
  const cleanupRef = useRef<(() => void) | null>(null)

  const sendMessage = useCallback((question: string) => {
    if (!question.trim() || isLoading) return

    // Clean up any existing stream
    if (cleanupRef.current) {
      cleanupRef.current()
    }

    setError(null)
    setIsLoading(true)

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
    }

    // Add placeholder for assistant message
    const assistantId = crypto.randomUUID()
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isStreaming: true,
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage])

    // Start streaming
    const cleanup = streamMessage(question, sessionIdRef.current, {
      onSources: (sources) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId ? { ...msg, sources } : msg
          )
        )
      },
      onText: (text) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: msg.content + text }
              : msg
          )
        )
      },
      onDone: (sessionId) => {
        sessionIdRef.current = sessionId
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId ? { ...msg, isStreaming: false } : msg
          )
        )
        setIsLoading(false)
        cleanupRef.current = null
      },
      onError: (err) => {
        setError(err.message)
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: 'Error: ' + err.message, isStreaming: false }
              : msg
          )
        )
        setIsLoading(false)
        cleanupRef.current = null
      },
    })

    cleanupRef.current = cleanup
  }, [isLoading])

  const clearMessages = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current()
      cleanupRef.current = null
    }
    setMessages([])
    setError(null)
    sessionIdRef.current = undefined
  }, [])

  return { messages, isLoading, error, sendMessage, clearMessages }
}
