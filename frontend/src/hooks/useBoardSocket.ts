import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Item } from '@/lib/api'

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected'

interface WSEvent {
  type: string
  board_id: number
  ts: string
  item?: Item
}

// Track processed event timestamps to prevent duplicate handling
const processedEvents = new Set<string>()

// Track recently added item IDs to prevent race conditions with duplicate additions
const recentlyAddedItems = new Set<number>()

export function useBoardSocket() {
  const boardId = 1
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const queryClient = useQueryClient()

  const handleEvent = useCallback((event: WSEvent) => {
    // Dedupe events by timestamp + type + item id
    const eventKey = `${event.ts}-${event.type}-${event.item?.id}`
    if (processedEvents.has(eventKey)) {
      return
    }
    processedEvents.add(eventKey)
    // Clean up old events after 10 seconds
    setTimeout(() => processedEvents.delete(eventKey), 10000)

    const queryKey = ['items', event.board_id]

    switch (event.type) {
      case 'item.created':
        queryClient.setQueryData<Item[]>(queryKey, (old) => {
          if (!old || !event.item) return old

          // Check if item was recently added (prevents race conditions)
          if (recentlyAddedItems.has(event.item.id)) {
            return old
          }

          // Check if item already exists in cache
          if (old.some((item) => item.id === event.item!.id)) {
            return old.map((item) =>
              item.id === event.item!.id ? event.item! : item
            )
          }

          // Track this item ID to prevent duplicate additions
          recentlyAddedItems.add(event.item.id)
          setTimeout(() => recentlyAddedItems.delete(event.item!.id), 5000)

          return [...old, event.item].sort((a, b) => a.position - b.position)
        })
        break

      case 'item.updated':
        queryClient.setQueryData<Item[]>(queryKey, (old) => {
          if (!old || !event.item) return old
          return old
            .map((item) => (item.id === event.item!.id ? event.item! : item))
            .sort((a, b) => a.position - b.position)
        })
        break

      case 'item.deleted':
        queryClient.setQueryData<Item[]>(queryKey, (old) => {
          if (!old || !event.item) return old
          return old.filter((item) => item.id !== event.item!.id)
        })
        break

      case 'label.created':
      case 'label.updated':
      case 'label.deleted':
        // Refetch labels and items (items embed label objects)
        queryClient.invalidateQueries({ queryKey: ['labels', event.board_id] })
        queryClient.invalidateQueries({ queryKey: ['items', event.board_id] })
        break
    }
  }, [queryClient])

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) return

    setStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws?board_id=${boardId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data)
        handleEvent(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      setStatus('disconnected')
      // Only reconnect if this is still our active connection
      if (wsRef.current === ws) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect()
        }, 2000)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }, [boardId, handleEvent])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { status }
}
