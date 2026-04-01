import { useState, useRef, useEffect } from 'react'
import { useParams, Navigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import { useBoardSocket } from '@/hooks/useBoardSocket'
import * as api from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toaster'
import ItemCard from '@/components/ItemCard'
import LabelBadge from '@/components/LabelBadge'
import { cn } from '@/lib/utils'
import CalendarPicker from '@/components/ui/calendar'
import PrioritySelect from '@/components/PrioritySelect'
import RecurrenceSelect from '@/components/RecurrenceSelect'
import { format } from 'date-fns'
import type { RecurrenceType } from '@/lib/api'
import { Plus, ChevronDown, ChevronRight, X, ArrowUpDown, Check, Search, Calendar, Tag } from 'lucide-react'

type SortOption = 'priority' | 'newest' | 'oldest' | 'due-date'

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'priority', label: 'Priority' },
  { value: 'due-date', label: 'Due Date' },
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
]

const PRIORITY_ORDER: Record<string, number> = {
  HIGH: 0,
  MEDIUM: 1,
  LOW: 2,
  high: 0,
  medium: 1,
  low: 2,
}

export default function BoardPage() {
  const { id } = useParams<{ id: string }>()
  const boardId = Number(id)

  if (!id || isNaN(boardId)) {
    return <Navigate to="/board/1" replace />
  }

  const queryClient = useQueryClient()
  const { status: wsStatus } = useBoardSocket(boardId)

  const [newItemTitle, setNewItemTitle] = useState('')
  const [newItemDueDate, setNewItemDueDate] = useState<Date | null>(null)
  const [newItemPriority, setNewItemPriority] = useState<api.ItemPriority>('medium')
  const [newItemLabels, setNewItemLabels] = useState<string[]>([])
  const [newItemRecurrence, setNewItemRecurrence] = useState<RecurrenceType | null>(null)
  const [newItemRecurrenceDays, setNewItemRecurrenceDays] = useState<string[] | null>(null)
  const [labelPickerOpen, setLabelPickerOpen] = useState(false)
  const [labelInput, setLabelInput] = useState('')
  const labelPickerRef = useRef<HTMLDivElement>(null)
  const [dueDatePickerOpen, setDueDatePickerOpen] = useState(false)
  const dueDatePickerRef = useRef<HTMLDivElement>(null)
  const [showDone, setShowDone] = useState(false)
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortOption>('priority')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortDropdownOpen, setSortDropdownOpen] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const sortDropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sortDropdownRef.current && !sortDropdownRef.current.contains(event.target as Node)) {
        setSortDropdownOpen(false)
      }
    }
    if (sortDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [sortDropdownOpen])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dueDatePickerRef.current && !dueDatePickerRef.current.contains(event.target as Node)) {
        setDueDatePickerOpen(false)
      }
    }
    if (dueDatePickerOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [dueDatePickerOpen])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (labelPickerRef.current && !labelPickerRef.current.contains(event.target as Node)) {
        setLabelPickerOpen(false)
      }
    }
    if (labelPickerOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [labelPickerOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable

      if (e.key === 'Escape' && document.activeElement === searchInputRef.current) {
        setSearchQuery('')
        searchInputRef.current?.blur()
        return
      }

      if (isInput) return

      if (e.key === '/' || ((e.metaKey || e.ctrlKey) && e.key === 'k')) {
        e.preventDefault()
        searchInputRef.current?.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items', boardId],
    queryFn: () => api.getItems(boardId),
  })

  const { data: allLabels = [] } = useQuery({
    queryKey: ['labels', boardId],
    queryFn: () => api.getLabels(boardId),
  })

  const createItemMutation = useMutation({
    mutationFn: (data: Parameters<typeof api.createItem>[1]) => api.createItem(boardId, data),
    onSuccess: () => {
      // Don't add item here - WebSocket will handle it to avoid duplicates
      // Only refetch if WebSocket is disconnected
      if (wsStatus !== 'connected') {
        queryClient.invalidateQueries({ queryKey: ['items', boardId] })
      }
      // Refetch labels in case new ones were created
      queryClient.invalidateQueries({ queryKey: ['labels', boardId] })
      setNewItemTitle('')
      setNewItemDueDate(null)
      setNewItemPriority('medium')
      setNewItemLabels([])
      setNewItemRecurrence(null)
      setNewItemRecurrenceDays(null)
    },
    onError: () => {
      toast({ title: 'Failed to create item', variant: 'destructive' })
    },
  })

  const updateItemMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof api.updateItem>[1] }) =>
      api.updateItem(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['items', boardId] })
      const previous = queryClient.getQueryData<api.Item[]>(['items', boardId])
      // Exclude labels from optimistic update (server returns Label objects, we send strings)
      const { labels: _, ...restData } = data as Record<string, unknown>
      queryClient.setQueryData<api.Item[]>(['items', boardId], (old) =>
        old?.map((item) => (item.id === id ? { ...item, ...restData } as api.Item : item))
      )
      return { previous }
    },
    onSuccess: () => {
      // Refetch labels in case new ones were created via label names
      queryClient.invalidateQueries({ queryKey: ['labels', boardId] })
    },
    onError: (_, __, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['items', boardId], context.previous)
      }
      toast({ title: 'Failed to update item', variant: 'destructive' })
    },
  })

  const deleteItemMutation = useMutation({
    mutationFn: (id: number) => api.deleteItem(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['items', boardId] })
      const previous = queryClient.getQueryData<api.Item[]>(['items', boardId])
      queryClient.setQueryData<api.Item[]>(['items', boardId], (old) =>
        old?.filter((item) => item.id !== id)
      )
      return { previous }
    },
    onError: (_, __, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['items', boardId], context.previous)
      }
      toast({ title: 'Failed to delete item', variant: 'destructive' })
    },
  })

  // Filter items by search query, then by selected label
  const searchLower = searchQuery.toLowerCase()
  const searchedItems = searchQuery
    ? items.filter(
        (item) =>
          item.title.toLowerCase().includes(searchLower) ||
          (item.notes && item.notes.toLowerCase().includes(searchLower))
      )
    : items

  const filteredItems = selectedLabel
    ? searchedItems.filter((item) => item.labels?.some((l) => l.name === selectedLabel))
    : searchedItems

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
      case 'due-date': {
        // Items with no due date go to bottom, otherwise ascending
        if (!a.due_at && !b.due_at) return 0
        if (!a.due_at) return 1
        if (!b.due_at) return -1
        return new Date(a.due_at).getTime() - new Date(b.due_at).getTime()
      }
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
      const data: Parameters<typeof api.createItem>[1] = { title: newItemTitle.trim(), priority: newItemPriority }
      if (newItemDueDate) {
        const d = newItemDueDate
        data.due_at = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate(), 12)).toISOString()
      }
      if (newItemLabels.length > 0) {
        data.labels = newItemLabels
      }
      if (newItemRecurrence) {
        data.recurrence_type = newItemRecurrence
        if (newItemRecurrence === 'custom' && newItemRecurrenceDays) {
          data.recurrence_days = newItemRecurrenceDays
        }
      }
      createItemMutation.mutate(data)
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

  const handleUpdateDueDate = (id: number, dueAt: string | null) => {
    updateItemMutation.mutate({ id, data: { due_at: dueAt } })
  }

  const handleUpdateRecurrence = (id: number, recurrenceType: RecurrenceType | null, recurrenceDays: string[] | null) => {
    updateItemMutation.mutate({ id, data: { recurrence_type: recurrenceType, recurrence_days: recurrenceDays } })
  }

  const handleLabelFilter = (label: string) => {
    setSelectedLabel(selectedLabel === label ? null : label)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Add item form */}
        <form onSubmit={handleAddItem} className="mb-6">
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Add a new task..."
              value={newItemTitle}
              onChange={(e) => setNewItemTitle(e.target.value)}
              className="flex-1"
            />
            <div className="grid grid-cols-3 sm:flex gap-2">
            <div className="relative" ref={dueDatePickerRef}>
              <button
                type="button"
                onClick={() => setDueDatePickerOpen(!dueDatePickerOpen)}
                className={cn(
                  'flex items-center gap-1.5 px-3 h-9 text-sm border rounded-md transition-colors',
                  'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
                  newItemDueDate
                    ? 'text-foreground'
                    : 'text-muted-foreground'
                )}
                title="Due date (optional)"
              >
                <Calendar className="h-4 w-4" />
                {newItemDueDate ? format(newItemDueDate, 'MMM d, yyyy') : 'Due date'}
              </button>
              {dueDatePickerOpen && (
                <div className="absolute z-50 mt-1 left-0 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 p-3">
                  <CalendarPicker
                    selected={newItemDueDate}
                    onSelect={(date) => {
                      setNewItemDueDate(date)
                      setDueDatePickerOpen(false)
                    }}
                  />
                  {newItemDueDate && (
                    <button
                      type="button"
                      onClick={() => {
                        setNewItemDueDate(null)
                        setDueDatePickerOpen(false)
                      }}
                      className="w-full mt-2 px-2 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                    >
                      Clear date
                    </button>
                  )}
                </div>
              )}
            </div>
            <PrioritySelect value={newItemPriority} onChange={setNewItemPriority} size="md" />
            <RecurrenceSelect
              recurrenceType={newItemRecurrence}
              recurrenceDays={newItemRecurrenceDays}
              onChange={(type, days) => {
                setNewItemRecurrence(type)
                setNewItemRecurrenceDays(days)
              }}
              size="md"
            />
            <div className="relative" ref={labelPickerRef}>
              <button
                type="button"
                onClick={() => setLabelPickerOpen(!labelPickerOpen)}
                className={cn(
                  'flex items-center gap-1.5 px-3 h-9 text-sm border rounded-md transition-colors',
                  'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
                  newItemLabels.length > 0
                    ? 'text-foreground'
                    : 'text-muted-foreground'
                )}
                title="Labels (optional)"
              >
                <Tag className="h-4 w-4" />
                {newItemLabels.length > 0 ? `${newItemLabels.length} label${newItemLabels.length > 1 ? 's' : ''}` : 'Labels'}
              </button>
              {labelPickerOpen && (
                <div className="absolute z-50 mt-1 left-0 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 p-3 min-w-[200px]">
                  <div className="flex gap-1 mb-2">
                    <Input
                      value={labelInput}
                      onChange={(e) => setLabelInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          const trimmed = labelInput.trim()
                          if (trimmed && !newItemLabels.includes(trimmed)) {
                            setNewItemLabels([...newItemLabels, trimmed])
                          }
                          setLabelInput('')
                        }
                      }}
                      placeholder="Add label..."
                      className="h-7 text-xs"
                      autoFocus
                    />
                  </div>
                  {allLabels.filter((l) => !newItemLabels.includes(l.name) && l.name.toLowerCase().includes(labelInput.toLowerCase())).length > 0 && (
                    <div className="max-h-32 overflow-y-auto mb-2">
                      {allLabels
                        .filter((l) => !newItemLabels.includes(l.name) && l.name.toLowerCase().includes(labelInput.toLowerCase()))
                        .map((label) => (
                          <button
                            key={label.id}
                            type="button"
                            onClick={() => {
                              setNewItemLabels([...newItemLabels, label.name])
                              setLabelInput('')
                            }}
                            className="w-full text-left px-2 py-1 text-xs hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                          >
                            {label.name}
                          </button>
                        ))}
                    </div>
                  )}
                  {newItemLabels.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-2 border-t border-gray-200 dark:border-gray-700">
                      {newItemLabels.map((label) => (
                        <LabelBadge
                          key={label}
                          label={label}
                          color={allLabels.find((l) => l.name === label)?.color}
                          onRemove={() => setNewItemLabels(newItemLabels.filter((l) => l !== label))}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            <Button type="submit" disabled={!newItemTitle.trim()} className="sm:w-auto">
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
            </div>
          </div>
        </form>

        {/* Search & Sort Bar */}
        <div className="mb-6 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              ref={searchInputRef}
              placeholder="Search tasks... (press / to focus)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-8"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('')
                  searchInputRef.current?.focus()
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="relative" ref={sortDropdownRef}>
            <button
              onClick={() => setSortDropdownOpen(!sortDropdownOpen)}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
            >
              <ArrowUpDown className="h-3.5 w-3.5" />
              <span>{SORT_OPTIONS.find(o => o.value === sortBy)?.label}</span>
              <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', sortDropdownOpen && 'rotate-180')} />
            </button>
            {sortDropdownOpen && (
              <div className="absolute z-50 mt-1 right-0 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1 min-w-[100px]">
                {SORT_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setSortBy(option.value)
                      setSortDropdownOpen(false)
                    }}
                    className={cn(
                      'w-full flex items-center justify-between gap-2 px-3 py-1.5 text-sm',
                      'text-gray-700 dark:text-gray-200',
                      'hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
                      sortBy === option.value && 'bg-gray-50 dark:bg-gray-800'
                    )}
                  >
                    <span>{option.label}</span>
                    {sortBy === option.value && <Check className="h-3.5 w-3.5 text-primary" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Label Filter Bar */}
        {allLabels.length > 0 && (
          <div className="mb-6 flex flex-wrap items-center gap-2" data-testid="label-filter-bar">
            <span className="text-sm text-muted-foreground mr-1">Filter:</span>
            {allLabels.map((label) => (
              <LabelBadge
                key={label.id}
                label={label.name}
                color={label.color}
                onClick={() => handleLabelFilter(label.name)}
                isSelected={selectedLabel === label.name}
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
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
            Todo ({todoItems.length})
          </h2>
          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {todoItems.map((item) => (
                <ItemCard
                  key={item.id}
                  item={item}
                  onToggle={() => handleToggleStatus(item)}
                  onUpdateLabels={(labels) => handleUpdateLabels(item.id, labels)}
                  onUpdatePriority={(priority) => handleUpdatePriority(item.id, priority)}
                  onUpdateDueDate={(dueAt) => handleUpdateDueDate(item.id, dueAt)}
                  onUpdateRecurrence={(type, days) => handleUpdateRecurrence(item.id, type, days)}
                  onDelete={() => handleDelete(item.id)}
                  allLabels={allLabels}
                />
              ))}
            </AnimatePresence>
            {todoItems.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                {searchQuery
                  ? `No tasks matching "${searchQuery}"`
                  : selectedLabel
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

          {(showDone || (searchQuery && doneItems.length > 0)) && (
            <div className="space-y-2">
              <AnimatePresence mode="popLayout">
                {doneItems.map((item) => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    onToggle={() => handleToggleStatus(item)}
                    onUpdateLabels={(labels) => handleUpdateLabels(item.id, labels)}
                    onUpdatePriority={(priority) => handleUpdatePriority(item.id, priority)}
                    onUpdateDueDate={(dueAt) => handleUpdateDueDate(item.id, dueAt)}
                    onUpdateRecurrence={(type, days) => handleUpdateRecurrence(item.id, type, days)}
                    onDelete={() => handleDelete(item.id)}
                    allLabels={allLabels}
                  />
                ))}
              </AnimatePresence>
              {doneItems.length === 0 && (
                <p className="text-center text-muted-foreground py-8">
                  {searchQuery
                    ? `No completed tasks matching "${searchQuery}"`
                    : selectedLabel
                      ? `No completed tasks with label "${selectedLabel}"`
                      : 'Completed tasks will appear here'}
                </p>
              )}
            </div>
          )}
        </div>
      </main>
  )
}
