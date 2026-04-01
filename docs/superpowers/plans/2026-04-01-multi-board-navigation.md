# Multi-Board Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded single-board layout with a bottom tab bar navigation system supporting dynamic board routing, a settings page, and disabled placeholder tabs for future features.

**Architecture:** New `AppLayout` component wraps authenticated routes with a fixed bottom tab bar. `BoardPage` loses its header and reads `boardId` from URL params. A new `SettingsPage` handles theme toggle and logout. API and WebSocket calls become board-ID-aware.

**Tech Stack:** React Router 6 (layout routes, `useParams`, `Outlet`), Tailwind CSS, Lucide icons, existing `useAuth`/`useTheme` hooks.

---

### Task 1: Make API calls board-ID-aware

**Files:**
- Modify: `frontend/src/lib/api.ts:103-110`

- [ ] **Step 1: Update `getItems` to accept `boardId`**

In `frontend/src/lib/api.ts`, replace the hardcoded `getItems` function:

```typescript
// Old (lines 103-104):
export const getItems = () =>
  fetchApi<Item[]>(`/boards/1/items`)

// New:
export const getItems = (boardId: number) =>
  fetchApi<Item[]>(`/boards/${boardId}/items`)
```

- [ ] **Step 2: Update `createItem` to accept `boardId`**

In the same file, replace the hardcoded `createItem` function:

```typescript
// Old (lines 106-110):
export const createItem = (data: { title: string; notes?: string; due_at?: string; priority?: ItemPriority; labels?: string[]; recurrence_type?: RecurrenceType; recurrence_days?: string[] }) =>
  fetchApi<Item>(`/boards/1/items`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

// New:
export const createItem = (boardId: number, data: { title: string; notes?: string; due_at?: string; priority?: ItemPriority; labels?: string[]; recurrence_type?: RecurrenceType; recurrence_days?: string[] }) =>
  fetchApi<Item>(`/boards/${boardId}/items`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "Make getItems and createItem accept boardId parameter"
```

---

### Task 2: Make WebSocket hook board-ID-aware

**Files:**
- Modify: `frontend/src/hooks/useBoardSocket.ts:20-21,98`

- [ ] **Step 1: Accept `boardId` as a parameter**

In `frontend/src/hooks/useBoardSocket.ts`, change the function signature and remove the hardcoded `boardId`:

```typescript
// Old (lines 20-21):
export function useBoardSocket() {
  const boardId = 1

// New:
export function useBoardSocket(boardId: number) {
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useBoardSocket.ts
git commit -m "Accept boardId parameter in useBoardSocket hook"
```

---

### Task 3: Create BottomTabBar component

**Files:**
- Create: `frontend/src/components/BottomTabBar.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/BottomTabBar.tsx`:

```tsx
import { useLocation, useNavigate } from 'react-router-dom'
import { ListTodo, Tv, MessageCircle, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Tab {
  label: string
  icon: React.ElementType
  path: string | null
  enabled: boolean
}

const tabs: Tab[] = [
  { label: 'Tasks', icon: ListTodo, path: '/board/1', enabled: true },
  { label: 'Watch', icon: Tv, path: null, enabled: false },
  { label: 'Chat', icon: MessageCircle, path: null, enabled: false },
  { label: 'Settings', icon: Settings, path: '/settings', enabled: true },
]

export default function BottomTabBar() {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (tab: Tab) => {
    if (!tab.path) return false
    if (tab.path === '/settings') return location.pathname === '/settings'
    // Match any /board/* path for the Tasks tab
    return location.pathname.startsWith('/board')
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around items-center h-[60px] max-w-lg mx-auto">
        {tabs.map((tab) => {
          const active = isActive(tab)
          const Icon = tab.icon
          return (
            <button
              key={tab.label}
              onClick={() => tab.enabled && tab.path && navigate(tab.path)}
              disabled={!tab.enabled}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 w-full h-full transition-colors',
                active && 'text-primary',
                !active && tab.enabled && 'text-muted-foreground',
                !tab.enabled && 'opacity-35 pointer-events-none'
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] leading-tight">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/BottomTabBar.tsx
git commit -m "Add BottomTabBar component with 4 tabs"
```

---

### Task 4: Create AppLayout component

**Files:**
- Create: `frontend/src/components/AppLayout.tsx`

- [ ] **Step 1: Create the layout wrapper**

Create `frontend/src/components/AppLayout.tsx`:

```tsx
import { Outlet } from 'react-router-dom'
import BottomTabBar from '@/components/BottomTabBar'

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="pb-[calc(60px+env(safe-area-inset-bottom))]">
        <Outlet />
      </div>
      <BottomTabBar />
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AppLayout.tsx
git commit -m "Add AppLayout wrapper with Outlet and BottomTabBar"
```

---

### Task 5: Create SettingsPage

**Files:**
- Create: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Create the settings page**

Create `frontend/src/pages/SettingsPage.tsx`:

```tsx
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { Button } from '@/components/ui/button'
import { Sun, Moon, LogOut } from 'lucide-react'

export default function SettingsPage() {
  const { logout } = useAuth()
  const { resolvedTheme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  return (
    <main className="max-w-md mx-auto px-4 py-8">
      <h1 className="text-xl font-bold text-foreground mb-6">Settings</h1>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg bg-card border border-border">
          <div className="flex items-center gap-3">
            {resolvedTheme === 'dark' ? <Moon className="h-5 w-5 text-muted-foreground" /> : <Sun className="h-5 w-5 text-muted-foreground" />}
            <div>
              <p className="text-sm font-medium text-foreground">Theme</p>
              <p className="text-xs text-muted-foreground">{resolvedTheme === 'dark' ? 'Dark' : 'Light'} mode</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={toggleTheme}>
            {resolvedTheme === 'dark' ? 'Light' : 'Dark'}
          </Button>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-card border border-border">
          <div className="flex items-center gap-3">
            <LogOut className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Sign out</p>
              <p className="text-xs text-muted-foreground">End your session</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={logout}>
            Logout
          </Button>
        </div>
      </div>
    </main>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "Add SettingsPage with theme toggle and logout"
```

