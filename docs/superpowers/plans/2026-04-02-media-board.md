# Media Board (TV Shows & Movies) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a media board for tracking TV shows and movies with a grouped-list UI, status dropdowns, search, and media type filtering.

**Architecture:** New `MediaItem` model + Alembic migration, CRUD endpoints in `routes.py` with WebSocket broadcast, new `MediaBoardPage` rendered via a `BoardRouter` wrapper that switches on `board_type`. Seeding creates a "Watch List" board alongside the existing task board.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, React, React Query, Framer Motion, Tailwind CSS, Shadcn/ui, Lucide icons

---

### Task 1: Add `board_type` Column to Board Model + Migration

**Files:**
- Modify: `backend/app/models/board.py`
- Modify: `backend/app/schemas/board.py`
- Create: `backend/alembic/versions/008_add_media_board.py`

- [ ] **Step 1: Add `board_type` column to Board model**

In `backend/app/models/board.py`, add the `board_type` column:

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.db.engine import Base


class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    board_type = Column(String(20), nullable=False, server_default="task")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: Add `board_type` to BoardResponse schema**

In `backend/app/schemas/board.py`, add the field:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BoardCreate(BaseModel):
    name: str
    board_type: str = "task"


class BoardResponse(BaseModel):
    id: int
    name: str
    board_type: str = "task"
    created_by_user_id: Optional[int] = None
    is_default: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: Create Alembic migration `008_add_media_board.py`**

Create `backend/alembic/versions/008_add_media_board.py`:

```python
"""Add board_type to boards and create media_items table.

Revision ID: 008_add_media_board
Revises: 007_add_translation_fields
Create Date: 2026-04-02
"""

import sqlalchemy as sa
from alembic import op

from migration_helpers import column_exists, table_exists

revision = "008_add_media_board"
down_revision = "007_add_translation_fields"
branch_labels = None
depends_on = None


def upgrade():
    # Add board_type to boards
    if not column_exists("boards", "board_type"):
        with op.batch_alter_table("boards") as batch_op:
            batch_op.add_column(
                sa.Column("board_type", sa.String(20), nullable=False, server_default="task")
            )

    # Create media_items table
    if not table_exists("media_items"):
        op.create_table(
            "media_items",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("board_id", sa.Integer, sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("title_en", sa.String(500), nullable=True),
            sa.Column("media_type", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="want_to_watch"),
            sa.Column("position", sa.Float, nullable=False, default=0.0),
            sa.Column("added_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        )


def downgrade():
    op.drop_table("media_items")
    with op.batch_alter_table("boards") as batch_op:
        batch_op.drop_column("board_type")
```

- [ ] **Step 4: Run the migration**

Run: `cd backend && python -m alembic upgrade head`
Expected: Migration applies successfully, `media_items` table created, `board_type` column added to `boards`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/board.py backend/app/schemas/board.py backend/alembic/versions/008_add_media_board.py
git commit -m "feat: add board_type column and media_items table (Closes #5 - schema)"
```

---

### Task 2: Create MediaItem Model + Pydantic Schemas

**Files:**
- Create: `backend/app/models/media_item.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/schemas/media_item.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: Create MediaItem model**

Create `backend/app/models/media_item.py`:

```python
import enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func

from app.db.engine import Base


class MediaType(str, enum.Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"


class MediaStatus(str, enum.Enum):
    WANT_TO_WATCH = "want_to_watch"
    WATCHING = "watching"
    WATCHED = "watched"


class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    title_en = Column(String(500), nullable=True)
    media_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default="want_to_watch")
    position = Column(Float, default=0.0, nullable=False)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Register MediaItem in models `__init__.py`**

Update `backend/app/models/__init__.py`:

```python
from .user import User
from .session import Session
from .board import Board
from .label import Label
from .item import Item
from .media_item import MediaItem

