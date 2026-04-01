# Multi-Board Navigation System

**Issue:** #7
**Date:** 2026-04-01

## Overview

Add a bottom tab bar navigation system to Looma, replacing the current hardcoded single-board layout. This enables multi-board routing and provides a home for future features (media board, chat).

## Decisions

- **Navigation pattern:** Bottom tab bar on all screen sizes (desktop and mobile)
- **No header:** Remove the existing sticky header entirely; all controls move to the tab bar or settings page
- **Tab bar style:** Minimal flat — no blur, no borders, just icons + labels with color differentiation
- **4 tabs:** Tasks (active), Watch List (disabled), Chat (disabled), Settings (active)
- **Disabled tabs:** Visible but greyed out and non-tappable; enabled as features ship (#5, #6)
- **Settings page:** Theme toggle and logout button only

## URL Routing

| Route | View | Notes |
|-------|------|-------|
| `/` | Redirect | → `/board/1` (default board) |
| `/board/:id` | `BoardPage` | Reads `id` from URL params |
| `/settings` | `SettingsPage` | Theme toggle + logout |
| `/login` | `LoginPage` | Outside layout (no tab bar) |

`/chat` and `/board/:id` for media boards are reserved but not routed until #5 and #6 ship.

## Components

### New Components

#### `AppLayout.tsx`
Wraps all authenticated routes. Renders:
- `<Outlet />` for page content (with bottom padding to clear the tab bar)
- `<BottomTabBar />` fixed at the bottom

This replaces the current pattern where `BoardPage` owns the full page layout including the header.

#### `BottomTabBar.tsx`
Fixed-position bar at the bottom of the viewport.

**Tabs:**

| Tab | Icon (Lucide) | Route | Enabled |
|-----|---------------|-------|---------|
| Tasks | `ListTodo` | `/board/1` | Yes |
| Watch List | `Tv` | — | No (greyed out) |
| Chat | `MessageCircle` | — | No (greyed out) |
| Settings | `Settings` | `/settings` | Yes |

**Behavior:**
- Active tab determined by matching current URL path
- Active tab: purple accent color (`text-primary`)
- Inactive enabled tab: muted color (`text-muted-foreground`)
- Disabled tab: reduced opacity (`opacity-35`), `pointer-events-none`
- Flat background: `bg-background` with no border or blur effects
- Dark mode: follows existing color tokens

**Sizing:**
- Tab bar height: ~60px (icon + label + padding)
- Icons: 20-22px
- Labels: 10-11px, below icon

#### `SettingsPage.tsx`
Minimal settings page with:
- Theme toggle (reuses existing theme logic from `useTheme`)
- Logout button (reuses `useAuth().logout()`)
- Centered layout, consistent styling with the rest of the app

### Modified Components

#### `BoardPage.tsx`
- **Remove:** The entire sticky header (logo, theme toggle, logout button)
- **Change:** Read `boardId` from `useParams()` instead of hardcoding `1`
- **Change:** Pass dynamic `boardId` to all queries, mutations, and the WebSocket hook
- Everything else (add item form, search, sort, label filter, item list) stays unchanged

#### `main.tsx`
- **Change:** Restructure routes to use `AppLayout` as a layout route
- **Change:** Add `/board/:id` param route and `/settings` route
- **Change:** Redirect `/` to `/board/1`
- **Keep:** `/login` outside the layout wrapper

#### `useBoardSocket.ts`
- **Change:** Accept `boardId` as a parameter instead of hardcoding `1`
- WebSocket URL becomes `ws://.../ws?board_id=${boardId}`

#### `api.ts`
- **Change:** `getItems` and `createItem` already accept `boardId` — verify all board-scoped API calls use the param, not a hardcoded value

### Unchanged Components

All existing components (`ItemCard`, `LabelBadge`, `LabelInput`, `PrioritySelect`, `DueDatePicker`, `RecurrenceSelect`, UI primitives) remain untouched. They don't reference board ID or navigation.

## Content Padding

The main content area needs bottom padding equal to the tab bar height (~60px + safe-area-inset-bottom for notched devices) so the last item isn't hidden behind the tab bar. This is handled in `AppLayout.tsx` via a padding-bottom on the content wrapper.

## Auth Flow

- `/login` renders outside `AppLayout` (no tab bar)
- On successful login, redirect to `/board/1`
- `AppLayout` is only rendered for authenticated users (existing auth check via `useAuth`)
- On logout (from Settings page), redirect to `/login`

## Backend Changes

None. The existing `GET /api/boards`, `GET /api/boards/{id}/items`, and `WebSocket /ws/{board_id}` endpoints already support dynamic board IDs. No new endpoints or schema changes needed.

## Out of Scope

- Animated page transitions between tabs
- Watch List tab functionality (#5)
- Chat tab functionality (#6)
- `board_type` column on boards table (#5)
- User profile/avatar display
- Swipe gestures between tabs
