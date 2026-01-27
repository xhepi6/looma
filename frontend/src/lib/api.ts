const API_BASE = '/api'

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

export interface Item {
  id: number
  board_id: number
  title: string
  notes: string | null
  status: 'todo' | 'done'
  due_at: string | null
  position: number
  created_at: string
  updated_at: string
  completed_at: string | null
  last_edited_by_user_id: number | null
  labels: string[]
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

// Items
export const getItems = (boardId: number) =>
  fetchApi<Item[]>(`/boards/${boardId}/items`)

export const createItem = (boardId: number, data: { title: string; notes?: string; due_at?: string }) =>
  fetchApi<Item>(`/boards/${boardId}/items`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const updateItem = (itemId: number, data: Partial<Pick<Item, 'title' | 'notes' | 'status' | 'due_at' | 'position' | 'labels'>>) =>
  fetchApi<Item>(`/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })

export const deleteItem = (itemId: number) =>
  fetchApi<null>(`/items/${itemId}`, { method: 'DELETE' })