__all__ = ["User", "Session", "Board", "Label", "Item", "MediaItem"]
```

- [ ] **Step 3: Create Pydantic schemas for MediaItem**

Create `backend/app/schemas/media_item.py`:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MediaItemCreate(BaseModel):
    title: str
    media_type: str
    status: str = "want_to_watch"


class MediaItemUpdate(BaseModel):
    title: Optional[str] = None
    media_type: Optional[str] = None
    status: Optional[str] = None


class MediaItemResponse(BaseModel):
    id: int
    board_id: int
    title: str
    title_en: Optional[str] = None
    media_type: str
    status: str
    position: float
    added_by_user_id: Optional[int] = None
    added_by_username: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Register schemas in `__init__.py`**

Update `backend/app/schemas/__init__.py`:

```python
from .auth import LoginRequest, UserResponse
from .board import BoardResponse, BoardCreate
from .item import ItemResponse, ItemCreate, ItemUpdate
from .label import LabelResponse, LabelCreate, LabelUpdate
from .media_item import MediaItemResponse, MediaItemCreate, MediaItemUpdate
from .events import WSEvent

__all__ = [
    "LoginRequest", "UserResponse",
    "BoardResponse", "BoardCreate",
    "ItemResponse", "ItemCreate", "ItemUpdate",
    "LabelResponse", "LabelCreate", "LabelUpdate",
    "MediaItemResponse", "MediaItemCreate", "MediaItemUpdate",
    "WSEvent"
]
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/media_item.py backend/app/models/__init__.py backend/app/schemas/media_item.py backend/app/schemas/__init__.py
git commit -m "feat: add MediaItem model and Pydantic schemas"
```

---

### Task 3: Add Media CRUD API Endpoints

**Files:**
- Modify: `backend/app/api/routes.py`

- [ ] **Step 1: Add imports for media types**

At the top of `backend/app/api/routes.py`, add to the existing imports:

```python
from app.models import User, Board, Item, Label, MediaItem
from app.schemas import (
    BoardResponse, BoardCreate,
    ItemResponse, ItemCreate, ItemUpdate,
    LabelResponse, LabelCreate, LabelUpdate,
    MediaItemResponse, MediaItemCreate, MediaItemUpdate,
)
```

- [ ] **Step 2: Add media translation helper**

Add this function after the existing `_translate_item` function (after line 116 in `routes.py`):

```python
async def _translate_media_item(media_item_id: int, title: str):
    """Background task: translate media item title and broadcast update."""
    title_en = await translate_text(title)
    if title_en is None:
        return

    async with async_session_maker() as db:
        result = await db.execute(select(MediaItem).where(MediaItem.id == media_item_id))
        media_item = result.scalar_one_or_none()
        if not media_item:
            return

        media_item.title_en = title_en
        await db.commit()
        await db.refresh(media_item)

        enriched = await enrich_media_item_with_username(media_item, db)
        await manager.broadcast_to_board(media_item.board_id, "media.updated", enriched)
```

- [ ] **Step 3: Add media item enrichment helper**

Add this function right before the `_translate_media_item` function:

```python
async def enrich_media_item_with_username(media_item: MediaItem, db: AsyncSession) -> dict:
    """Add added_by_username to media item response."""
    response = MediaItemResponse.model_validate(media_item).model_dump(mode="json")
    if media_item.added_by_user_id:
        result = await db.execute(
            select(User.username).where(User.id == media_item.added_by_user_id)
        )
        response['added_by_username'] = result.scalar_one_or_none()
    return response
```

- [ ] **Step 4: Add GET media items endpoint**

Add at the end of `routes.py`:

```python
# ============ MEDIA ITEMS ============

