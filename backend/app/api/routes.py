import asyncio
import colorsys

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import List

from app.db import get_db, async_session_maker
from app.models import User, Board, Item, Label, MediaItem
from app.models.item import ItemStatus
from app.schemas import (
    BoardResponse, BoardCreate,
    ItemResponse, ItemCreate, ItemUpdate,
    LabelResponse, LabelCreate, LabelUpdate,
    MediaItemResponse, MediaItemCreate, MediaItemUpdate,
)
from app.auth.deps import get_current_user
from app.realtime.manager import manager
from app.services.notifications import send_ntfy, build_ntfy_body, PRIORITY_MAP, TAG_MAP
from app.services.recurrence import compute_next_due_date
from app.services.translation import translate_text
from app.services.tmdb import fetch_tmdb_metadata

router = APIRouter(tags=["api"])


# --- Label color helper (matches frontend djb2 hash) ---

LABEL_HUES = [0, 25, 45, 120, 180, 200, 280, 320, 340]


def _djb2_hash(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h << 5) + h) ^ ord(c)
    return abs(h)


def compute_label_color(name: str) -> str:
    h = _djb2_hash(name.lower().strip())
    hue = LABEL_HUES[h % len(LABEL_HUES)]
    r, g, b = colorsys.hls_to_rgb(hue / 360, 0.92, 0.85)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


async def _resolve_labels(
    db: AsyncSession, board_id: int, label_names: list[str]
) -> list[Label]:
    """Resolve label name strings to Label objects, creating new labels as needed."""
    labels = []
    for name in label_names:
        name = name.strip()
        if not name:
            continue
        result = await db.execute(
            select(Label).where(
                Label.board_id == board_id,
                Label.name_lower == name.lower(),
            )
        )
        label = result.scalar_one_or_none()
        if not label:
            label = Label(
                board_id=board_id,
                name=name,
                name_lower=name.lower(),
                color=compute_label_color(name),
            )
            db.add(label)
            await db.flush()
            asyncio.create_task(_translate_label(label.id, label.name))
        labels.append(label)
    return labels


def _label_names(item: Item) -> list[str]:
    """Extract label name strings from an item's label relationship."""
    return [l.name for l in item.labels]


async def enrich_item_with_username(item: Item, db: AsyncSession) -> dict:
    """Add completed_by_username to item response."""
    response = ItemResponse.model_validate(item).model_dump(mode="json")
    if item.completed_by_user_id:
        result = await db.execute(
            select(User.username).where(User.id == item.completed_by_user_id)
        )
        response['completed_by_username'] = result.scalar_one_or_none()
    return response


