import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import List

from app.db import get_db
from app.models import User, Board, Item
from app.models.item import ItemStatus
from app.schemas import BoardResponse, BoardCreate, ItemResponse, ItemCreate, ItemUpdate
from app.auth.deps import get_current_user
from app.realtime.manager import manager
from app.services.notifications import send_ntfy, build_ntfy_body, PRIORITY_MAP, TAG_MAP

router = APIRouter(tags=["api"])


async def enrich_item_with_username(item: Item, db: AsyncSession) -> dict:
    """Add completed_by_username to item response."""
    response = ItemResponse.model_validate(item).model_dump(mode="json")
    if item.completed_by_user_id:
        result = await db.execute(
            select(User.username).where(User.id == item.completed_by_user_id)
        )
        response['completed_by_username'] = result.scalar_one_or_none()
    return response


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

    item = Item(
        board_id=board_id,
        title=data.title,
        notes=data.notes,
        due_at=data.due_at,
        position=max_position + 1,
        last_edited_by_user_id=current_user.id
    )
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

    body = build_ntfy_body(data.title, data.labels or [], data.priority.value, data.due_at)
    asyncio.create_task(send_ntfy(
        title="New Task",
        message=body,
        priority=PRIORITY_MAP.get(data.priority.value, "default"),
        tags=TAG_MAP.get(data.priority.value, "blue_circle"),
    ))

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
        allowed_fields = {'status', 'due_at'}
        disallowed_updates = set(update_data.keys()) - allowed_fields
        if disallowed_updates:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify priority, labels, or other fields on completed items. Reopen the item first."
            )

    for field, value in update_data.items():
        setattr(item, field, value)

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
            item.labels or [],
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
