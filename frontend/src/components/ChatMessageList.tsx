import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Bot, User } from 'lucide-react'

interface ChatMessage {
  id: number | string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface ChatMessageListProps {
  messages: ChatMessage[]
  isStreaming: boolean
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      <div className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:0ms]" />
      <div className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:150ms]" />
      <div className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:300ms]" />
    </div>
  )
}

function formatTime(dateStr: string) {
  try {
    const date = new Date(dateStr)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

export default function ChatMessageList({ messages, isStreaming }: ChatMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-muted-foreground">
          <Bot className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm font-medium">Start a conversation</p>
          <p className="text-xs mt-1">Ask me to manage your tasks or media</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {messages.map(msg => {
        const isUser = msg.role === 'user'
        const isEmptyAssistant = !isUser && !msg.content && isStreaming

        return (
          <div key={msg.id} className={cn('flex gap-2', isUser ? 'justify-end' : 'justify-start')}>
            {!isUser && (
              <div className="flex-shrink-0 h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                <Bot className="h-4 w-4 text-primary" />
              </div>
            )}
            <div className={cn('max-w-[80%] min-w-0')}>
              <div
                className={cn(
                  'px-4 py-2.5 text-sm whitespace-pre-wrap break-words',
                  isUser
                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-br-md'
                    : 'bg-card border border-border rounded-2xl rounded-bl-md'
                )}
              >
                {isEmptyAssistant ? <TypingIndicator /> : msg.content}
              </div>
              <p className={cn('text-[10px] text-muted-foreground mt-1', isUser ? 'text-right' : 'text-left')}>
                {formatTime(msg.created_at)}
              </p>
            </div>
            {isUser && (
              <div className="flex-shrink-0 h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                <User className="h-4 w-4 text-primary" />
              </div>
            )}
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
