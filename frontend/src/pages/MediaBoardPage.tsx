import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import { useBoardSocket } from '@/hooks/useBoardSocket'
import * as api from '@/lib/api'
import type { MediaItem, MediaType, MediaStatus } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import MediaCard from '@/components/MediaCard'
import { cn } from '@/lib/utils'
import { Plus, Search, Film, Tv } from 'lucide-react'

type MediaTypeFilter = 'all' | 'movie' | 'tv_show'

const STATUS_SECTIONS: { status: MediaStatus; label: string; color: string }[] = [
  { status: 'watching', label: 'Watching', color: 'text-blue-600 dark:text-blue-400' },
  { status: 'want_to_watch', label: 'Want to Watch', color: 'text-amber-600 dark:text-amber-400' },
  { status: 'watched', label: 'Watched', color: 'text-green-600 dark:text-green-400' },
]

interface MediaBoardPageProps {
  boardId: number
}

export default function MediaBoardPage({ boardId }: MediaBoardPageProps) {
  const queryClient = useQueryClient()
  useBoardSocket(boardId)

  // Form state
  const [newTitle, setNewTitle] = useState('')
  const [newMediaType, setNewMediaType] = useState<MediaType>('movie')

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<MediaTypeFilter>('all')

  const { data: mediaItems = [], isLoading } = useQuery({
    queryKey: ['media', boardId],
    queryFn: () => api.getMedia(boardId),
  })

  const createMutation = useMutation({
    mutationFn: (data: { title: string; media_type: MediaType }) =>
      api.createMedia(boardId, data),
    onSuccess: (newItem) => {
      queryClient.setQueryData<MediaItem[]>(['media', boardId], (old) =>
        old ? [...old, newItem].sort((a, b) => a.position - b.position) : [newItem]
      )
      setNewTitle('')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { status?: MediaStatus } }) =>
      api.updateMedia(id, data),
    onMutate: async ({ id, data }) => {
      const previous = queryClient.getQueryData<MediaItem[]>(['media', boardId])
      queryClient.setQueryData<MediaItem[]>(['media', boardId], (old) =>
        old?.map((m) => (m.id === id ? { ...m, ...data } : m))
      )
      return { previous }
    },
    onError: (_, __, context) => {
      queryClient.setQueryData(['media', boardId], context?.previous)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteMedia(id),
    onMutate: async (id) => {
      const previous = queryClient.getQueryData<MediaItem[]>(['media', boardId])
      queryClient.setQueryData<MediaItem[]>(['media', boardId], (old) =>
        old?.filter((m) => m.id !== id)
      )
      return { previous }
    },
    onError: (_, __, context) => {
      queryClient.setQueryData(['media', boardId], context?.previous)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const title = newTitle.trim()
    if (!title) return
    createMutation.mutate({ title, media_type: newMediaType })
  }

  // Apply filters
  const filtered = mediaItems.filter((item) => {
    if (typeFilter !== 'all' && item.media_type !== typeFilter) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return item.title.toLowerCase().includes(q) ||
        (item.title_en?.toLowerCase().includes(q) ?? false)
    }
    return true
  })

  const groupedByStatus = (status: MediaStatus) =>
    filtered.filter((item) => item.status === status)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Header */}
      <h1 className="text-2xl font-bold mb-4">Watch List</h1>

      {/* Add form */}
      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        <Input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="Add a movie or TV show..."
          className="flex-1"
        />
        <select
          value={newMediaType}
          onChange={(e) => setNewMediaType(e.target.value as MediaType)}
          className="px-3 py-2 rounded-md border bg-background text-sm"
        >
          <option value="movie">Movie</option>
          <option value="tv_show">TV Show</option>
        </select>
        <Button type="submit" size="icon" disabled={!newTitle.trim() || createMutation.isPending}>
          <Plus className="h-4 w-4" />
        </Button>
      </form>

      {/* Search and filter bar */}
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            className="pl-9"
          />
        </div>
        <div className="flex rounded-md border bg-background">
          <button
            onClick={() => setTypeFilter('all')}
            className={cn(
              'px-3 py-2 text-xs font-medium transition-colors rounded-l-md',
              typeFilter === 'all' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            )}
          >
            All
          </button>
          <button
            onClick={() => setTypeFilter('movie')}
            className={cn(
              'px-3 py-2 text-xs font-medium transition-colors flex items-center gap-1',
              typeFilter === 'movie' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            )}
          >
            <Film className="h-3 w-3" /> Movies
          </button>
          <button
            onClick={() => setTypeFilter('tv_show')}
            className={cn(
              'px-3 py-2 text-xs font-medium transition-colors rounded-r-md flex items-center gap-1',
              typeFilter === 'tv_show' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            )}
          >
            <Tv className="h-3 w-3" /> TV Shows
          </button>
        </div>
      </div>

      {/* Grouped sections */}
      {STATUS_SECTIONS.map(({ status, label, color }) => {
        const items = groupedByStatus(status)
        return (
          <div key={status} className="mb-6">
            <h2 className={cn('text-sm font-semibold uppercase tracking-wide mb-2', color)}>
              {label} ({items.length})
            </h2>
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground py-3 text-center">Nothing here yet</p>
            ) : (
              <div className="space-y-2">
                <AnimatePresence mode="popLayout">
                  {items.map((item) => (
                    <MediaCard
                      key={item.id}
                      item={item}
                      onUpdateStatus={(newStatus) =>
                        updateMutation.mutate({ id: item.id, data: { status: newStatus } })
                      }
                      onDelete={() => deleteMutation.mutate(item.id)}
                    />
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
