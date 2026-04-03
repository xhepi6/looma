import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'

interface LocalChatMessage {
  id: number | string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export function useChat() {
  const [messages, setMessages] = useState<LocalChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const idCounter = useRef(0)
  const historyLoaded = useRef(false)

  const { data: history, isLoading } = useQuery({
    queryKey: ['chatHistory'],
    queryFn: api.getChatHistory,
  })

  useEffect(() => {
    if (history && !historyLoaded.current) {
      setMessages(history)
      historyLoaded.current = true
    }
  }, [history])

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming || !content.trim()) return

    setError(null)
    setIsStreaming(true)

    const userMsgId = `local-user-${++idCounter.current}`
    const assistantMsgId = `local-assistant-${++idCounter.current}`

    // Optimistically add user message
    const userMsg: LocalChatMessage = {
      id: userMsgId,
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString(),
    }

    // Add user message and empty assistant placeholder
    setMessages(prev => [
      ...prev,
      userMsg,
      { id: assistantMsgId, role: 'assistant', content: '', created_at: new Date().toISOString() },
    ])

    try {
      const response = await api.sendChatMessage(content.trim())
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()!

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            // Append delta to assistant message
            setMessages(prev =>
              prev.map(msg =>
                msg.id === assistantMsgId
                  ? { ...msg, content: msg.content + data }
                  : msg
              )
            )
          }
        }
      }

      // Process any remaining buffer
      if (buffer.startsWith('data: ')) {
        const data = buffer.slice(6)
        if (data !== '[DONE]') {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, content: msg.content + data }
                : msg
            )
          )
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong'
      setError(message)
      // Remove empty assistant placeholder on error
      setMessages(prev => prev.filter(msg => msg.id !== assistantMsgId || msg.content))
    } finally {
      setIsStreaming(false)
    }
  }, [isStreaming])

  return { messages, isLoading, isStreaming, sendMessage, error }
}