async def _translate_item(item_id: int, title: str, notes: str | None):
    """Background task: translate item fields and broadcast update."""
    title_en = await translate_text(title)
    notes_en = await translate_text(notes) if notes else None

    if title_en is None and notes_en is None:
        return

    async with async_session_maker() as db:
        result = await db.execute(select(Item).where(Item.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            return

        if title_en is not None:
            item.title_en = title_en
        if notes_en is not None:
            item.notes_en = notes_en

        await db.commit()
        await db.refresh(item)

        enriched = await enrich_item_with_username(item, db)
        await manager.broadcast_to_board(item.board_id, "item.updated", enriched)


async def _translate_label(label_id: int, name: str):
    """Background task: translate label name and broadcast update."""
    english_name = await translate_text(name)
    if english_name is None:
        return

    async with async_session_maker() as db:
        result = await db.execute(select(Label).where(Label.id == label_id))
        label = result.scalar_one_or_none()
        if not label:
            return

        label.english_name = english_name
        await db.commit()
        await db.refresh(label)

        await manager.broadcast_to_board(
            label.board_id, "label.updated",
            LabelResponse.model_validate(label).model_dump(mode="json"),
        )


async def enrich_media_item_with_username(media_item: MediaItem, db: AsyncSession) -> dict:
    """Add added_by_username to media item response."""
    response = MediaItemResponse.model_validate(media_item).model_dump(mode="json")
    if media_item.added_by_user_id:
        result = await db.execute(
            select(User.username).where(User.id == media_item.added_by_user_id)
        )
        response['added_by_username'] = result.scalar_one_or_none()
    return response


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


async def _enrich_media_item_tmdb(media_item_id: int, title: str, media_type: str):
    """Background task: fetch TMDB metadata and broadcast update."""
    metadata = await fetch_tmdb_metadata(title, media_type)
    if metadata is None:
        return

    async with async_session_maker() as db:
        result = await db.execute(select(MediaItem).where(MediaItem.id == media_item_id))
        media_item = result.scalar_one_or_none()
        if not media_item:
            return

        for field, value in metadata.items():
            if value is not None:
                setattr(media_item, field, value)

        await db.commit()
        await db.refresh(media_item)

        enriched = await enrich_media_item_with_username(media_item, db)
        await manager.broadcast_to_board(media_item.board_id, "media.updated", enriched)


# ============ BOARDS ============

@router.get("/boards", response_model=List[BoardResponse])
async def get_boards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all boards."""
    result = await db.execute(select(Board).order_by(Board.id))
    return result.scalars().all()


@router.post("/boards", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new board."""
    board = Board(
        name=data.name,
        board_type=data.board_type,
        created_by_user_id=current_user.id
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific board."""
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


# ============ LABELS ============

@router.get("/boards/{board_id}/labels", response_model=List[LabelResponse])
async def get_labels(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all labels for a board."""
    result = await db.execute(
        select(Label).where(Label.board_id == board_id).order_by(Label.name)
    )
    return result.scalars().all()


@router.post("/boards/{board_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    board_id: int,
    data: LabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new label for a board."""
    result = await db.execute(select(Board).where(Board.id == board_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    # Check for duplicate
    result = await db.execute(
        select(Label).where(
            Label.board_id == board_id,
            Label.name_lower == data.name.lower(),
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Label already exists")

    label = Label(
        board_id=board_id,
        name=data.name,
        name_lower=data.name.lower(),
        color=data.color or compute_label_color(data.name),
    )
    db.add(label)
    await db.commit()
    await db.refresh(label)

    await manager.broadcast_to_board(
        board_id, "label.created",
        LabelResponse.model_validate(label).model_dump(mode="json"),
    )

    asyncio.create_task(_translate_label(label.id, label.name))

    return label


@router.patch("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: int,
    data: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a label."""
    result = await db.execute(select(Label).where(Label.id == label_id))
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        # Check for duplicate with new name
        result = await db.execute(
            select(Label).where(
                Label.board_id == label.board_id,
                Label.name_lower == update_data["name"].lower(),
                Label.id != label_id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Label already exists")
        label.name = update_data["name"]
        label.name_lower = update_data["name"].lower()
        label.english_name = None
    if "color" in update_data:
        label.color = update_data["color"]

    await db.commit()
    await db.refresh(label)

    await manager.broadcast_to_board(
        label.board_id, "label.updated",
        LabelResponse.model_validate(label).model_dump(mode="json"),
    )

    if "name" in update_data:
        asyncio.create_task(_translate_label(label.id, label.name))

    return label


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a label (cascade removes from items)."""
    result = await db.execute(select(Label).where(Label.id == label_id))
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    board_id = label.board_id
    await db.delete(label)
    await db.commit()

    await manager.broadcast_to_board(
        board_id, "label.deleted", {"id": label_id}
    )


# ============ ITEMS ============

@router.get("/boards/{board_id}/items")
async def get_items(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items for a board, ordered by position."""
    result = await db.execute(
        select(Item)
        .where(Item.board_id == board_id)
        .order_by(Item.position.asc(), Item.updated_at.desc())
    )
    items = result.scalars().all()
    return [await enrich_item_with_username(item, db) for item in items]


@router.post("/boards/{board_id}/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    board_id: int,
    data: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new item in a board."""
    # Verify board exists
    result = await db.execute(select(Board).where(Board.id == board_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    # Get max position
    result = await db.execute(
        select(func.coalesce(func.max(Item.position), 0))
        .where(Item.board_id == board_id)
    )
    max_position = result.scalar() or 0

    # Resolve label names to Label objects
    label_objects = await _resolve_labels(db, board_id, data.labels)

    item = Item(
        board_id=board_id,
        title=data.title,
        notes=data.notes,
        due_at=data.due_at,
        priority=data.priority,
        recurrence_type=data.recurrence_type,
        recurrence_days=data.recurrence_days,
        position=max_position + 1,
        last_edited_by_user_id=current_user.id
    )
    item.labels = label_objects
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Enrich with username for broadcast and response
    enriched_item = await enrich_item_with_username(item, db)

    # Broadcast to connected clients
    await manager.broadcast_to_board(
        board_id,
        "item.created",
        enriched_item
    )

    body = build_ntfy_body(
        data.title, data.labels or [], data.priority.value,
        due_at=data.due_at, recurrence_type=data.recurrence_type,
    )
    asyncio.create_task(send_ntfy(
        title="New Task",
        message=body,
        priority=PRIORITY_MAP.get(data.priority.value, "default"),
        tags=TAG_MAP.get(data.priority.value, "blue_circle"),
    ))

    asyncio.create_task(_translate_item(item.id, item.title, item.notes))

    return enriched_item


@router.patch("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Prevent modifying priority/labels on completed items (only status changes allowed)
    if item.status == ItemStatus.DONE:
        allowed_fields = {'status', 'due_at', 'recurrence_type', 'recurrence_days'}
        disallowed_updates = set(update_data.keys()) - allowed_fields
        if disallowed_updates:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify priority, labels, or other fields on completed items. Reopen the item first."
            )

    # Capture old values for re-translation check
    old_title = item.title
    old_notes = item.notes

    # Handle labels separately (relationship, not a simple column)
    label_names = update_data.pop("labels", None)
    if label_names is not None:
        item.labels = await _resolve_labels(db, item.board_id, label_names)

    for field, value in update_data.items():
        setattr(item, field, value)

    # Clear stale translations when source text changes
    if "title" in update_data and item.title != old_title:
        item.title_en = None
    if "notes" in update_data and item.notes != old_notes:
        item.notes_en = None

    # Track completion
    newly_completed = data.status == ItemStatus.DONE and item.completed_at is None
    if newly_completed:
        item.completed_at = datetime.now(timezone.utc)
        item.completed_by_user_id = current_user.id
    elif data.status == ItemStatus.TODO:
        item.completed_at = None
        item.completed_by_user_id = None

    item.last_edited_by_user_id = current_user.id
    item.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)

    # Enrich with username for broadcast and response
    enriched_item = await enrich_item_with_username(item, db)

    # Broadcast to connected clients
    await manager.broadcast_to_board(
        item.board_id,
        "item.updated",
        enriched_item
    )

    if newly_completed:
        body = build_ntfy_body(
            item.title,
            _label_names(item),
            item.priority.value,
            completed_by=current_user.username,
        )
        priority_tag = TAG_MAP.get(item.priority.value, "blue_circle")
        asyncio.create_task(send_ntfy(
            title="Task Completed",
            message=body,
            priority=PRIORITY_MAP.get(item.priority.value, "default"),
            tags=f"white_check_mark,{priority_tag}",
        ))

        # Spawn next occurrence for recurring tasks
        if item.recurrence_type:
            next_due = compute_next_due_date(
                item.due_at, item.recurrence_type, item.recurrence_days
            )
            result = await db.execute(
                select(func.coalesce(func.max(Item.position), 0))
                .where(Item.board_id == item.board_id)
            )
            max_pos = result.scalar() or 0

            next_item = Item(
                board_id=item.board_id,
                title=item.title,
                notes=item.notes,
                priority=item.priority,
                recurrence_type=item.recurrence_type,
                recurrence_days=item.recurrence_days,
                due_at=next_due,
                position=max_pos + 1,
                last_edited_by_user_id=current_user.id,
            )
            next_item.labels = list(item.labels)
            db.add(next_item)
            await db.commit()
            await db.refresh(next_item)

            enriched_next = await enrich_item_with_username(next_item, db)
            await manager.broadcast_to_board(
                item.board_id, "item.created", enriched_next
            )

            # Notify about the new recurring occurrence
            next_body = build_ntfy_body(
                next_item.title,
                _label_names(next_item),
                next_item.priority.value,
                due_at=next_due,
                recurrence_type=next_item.recurrence_type,
            )
            asyncio.create_task(send_ntfy(
                title="Next Occurrence",
                message=next_body,
                priority=PRIORITY_MAP.get(next_item.priority.value, "default"),
                tags=f"repeat,{TAG_MAP.get(next_item.priority.value, 'blue_circle')}",
            ))
            asyncio.create_task(_translate_item(next_item.id, next_item.title, next_item.notes))

    # Translate only if title or notes actually changed
    title_changed = "title" in update_data and item.title != old_title
    notes_changed = "notes" in update_data and item.notes != old_notes
    if title_changed or notes_changed:
        asyncio.create_task(_translate_item(item.id, item.title, item.notes))

    return enriched_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    board_id = item.board_id

    await db.delete(item)
    await db.commit()

    # Broadcast to connected clients
    await manager.broadcast_to_board(
        board_id,
        "item.deleted",
        {"id": item_id}
    )


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
    asyncio.create_task(_enrich_media_item_tmdb(media_item.id, media_item.title, media_item.media_type))

    return enriched


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

    # Clear stale translation and TMDB metadata when title changes
    if "title" in update_data and media_item.title != old_title:
        media_item.title_en = None
        media_item.year = None
        media_item.genre = None
        media_item.rating = None
        media_item.synopsis = None
        media_item.seasons = None
        media_item.tmdb_id = None

    await db.commit()
    await db.refresh(media_item)

    enriched = await enrich_media_item_with_username(media_item, db)
    await manager.broadcast_to_board(media_item.board_id, "media.updated", enriched)

    if "title" in update_data and media_item.title != old_title:
        asyncio.create_task(_translate_media_item(media_item.id, media_item.title))
        asyncio.create_task(_enrich_media_item_tmdb(media_item.id, media_item.title, media_item.media_type))

    return enriched


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
