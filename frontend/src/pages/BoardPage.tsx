import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { useBoardSocket } from '@/hooks/useBoardSocket'
import { useTheme } from '@/hooks/useTheme'
import * as api from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toaster'
import ItemCard from '@/components/ItemCard'
import LabelBadge from '@/components/LabelBadge'
import { LogOut, Plus, ChevronDown, ChevronRight, X, Sun, Moon, ArrowUpDown } from 'lucide-react'

type SortOption = 'priority' | 'newest' | 'oldest'

const PRIORITY_ORDER: Record<string, number> = {
  HIGH: 0,
  MEDIUM: 1,
  LOW: 2,
  high: 0,
  medium: 1,
  low: 2,
}

export default function BoardPage() {
  const { boardId } = useParams<{ boardId: string }>()
  const boardIdNum = parseInt(boardId || '1', 10)
  const { logout } = useAuth()
  const queryClient = useQueryClient()
  const { status: wsStatus } = useBoardSocket(boardIdNum)
  const { resolvedTheme, setTheme } = useTheme()

  const [newItemTitle, setNewItemTitle] = useState('')
  const [showDone, setShowDone] = useState(false)
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortOption>('priority')

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items', boardIdNum],
    queryFn: () => api.getItems(boardIdNum),
  })

  const createItemMutation = useMutation({
    mutationFn: (title: string) => api.createItem(boardIdNum, { title }),
    onSuccess: () => {
      // Don't add item here - WebSocket will handle it to avoid duplicates
      // Only refetch if WebSocket is disconnected
      if (wsStatus !== 'connected') {
        queryClient.invalidateQueries({ queryKey: ['items', boardIdNum] })
      }
      setNewItemTitle('')
    },
    onError: () => {
      toast({ title: 'Failed to create item', variant: 'destructive' })
    },
  })

  const updateItemMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof api.updateItem>[1] }) =>
      api.updateItem(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['items', boardIdNum] })
      const previous = queryClient.getQueryData<api.Item[]>(['items', boardIdNum])
      queryClient.setQueryData<api.Item[]>(['items', boardIdNum], (old) =>
        old?.map((item) => (item.id === id ? { ...item, ...data } : item))
      )
      return { previous }
    },
    onError: (_, __, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['items', boardIdNum], context.previous)
      }
      toast({ title: 'Failed to update item', variant: 'destructive' })
    },
  })

  const deleteItemMutation = useMutation({
    mutationFn: (id: number) => api.deleteItem(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['items', boardIdNum] })
      const previous = queryClient.getQueryData<api.Item[]>(['items', boardIdNum])
      queryClient.setQueryData<api.Item[]>(['items', boardIdNum], (old) =>
        old?.filter((item) => item.id !== id)
      )
      return { previous }
    },
    onError: (_, __, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['items', boardIdNum], context.previous)
      }
      toast({ title: 'Failed to delete item', variant: 'destructive' })
    },
  })

  // Compute all unique labels from all items
  const allLabels = [...new Set(items.flatMap((item) => item.labels || []))]

  // Filter items by selected label
  const filteredItems = selectedLabel
    ? items.filter((item) => item.labels?.includes(selectedLabel))
    : items

  // Sort function based on selected option
  const sortItems = (a: api.Item, b: api.Item) => {
    switch (sortBy) {
      case 'priority': {
        const priorityA = PRIORITY_ORDER[a.priority] ?? 1
        const priorityB = PRIORITY_ORDER[b.priority] ?? 1
        if (priorityA !== priorityB) return priorityA - priorityB
        // Secondary sort by newest
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }
      case 'newest':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      case 'oldest':
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      default:
        return 0
    }
  }

  const todoItems = filteredItems
    .filter((item) => item.status === 'todo')
    .sort(sortItems)
  const doneItems = filteredItems
    .filter((item) => item.status === 'done')
    .sort(sortItems)

  const handleAddItem = (e: React.FormEvent) => {
    e.preventDefault()
    if (newItemTitle.trim()) {
      createItemMutation.mutate(newItemTitle.trim())
    }
  }

  const handleToggleStatus = (item: api.Item) => {
    updateItemMutation.mutate({
      id: item.id,
      data: { status: item.status === 'todo' ? 'done' : 'todo' },
    })
  }

  const handleDelete = (id: number) => {
    deleteItemMutation.mutate(id)
  }

  const handleUpdateLabels = (id: number, labels: string[]) => {
    updateItemMutation.mutate({ id, data: { labels } })
  }

  const handleUpdatePriority = (id: number, priority: api.ItemPriority) => {
    updateItemMutation.mutate({ id, data: { priority } })
  }

  const handleLabelFilter = (label: string) => {
    setSelectedLabel(selectedLabel === label ? null : label)
  }

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-primary">Looma</h1>
          <div className="flex items-center gap-2">
            {/* Theme toggle */}
            <Button variant="ghost" size="icon" onClick={toggleTheme} title="Toggle theme">
              {resolvedTheme === 'dark' ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
            {/* Logout */}
            <Button variant="ghost" size="icon" onClick={logout} title="Logout">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Add item form */}
        <form onSubmit={handleAddItem} className="mb-6">
          <div className="flex gap-2">
            <Input
              placeholder="Add a new task..."
              value={newItemTitle}
              onChange={(e) => setNewItemTitle(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" disabled={!newItemTitle.trim()}>
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>
        </form>

        {/* Label Filter Bar */}
        {allLabels.length > 0 && (
          <div className="mb-6 flex flex-wrap items-center gap-2" data-testid="label-filter-bar">
            <span className="text-sm text-muted-foreground mr-1">Filter:</span>
            {allLabels.map((label) => (
              <LabelBadge
                key={label}
                label={label}
                onClick={() => handleLabelFilter(label)}
                isSelected={selectedLabel === label}
              />
            ))}
            {selectedLabel && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => setSelectedLabel(null)}
              >
                <X className="h-3 w-3 mr-1" />
                Clear
              </Button>
            )}
          </div>
        )}

        {/* Todo Items */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
              Todo ({todoItems.length})
            </h2>
            <div className="flex items-center gap-1">
              <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="text-sm bg-transparent border-none text-muted-foreground hover:text-foreground focus:outline-none cursor-pointer"
              >
                <option value="priority">Priority</option>
                <option value="newest">Newest</option>
                <option value="oldest">Oldest</option>
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {todoItems.map((item) => (
                <ItemCard
                  key={item.id}
                  item={item}
                  onToggle={() => handleToggleStatus(item)}
                  onUpdateLabels={(labels) => handleUpdateLabels(item.id, labels)}
                  onUpdatePriority={(priority) => handleUpdatePriority(item.id, priority)}
                  onDelete={() => handleDelete(item.id)}
                  allLabels={allLabels}
                />
              ))}
            </AnimatePresence>
            {todoItems.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                {selectedLabel
                  ? `No tasks with label "${selectedLabel}"`
                  : 'No tasks yet. Add one above!'}
              </p>
            )}
          </div>
        </div>

        {/* Done Items Toggle */}
        <div>
          <button
            onClick={() => setShowDone(!showDone)}
            className="flex items-center gap-2 text-lg font-semibold mb-4 hover:text-primary transition-colors"
            data-testid="toggle-done"
          >
            {showDone ? (
              <ChevronDown className="h-5 w-5" />
            ) : (
              <ChevronRight className="h-5 w-5" />
            )}
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            Done ({doneItems.length})
          </button>

          {showDone && (
            <div className="space-y-2">
              <AnimatePresence mode="popLayout">
                {doneItems.map((item) => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    onToggle={() => handleToggleStatus(item)}
                    onUpdateLabels={(labels) => handleUpdateLabels(item.id, labels)}
                    onUpdatePriority={(priority) => handleUpdatePriority(item.id, priority)}
                    onDelete={() => handleDelete(item.id)}
                    allLabels={allLabels}
                  />
                ))}
              </AnimatePresence>
              {doneItems.length === 0 && (
                <p className="text-center text-muted-foreground py-8">
                  {selectedLabel
                    ? `No completed tasks with label "${selectedLabel}"`
                    : 'Completed tasks will appear here'}
                </p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
