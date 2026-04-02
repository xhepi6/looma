# Media Board (TV Shows & Movies) — Design Spec

**Issue:** #5
**Date:** 2026-04-02

## Overview

Add a media board for tracking TV shows and movies. The board has its own status flow (Want to Watch → Watching → Watched) and a dedicated page separate from the task board. Users manage media items via a simple card-based UI with status dropdowns, text search, and media type filtering.

## Data Model

### Board Model Change

Add `board_type` column to the existing `boards` table:
- Type: `String(20)`, default `"task"`
- Values: `"task"` or `"media"`
- Existing boards get `"task"` via default

### New `media_items` Table

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `board_id` | FK → boards | Scoped to media board |
| `title` | String(500) | Original title |
| `title_en` | String(500), nullable | English translation (via existing translation layer) |
| `media_type` | String(20) | `"movie"` or `"tv_show"` |
| `status` | String(20) | `"want_to_watch"`, `"watching"`, `"watched"` |
| `position` | Float | Ordering within status group |
| `added_by_user_id` | FK → users | Who added this item |
| `created_at` | DateTime | server_default=func.now() |
| `updated_at` | DateTime | onupdate=func.now() |

Enums stored as strings (same pattern as `ItemStatus`, `ItemPriority`).

## API Endpoints

All endpoints follow the existing patterns in `routes.py` — async handlers, `Depends(get_db)`, `Depends(get_current_user)`.

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/boards/{id}/media` | List all media items for a board |
| `POST` | `/api/boards/{id}/media` | Create a media item |
| `PATCH` | `/api/media/{id}` | Update media item (title, status, media_type) |
| `DELETE` | `/api/media/{id}` | Delete media item |

### Pydantic Schemas

**`MediaItemCreate`:** `title` (str), `media_type` (str), `status` (str, default `"want_to_watch"`)

**`MediaItemUpdate`:** `title` (optional str), `media_type` (optional str), `status` (optional str)

**`MediaItemResponse`:** All fields from the model + `added_by_username` (enriched from user join, same pattern as items).

### WebSocket Events

Broadcast via existing `manager.broadcast_to_board()`:
- `media.created` — payload: full media item
- `media.updated` — payload: full media item
- `media.deleted` — payload: `{ id: media_item_id }`

### Translation

On create and update, fire-and-forget `asyncio.create_task()` to translate `title` → `title_en` using the existing translation service. Same pattern as task items.

## Frontend Architecture

### Routing

A wrapper component at `/board/:id` fetches board data and renders either `BoardPage` or `MediaBoardPage` based on `board_type`. This keeps the two page components fully independent.

```
/board/:id → BoardRouter (fetches board, checks board_type)
  → board_type === "task"  → BoardPage (existing)
  → board_type === "media" → MediaBoardPage (new)
```

### New Components

**`MediaBoardPage.tsx`** — standalone page component:
- Search bar + media type filter (All / Movies / TV Shows) at the top
- Add media form (title input + media type select + submit)
- Grouped list layout with three sections:
  - **Watching** (blue header) — shown first, active items
  - **Want to Watch** (amber header) — backlog
  - **Watched** (green header) — completed
- Each section shows count in header
- Empty state per section ("Nothing here yet")
- Framer Motion `AnimatePresence` for add/remove animations

**`MediaCard.tsx`** — individual media item card:
- Title display
- Media type badge (small colored pill — "Movie" or "TV Show")
- Added by username
- Status dropdown to change between want_to_watch / watching / watched
- Delete button
- Same card styling as `ItemCard` (shadows, rounded corners)
- Framer Motion `layout` and `initial`/`exit` animations

**`AddMediaForm.tsx`** — form to create new media items:
- Title text input
- Media type select (Movie / TV Show)
- Submit button

### State Management

Same patterns as the task board:
- **React Query** for data fetching: `queryKey: ['media', boardId]`
- **Optimistic updates** on mutations with rollback on error
- **`useBoardSocket`** for real-time sync — handle `media.created`, `media.updated`, `media.deleted` events by updating React Query cache directly
- **API client** (`api.ts`): add `getMedia()`, `createMedia()`, `updateMedia()`, `deleteMedia()`

### Search & Filter

Both applied client-side before grouping by status:
- **Text search:** filter media items by title (case-insensitive includes)
- **Media type filter:** toggle between All / Movies / TV Shows

### Navigation

The `BottomTabBar` already has a disabled "Watch" tab. Enable it and point to the media board's URL (e.g., `/board/2`). The board ID for the media board comes from the boards list.

## Database Migration

Alembic migration `008_add_media_board.py`:
1. Add `board_type` column to `boards` table with default `"task"`
2. Create `media_items` table with all columns and foreign keys

## Seeding

Update `seed.py` to create a "Watch List" board with `board_type: "media"` alongside the existing "Shared Todo" board. Idempotent — skip if a media board already exists.

## What's NOT Included

- No drag-and-drop — status changes via dropdown only
- No media metadata (plot, actors, ratings, poster images)
- No external API integration (TMDB, IMDB) — manual entry only
- No labels on media items
- No priority or due dates on media items
- No recurrence
- No notifications for media items
