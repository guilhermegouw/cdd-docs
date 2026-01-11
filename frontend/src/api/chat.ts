export interface Source {
  file_path: string
  section: string
  score: number
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  session_id: string
}

const API_BASE = ''  // Uses Vite proxy in dev, same origin in prod

export async function sendMessage(
  question: string,
  sessionId?: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, session_id: sessionId }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.json()
}

export interface StreamCallbacks {
  onSources: (sources: Source[]) => void
  onText: (text: string) => void
  onDone: (sessionId: string) => void
  onError: (error: Error) => void
}

export function streamMessage(
  question: string,
  sessionId: string | undefined,
  callbacks: StreamCallbacks
): () => void {
  const params = new URLSearchParams({ question })
  if (sessionId) {
    params.set('session_id', sessionId)
  }

  const eventSource = new EventSource(`${API_BASE}/chat/stream?${params}`)

  eventSource.addEventListener('sources', (event) => {
    const sources = JSON.parse(event.data) as Source[]
    callbacks.onSources(sources)
  })

  eventSource.addEventListener('text', (event) => {
    const text = JSON.parse(event.data) as string
    callbacks.onText(text)
  })

  eventSource.addEventListener('done', (event) => {
    const data = JSON.parse(event.data) as { session_id: string }
    callbacks.onDone(data.session_id)
    eventSource.close()
  })

  eventSource.onerror = () => {
    callbacks.onError(new Error('Connection error'))
    eventSource.close()
  }

  // Return cleanup function
  return () => eventSource.close()
}
