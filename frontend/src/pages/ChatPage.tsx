import { useChat } from '@/hooks/useChat'
import ChatMessageList from '@/components/ChatMessageList'
import ChatInput from '@/components/ChatInput'

export default function ChatPage() {
  const { messages, isLoading, isStreaming, sendMessage, error } = useChat()

  return (
    <div className="flex flex-col h-[calc(100vh-60px-env(safe-area-inset-bottom))]">
      <div className="border-b border-border bg-background/80 backdrop-blur-sm px-4 py-3">
        <h1 className="text-lg font-semibold text-center">Chat</h1>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ChatMessageList messages={messages} isStreaming={isStreaming} />
      )}

      {error && (
        <div className="px-4 py-2 bg-destructive/10 text-destructive text-sm text-center">
          {error}
        </div>
      )}

      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}