@router.get("/boards/{board_id}/media")
async def get_media_items(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all media items for a board, ordered by position."""
    result = await db.execute(
        select(MediaItem)
        .where(MediaItem.board_id == board_id)
        .order_by(MediaItem.position.asc(), MediaItem.updated_at.desc())
    )
    items = result.scalars().all()
    return [await enrich_media_item_with_username(item, db) for item in items]
```

- [ ] **Step 5: Add POST media item endpoint**

Add after the GET endpoint:

```python
@router.post("/boards/{board_id}/media", response_model=MediaItemResponse, status_code=status.HTTP_201_CREATED)
async def create_media_item(
    board_id: int,
    data: MediaItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new media item in a board."""
    result = await db.execute(select(Board).where(Board.id == board_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    # Get max position
    result = await db.execute(
        select(func.coalesce(func.max(MediaItem.position), 0))
        .where(MediaItem.board_id == board_id)
    )
    max_position = result.scalar() or 0

    media_item = MediaItem(
        board_id=board_id,
        title=data.title,
        media_type=data.media_type,
        status=data.status,
        position=max_position + 1,
        added_by_user_id=current_user.id,
    )
    db.add(media_item)
    await db.commit()
    await db.refresh(media_item)

    enriched = await enrich_media_item_with_username(media_item, db)

    await manager.broadcast_to_board(board_id, "media.created", enriched)
    asyncio.create_task(_translate_media_item(media_item.id, media_item.title))

    return enriched
```

- [ ] **Step 6: Add PATCH media item endpoint**

```python
@router.patch("/media/{media_item_id}", response_model=MediaItemResponse)
async def update_media_item(
    media_item_id: int,
    data: MediaItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a media item."""
    result = await db.execute(select(MediaItem).where(MediaItem.id == media_item_id))
    media_item = result.scalar_one_or_none()
    if not media_item:
        raise HTTPException(status_code=404, detail="Media item not found")

    update_data = data.model_dump(exclude_unset=True)
    old_title = media_item.title

    for field, value in update_data.items():
        setattr(media_item, field, value)

    # Clear stale translation when title changes
    if "title" in update_data and media_item.title != old_title:
        media_item.title_en = None

    await db.commit()
    await db.refresh(media_item)

    enriched = await enrich_media_item_with_username(media_item, db)
    await manager.broadcast_to_board(media_item.board_id, "media.updated", enriched)

    if "title" in update_data and media_item.title != old_title:
        asyncio.create_task(_translate_media_item(media_item.id, media_item.title))

    return enriched
```

- [ ] **Step 7: Add DELETE media item endpoint**

```python
@router.delete("/media/{media_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_item(
    media_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a media item."""
    result = await db.execute(select(MediaItem).where(MediaItem.id == media_item_id))
    media_item = result.scalar_one_or_none()
    if not media_item:
        raise HTTPException(status_code=404, detail="Media item not found")

    board_id = media_item.board_id
    await db.delete(media_item)
    await db.commit()

    await manager.broadcast_to_board(board_id, "media.deleted", {"id": media_item_id})
```

- [ ] **Step 8: Verify backend starts**

Run: `cd backend && python -c "from app.api.routes import router; print('Routes OK')"`
Expected: `Routes OK`

- [ ] **Step 9: Commit**

```bash
git add backend/app/api/routes.py
git commit -m "feat: add media CRUD API endpoints with WebSocket broadcast"
```

---

### Task 4: Seed the Watch List Board

**Files:**
- Modify: `backend/app/services/seed.py`

- [ ] **Step 1: Update seed to create media board**

Replace the contents of `backend/app/services/seed.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Board
from app.auth.password import hash_password
from app.settings import settings


async def seed_database(db: AsyncSession):
    """Seed initial users and default board."""
    if not settings.seed_admin_users:
        return

    # Check if users exist
    result = await db.execute(select(User))
    existing_users = result.scalars().all()

    if len(existing_users) >= 2:
        print("Users already seeded, skipping...")
    else:
        # Create users
        users_to_create = [
            {"username": settings.seed_user_1_username, "password": settings.seed_user_1_password},
            {"username": settings.seed_user_2_username, "password": settings.seed_user_2_password},
        ]

        created_user = None
        for user_data in users_to_create:
            result = await db.execute(
                select(User).where(User.username == user_data["username"])
            )
            if result.scalar_one_or_none():
                continue

            user = User(
                username=user_data["username"],
                password_hash=hash_password(user_data["password"]),
                is_active=True
            )
            db.add(user)
            created_user = user
            print(f"Created user: {user_data['username']}")

        await db.commit()

    # Create default task board if not exists
    result = await db.execute(select(Board).where(Board.is_default == True))
    if not result.scalar_one_or_none():
        # Get a user for created_by
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        board = Board(
            name="Shared Todo",
            board_type="task",
            is_default=True,
            created_by_user_id=user.id if user else None
        )
        db.add(board)
        await db.commit()
        print("Created default board: Shared Todo")

    # Create media board if not exists
    result = await db.execute(select(Board).where(Board.board_type == "media"))
    if not result.scalar_one_or_none():
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        media_board = Board(
            name="Watch List",
            board_type="media",
            is_default=False,
            created_by_user_id=user.id if user else None
        )
        db.add(media_board)
        await db.commit()
        print("Created media board: Watch List")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/seed.py
git commit -m "feat: seed Watch List media board on startup"
```

---

### Task 5: Add Media Types and API Functions to Frontend

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add `board_type` to Board interface and media types/API functions**

In `frontend/src/lib/api.ts`, add `board_type` to the `Board` interface:

```typescript
export interface Board {
  id: number
  name: string
  board_type: string
  is_default: boolean
}
```

Then add the media types and API functions at the end of the file:

```typescript
// Media
export type MediaType = 'movie' | 'tv_show'
export type MediaStatus = 'want_to_watch' | 'watching' | 'watched'

export interface MediaItem {
  id: number
  board_id: number
  title: string
  title_en: string | null
  media_type: MediaType
  status: MediaStatus
  position: number
  added_by_user_id: number | null
  added_by_username: string | null
  created_at: string
  updated_at: string
}

export const getMedia = (boardId: number) =>
  fetchApi<MediaItem[]>(`/boards/${boardId}/media`)

export const createMedia = (boardId: number, data: { title: string; media_type: MediaType; status?: MediaStatus }) =>
  fetchApi<MediaItem>(`/boards/${boardId}/media`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const updateMedia = (mediaId: number, data: { title?: string; media_type?: MediaType; status?: MediaStatus }) =>
  fetchApi<MediaItem>(`/media/${mediaId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })

export const deleteMedia = (mediaId: number) =>
  fetchApi<null>(`/media/${mediaId}`, { method: 'DELETE' })
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add media types and API functions to frontend client"
```

---

### Task 6: Update WebSocket Hook for Media Events

**Files:**
- Modify: `frontend/src/hooks/useBoardSocket.ts`

- [ ] **Step 1: Add media event handling to useBoardSocket**

In `frontend/src/hooks/useBoardSocket.ts`, update the imports to include `MediaItem`:

```typescript
import type { Item, MediaItem } from '@/lib/api'
```

Update the `WSEvent` interface to include a `media` field:

```typescript
interface WSEvent {
  type: string
  board_id: number
  ts: string
  item?: Item
  media?: MediaItem
}
```

Then add media cases inside the `handleEvent` `switch` statement, after the `label.deleted` case (after line 85):

```typescript
      case 'media.created':
        queryClient.setQueryData<MediaItem[]>(['media', event.board_id], (old) => {
          if (!old || !event.media) return old
          if (old.some((m) => m.id === event.media!.id)) {
            return old.map((m) => m.id === event.media!.id ? event.media! : m)
          }
          return [...old, event.media].sort((a, b) => a.position - b.position)
        })
        break

      case 'media.updated':
        queryClient.setQueryData<MediaItem[]>(['media', event.board_id], (old) => {
          if (!old || !event.media) return old
          return old
            .map((m) => (m.id === event.media!.id ? event.media! : m))
            .sort((a, b) => a.position - b.position)
        })
        break

      case 'media.deleted':
        queryClient.setQueryData<MediaItem[]>(['media', event.board_id], (old) => {
          if (!old || !event.media) return old
          return old.filter((m) => m.id !== event.media!.id)
        })
        break
```

Also update the WebSocket broadcast in the backend to use `media` as the payload key instead of `item`. In `backend/app/realtime/manager.py`, check the broadcast format.

- [ ] **Step 2: Check WebSocket manager broadcast format**

Read `backend/app/realtime/manager.py` to see how the payload key is set. If it always uses `item`, we need to update the manager or the route handlers to use `media` for media events.

The manager's `broadcast_to_board` method likely sends:
```json
{"type": "media.created", "board_id": 1, "ts": "...", "item": {...}}
```

We need the media payload to arrive under a `media` key. Check the manager implementation and update accordingly. If the manager hardcodes `"item"` as the key, update it to accept a configurable key, or handle it in the frontend by reading from `event.item` as a fallback.

**Simpler approach:** In the frontend, read media events from `event.item` (since the manager sends all payloads as `item`). Update the WSEvent interface back:

```typescript
interface WSEvent {
  type: string
  board_id: number
  ts: string
  item?: any  // Used for both item and media payloads
}
```

And update the media cases to read from `event.item`:

```typescript
      case 'media.created':
        queryClient.setQueryData<MediaItem[]>(['media', event.board_id], (old) => {
          const media = event.item as MediaItem | undefined
          if (!old || !media) return old
          if (old.some((m) => m.id === media.id)) {
            return old.map((m) => m.id === media.id ? media : m)
          }
          return [...old, media].sort((a, b) => a.position - b.position)
        })
        break

      case 'media.updated':
        queryClient.setQueryData<MediaItem[]>(['media', event.board_id], (old) => {
          const media = event.item as MediaItem | undefined
          if (!old || !media) return old
          return old
            .map((m) => (m.id === media.id ? media : m))
            .sort((a, b) => a.position - b.position)
        })
        break

      case 'media.deleted':
        queryClient.setQueryData<MediaItem[]>(['media', event.board_id], (old) => {
          const media = event.item as { id: number } | undefined
          if (!old || !media) return old
          return old.filter((m) => m.id !== media.id)
        })
        break
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useBoardSocket.ts
git commit -m "feat: handle media WebSocket events in useBoardSocket"
```

---

### Task 7: Create MediaCard Component

**Files:**
- Create: `frontend/src/components/MediaCard.tsx`

- [ ] **Step 1: Create MediaCard component**

Create `frontend/src/components/MediaCard.tsx`:

```tsx
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { MediaItem, MediaStatus } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Trash2, Film, Tv } from 'lucide-react'

const STATUS_OPTIONS: { value: MediaStatus; label: string }[] = [
  { value: 'want_to_watch', label: 'Want to Watch' },
  { value: 'watching', label: 'Watching' },
  { value: 'watched', label: 'Watched' },
]

const STATUS_COLORS: Record<MediaStatus, string> = {
  want_to_watch: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50',
  watching: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50',
  watched: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/50',
}

interface MediaCardProps {
  item: MediaItem
  onUpdateStatus: (status: MediaStatus) => void
  onDelete: () => void
}

export default function MediaCard({ item, onUpdateStatus, onDelete }: MediaCardProps) {
  const isWatched = item.status === 'watched'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn(
        'group flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border shadow-sm transition-shadow',
        isWatched && 'opacity-60'
      )}
    >
      {/* Media type icon */}
      <div className="flex-shrink-0 text-muted-foreground">
        {item.media_type === 'movie' ? (
          <Film className="h-4 w-4" />
        ) : (
          <Tv className="h-4 w-4" />
        )}
      </div>

      {/* Title and metadata */}
      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-medium truncate', isWatched && 'line-through')}>
          {item.title}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={cn(
            'text-[10px] font-medium px-1.5 py-0.5 rounded-full',
            item.media_type === 'movie'
              ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/50'
              : 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50'
          )}>
            {item.media_type === 'movie' ? 'Movie' : 'TV Show'}
          </span>
          {item.added_by_username && (
            <span className="text-[10px] text-muted-foreground">
              {item.added_by_username}
            </span>
          )}
        </div>
      </div>

      {/* Status dropdown */}
      <select
        value={item.status}
        onChange={(e) => onUpdateStatus(e.target.value as MediaStatus)}
        className={cn(
          'text-xs font-medium px-2 py-1 rounded-md border-0 cursor-pointer appearance-none',
          STATUS_COLORS[item.status]
        )}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Delete button */}
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </motion.div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/MediaCard.tsx
git commit -m "feat: add MediaCard component with status dropdown"
```

---

### Task 8: Create MediaBoardPage Component

**Files:**
- Create: `frontend/src/pages/MediaBoardPage.tsx`

- [ ] **Step 1: Create MediaBoardPage**

Create `frontend/src/pages/MediaBoardPage.tsx`:

```tsx
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/MediaBoardPage.tsx
git commit -m "feat: add MediaBoardPage with search, filters, and grouped layout"
```

---

### Task 9: Create BoardRouter and Update Routing + Navigation

**Files:**
- Create: `frontend/src/components/BoardRouter.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/components/BottomTabBar.tsx`

- [ ] **Step 1: Create BoardRouter component**

Create `frontend/src/components/BoardRouter.tsx`:

```tsx
import { useParams, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'
import BoardPage from '@/pages/BoardPage'
import MediaBoardPage from '@/pages/MediaBoardPage'

export default function BoardRouter() {
  const { id } = useParams<{ id: string }>()
  const boardId = Number(id)

  if (!id || isNaN(boardId)) {
    return <Navigate to="/board/1" replace />
  }

  const { data: board, isLoading, error } = useQuery({
    queryKey: ['board', boardId],
    queryFn: () => api.getBoard(boardId),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error || !board) {
    return <Navigate to="/board/1" replace />
  }

  if (board.board_type === 'media') {
    return <MediaBoardPage boardId={boardId} />
  }

  return <BoardPage />
}
```

- [ ] **Step 2: Update main.tsx to use BoardRouter**

In `frontend/src/main.tsx`, replace the `BoardPage` import and route:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import { AuthProvider } from '@/hooks/useAuth'
import { ThemeProvider } from '@/hooks/useTheme'
import LoginPage from '@/pages/LoginPage'
import BoardRouter from '@/components/BoardRouter'
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
                <Route path="/board/:id" element={<BoardRouter />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
              <Route path="/" element={<Navigate to="/board/1" replace />} />
              <Route path="/board" element={<Navigate to="/board/1" replace />} />
              <Route path="*" element={<Navigate to="/board/1" replace />} />
            </Routes>
            <Toaster />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
```

- [ ] **Step 3: Update BottomTabBar to enable Watch tab**

The Watch tab needs to link to the media board. Since the media board ID is dynamic (seeded as board 2, but could be any ID), we fetch the boards list and find the media board.

Replace `frontend/src/components/BottomTabBar.tsx`:

```tsx
import { useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ListTodo, Tv, MessageCircle, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import * as api from '@/lib/api'

export default function BottomTabBar() {
  const location = useLocation()
  const navigate = useNavigate()

  const { data: boards = [] } = useQuery({
    queryKey: ['boards'],
    queryFn: api.getBoards,
  })

  const taskBoard = boards.find((b) => b.board_type === 'task')
  const mediaBoard = boards.find((b) => b.board_type === 'media')

  const tabs = [
    { label: 'Tasks', icon: ListTodo, path: taskBoard ? `/board/${taskBoard.id}` : '/board/1', enabled: true },
    { label: 'Watch', icon: Tv, path: mediaBoard ? `/board/${mediaBoard.id}` : null, enabled: !!mediaBoard },
    { label: 'Chat', icon: MessageCircle, path: null, enabled: false },
    { label: 'Settings', icon: Settings, path: '/settings', enabled: true },
  ]

  const isActive = (tab: typeof tabs[number]) => {
    if (!tab.path) return false
    if (tab.path === '/settings') return location.pathname === '/settings'
    return location.pathname === tab.path
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

- [ ] **Step 4: Verify frontend compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/BoardRouter.tsx frontend/src/main.tsx frontend/src/components/BottomTabBar.tsx
git commit -m "feat: add BoardRouter, enable Watch tab in navigation"
```

---

### Task 10: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run backend migration and start server**

```bash
cd backend && python -m alembic upgrade head
```

- [ ] **Step 2: Start backend and verify seeding**

Start the backend, verify "Created media board: Watch List" appears in logs, and test the API:

```bash
# In another terminal or via curl:
# Login first, then:
# GET /api/boards should return two boards (Shared Todo + Watch List)
# GET /api/boards/2/media should return empty array
# POST /api/boards/2/media with {"title": "Breaking Bad", "media_type": "tv_show"} should create item
```

- [ ] **Step 3: Start frontend and test end-to-end**

```bash
cd frontend && npm run dev
```

Verify:
- Bottom tab bar shows "Watch" tab as enabled
- Clicking "Watch" navigates to the media board
- Can add a movie or TV show via the form
- Media card shows with type badge, status dropdown, delete button
- Changing status via dropdown moves card between sections
- Search filters by title
- Type filter toggles between All/Movies/TV Shows
- Real-time sync: open in two tabs, changes appear in both

- [ ] **Step 4: Final commit with issue reference**

```bash
git add -A
git commit -m "feat: add TV Shows and Movies board

Closes #5"
```