---

### Task 6: Update BoardPage — remove header, use URL params

**Files:**
- Modify: `frontend/src/pages/BoardPage.tsx:1-19,39-44,123-126,133-134,309-333`

- [ ] **Step 1: Add `useParams` import and remove unused imports**

In `frontend/src/pages/BoardPage.tsx`, update the imports:

```typescript
// Old (line 1):
import { useState, useRef, useEffect } from 'react'

// New:
import { useState, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
```

Remove unused imports that were only used in the header (line 6, and parts of line 19):

```typescript
// Old (line 6):
import { useTheme } from '@/hooks/useTheme'

// Remove this line entirely — theme toggle moved to SettingsPage
```

Remove `CheckCircle`, `Sun`, `Moon`, `LogOut` from the lucide import (line 19) since they're only used in the header. Keep all other icons.

```typescript
// Old (line 19):
import { LogOut, Plus, ChevronDown, ChevronRight, X, Sun, Moon, ArrowUpDown, Check, CheckCircle, Search, Calendar, Tag } from 'lucide-react'

// New:
import { Plus, ChevronDown, ChevronRight, X, ArrowUpDown, Check, Search, Calendar, Tag } from 'lucide-react'
```

- [ ] **Step 2: Replace hardcoded boardId with URL param**

```typescript
// Old (lines 39-44):
export default function BoardPage() {
  const boardId = 1
  const { logout } = useAuth()
  const queryClient = useQueryClient()
  const { status: wsStatus } = useBoardSocket()
  const { resolvedTheme, setTheme } = useTheme()

// New:
export default function BoardPage() {
  const { id } = useParams<{ id: string }>()
  const boardId = Number(id)
  const queryClient = useQueryClient()
  const { status: wsStatus } = useBoardSocket(boardId)
```

Remove the `useAuth` import from line 4 since `logout` is no longer needed here:

```typescript
// Old (line 4):
import { useAuth } from '@/hooks/useAuth'

// Remove this line entirely
```

- [ ] **Step 3: Update `getItems` call to pass boardId**

```typescript
// Old (lines 123-126):
  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items', boardId],
    queryFn: () => api.getItems(),
  })

// New:
  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items', boardId],
    queryFn: () => api.getItems(boardId),
  })
```

- [ ] **Step 4: Update `createItem` call to pass boardId**

```typescript
// Old (line 134):
    mutationFn: (data: Parameters<typeof api.createItem>[0]) => api.createItem(data),

// New:
    mutationFn: (data: Parameters<typeof api.createItem>[1]) => api.createItem(boardId, data),
```

- [ ] **Step 5: Remove the header and outer background div**

Remove the `toggleTheme` function (lines 297-299):

```typescript
// Remove entirely:
  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }
```

Replace the return statement. Remove the outer `min-h-screen` div (background is now in AppLayout) and remove the entire `<header>` block:

```tsx
// Old (lines 309-336):
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-primary flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Looma
          </h1>
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

// New:
  return (
      <main className="max-w-4xl mx-auto px-4 py-6">
```

And the closing tags at the end:

```tsx
// Old (lines 639-641):
      </main>
    </div>
  )

// New:
      </main>
  )
```

- [ ] **Step 6: Also update the loading state to remove the outer div**

```tsx
// Old (lines 301-307):
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

// New:
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/BoardPage.tsx
git commit -m "Remove header from BoardPage, read boardId from URL params"
```

---

### Task 7: Update routing and auth redirects

**Files:**
- Modify: `frontend/src/main.tsx:1-38`
- Modify: `frontend/src/hooks/useAuth.tsx:52`

- [ ] **Step 1: Rewrite main.tsx with layout routes**

Replace the entire contents of `frontend/src/main.tsx`:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import { AuthProvider } from '@/hooks/useAuth'
import { ThemeProvider } from '@/hooks/useTheme'
import LoginPage from '@/pages/LoginPage'
import BoardPage from '@/pages/BoardPage'
import SettingsPage from '@/pages/SettingsPage'
import AppLayout from '@/components/AppLayout'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<AppLayout />}>
                <Route path="/board/:id" element={<BoardPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
              <Route path="/" element={<Navigate to="/board/1" replace />} />
              <Route path="/board" element={<Navigate to="/board/1" replace />} />
            </Routes>
            <Toaster />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
```

- [ ] **Step 2: Update login redirect in useAuth**

In `frontend/src/hooks/useAuth.tsx`, change the login success redirect:

```typescript
// Old (line 52):
      navigate('/board')

// New:
      navigate('/board/1')
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/main.tsx frontend/src/hooks/useAuth.tsx
git commit -m "Wire up layout routes with AppLayout, update auth redirects"
```

---

### Task 8: Verify and fix any remaining hardcoded references

**Files:**
- Verify: all frontend files

- [ ] **Step 1: Search for remaining hardcoded board references**

Run: `grep -rn "board/1\|boardId = 1\|board_id=1\|boards/1" frontend/src/`

Verify no remaining hardcoded references exist except in the tab bar config (which is intentional for now — Tasks tab points to `/board/1`).

- [ ] **Step 2: Build check**

Run: `cd frontend && npx tsc --noEmit`

Fix any TypeScript errors.

- [ ] **Step 3: Commit any fixes**

```bash
git add -u frontend/src/
git commit -m "Fix remaining hardcoded board references"
```

(Skip this commit if there are no changes.)
