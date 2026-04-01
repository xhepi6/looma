const API_BASE = import.meta.env.VITE_API_URL || '/api'

export interface User {
  id: number
  username: string
  is_active: boolean
}

export interface Board {
  id: number
  name: string
  is_default: boolean
}

export interface Label {
  id: number
  name: string
  color: string
  board_id: number
}

export type ItemPriority = 'low' | 'medium' | 'high'
export type RecurrenceType = 'daily' | 'weekly' | 'monthly' | 'weekdays' | 'custom'

export interface Item {
  id: number
  board_id: number
  title: string
  notes: string | null
  status: 'todo' | 'done'
  priority: ItemPriority
  due_at: string | null
  position: number
  created_at: string
  updated_at: string
  completed_at: string | null
  last_edited_by_user_id: number | null
  completed_by_user_id: number | null
  completed_by_username: string | null
  labels: Label[]
  recurrence_type: RecurrenceType | null
  recurrence_days: string[] | null
}

async function fetchApi<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || 'Request failed')
  }

  if (response.status === 204) {
    return null as T
  }

  return response.json()
}

// Auth
export const login = (username: string, password: string) =>
  fetchApi<{ message: string; user: User }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })

export const logout = () =>
  fetchApi<{ message: string }>('/auth/logout', { method: 'POST' })

export const getMe = () => fetchApi<User>('/auth/me')

// Boards
export const getBoards = () => fetchApi<Board[]>('/boards')
export const getBoard = (id: number) => fetchApi<Board>(`/boards/${id}`)

// Labels
export const getLabels = (boardId: number) =>
  fetchApi<Label[]>(`/boards/${boardId}/labels`)

export const createLabel = (boardId: number, data: { name: string; color?: string }) =>
  fetchApi<Label>(`/boards/${boardId}/labels`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const updateLabel = (labelId: number, data: { name?: string; color?: string }) =>
  fetchApi<Label>(`/labels/${labelId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })

export const deleteLabel = (labelId: number) =>
  fetchApi<null>(`/labels/${labelId}`, { method: 'DELETE' })

// Items
export const getItems = (boardId: number) =>
  fetchApi<Item[]>(`/boards/${boardId}/items`)

export const createItem = (boardId: number, data: { title: string; notes?: string; due_at?: string; priority?: ItemPriority; labels?: string[]; recurrence_type?: RecurrenceType; recurrence_days?: string[] }) =>
  fetchApi<Item>(`/boards/${boardId}/items`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const updateItem = (itemId: number, data: Partial<Pick<Item, 'title' | 'notes' | 'status' | 'priority' | 'due_at' | 'position' | 'recurrence_type' | 'recurrence_days'>> & { labels?: string[] }) =>
  fetchApi<Item>(`/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })

export const deleteItem = (itemId: number) =>
  fetchApi<null>(`/items/${itemId}`, { method: 'DELETE' })
