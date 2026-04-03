import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from pydantic_ai import RunContext
from sqlalchemy import select, func, or_

from app.agent.agent import agent
from app.agent.context import ChatDeps
from app.models import Board, Item, Label, MediaItem, User
from app.models.item import ItemStatus, ItemPriority
from app.schemas import ItemResponse, MediaItemResponse, LabelResponse
from app.realtime.manager import manager
from app.api.routes import (
    _resolve_labels,
    enrich_item_with_username,
    enrich_media_item_with_username,
    _translate_item,
    _translate_label,
    _translate_media_item,
    _enrich_media_item_tmdb,
    compute_label_color,
)
from app.services.recurrence import compute_next_due_date

logger = logging.getLogger(__name__)


# ============ BOARD TOOLS ============


@agent.tool
async def list_boards(ctx: RunContext[ChatDeps]) -> str:
    """List all available boards with their types and item counts."""
    db = ctx.deps.db
    result = await db.execute(select(Board).order_by(Board.id))
    boards = result.scalars().all()

    if not boards:
        return "No boards found."

    lines = []
    for b in boards:
        lines.append(f"- {b.name} (id={b.id}, type={b.board_type})")
    return "Boards:\n" + "\n".join(lines)


# ============ ITEM TOOLS ============


@agent.tool
async def list_items(
    ctx: RunContext[ChatDeps],
    board_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    label_name: Optional[str] = None,
) -> str:
    """List items on a task board with optional filters.

    Args:
        board_id: The board ID to list items from.
        status: Filter by status: 'todo' or 'done'. If not provided, shows all.
        priority: Filter by priority: 'low', 'medium', or 'high'.
        label_name: Filter by label name (case-insensitive).
    """
    db = ctx.deps.db
    query = select(Item).where(Item.board_id == board_id)

    if status:
        query = query.where(Item.status == status)
    if priority:
        query = query.where(Item.priority == priority)

    query = query.order_by(Item.position.asc())
    result = await db.execute(query)
    items = result.scalars().all()

    # Filter by label in Python (many-to-many)
    if label_name:
        items = [
            i for i in items
            if any(
                l.name.lower() == label_name.lower()
                or (l.english_name and l.english_name.lower() == label_name.lower())
                for l in i.labels
            )
        ]

    if not items:
        return "No items found matching the filters."

    lines = []
    for i in items:
        labels_str = ", ".join(l.name for l in i.labels)
        due_str = f", due {i.due_at.strftime('%Y-%m-%d')}" if i.due_at else ""
        title = i.title_en or i.title
        lines.append(
            f"- [{i.id}] {title} ({i.priority.value} priority{due_str}) "
            f"[{i.status.value}]{f' labels: {labels_str}' if labels_str else ''}"
        )
    return f"Found {len(items)} items:\n" + "\n".join(lines)


@agent.tool
async def create_item(
    ctx: RunContext[ChatDeps],
    board_id: int,
    title: str,
    priority: str = "medium",
    labels: Optional[list[str]] = None,
    notes: Optional[str] = None,
    due_at: Optional[str] = None,
) -> str:
    """Create a new task item on a board.

    Args:
        board_id: The board ID to create the item on.
        title: The title of the task.
        priority: Priority level: 'low', 'medium', or 'high'. Defaults to 'medium'.
        labels: List of label names to assign (will be created if they don't exist).
        notes: Optional notes for the task.
        due_at: Optional due date in ISO format (e.g. '2026-04-05' or '2026-04-05T14:00:00').
    """
    db = ctx.deps.db

    # Parse due_at
    parsed_due = None
    if due_at:
        try:
            parsed_due = datetime.fromisoformat(due_at)
            if parsed_due.tzinfo is None:
                parsed_due = parsed_due.replace(tzinfo=timezone.utc)
        except ValueError:
            return f"Invalid date format: {due_at}. Use ISO format like '2026-04-05'."

    # Get max position
    result = await db.execute(
        select(func.coalesce(func.max(Item.position), 0)).where(Item.board_id == board_id)
    )
    max_position = result.scalar() or 0

    # Resolve labels
    label_objects = await _resolve_labels(db, board_id, labels or [])

    item = Item(
        board_id=board_id,
        title=title,
        notes=notes,
        due_at=parsed_due,
        priority=ItemPriority(priority),
        position=max_position + 1,
        last_edited_by_user_id=ctx.deps.user_id,
    )
    item.labels = label_objects
    db.add(item)
    await db.commit()
    await db.refresh(item)

    enriched = await enrich_item_with_username(item, db)
    await manager.broadcast_to_board(board_id, "item.created", enriched)
    asyncio.create_task(_translate_item(item.id, item.title, item.notes))

    labels_str = ", ".join(l.name for l in item.labels)
    due_str = f", due {parsed_due.strftime('%Y-%m-%d')}" if parsed_due else ""
    label_str = f", labels: {labels_str}" if labels_str else ""
    return f"Created item '{title}' (id={item.id}) on board {board_id} with {priority} priority{label_str}{due_str}."


@agent.tool
async def update_item(
    ctx: RunContext[ChatDeps],
    item_id: int,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    priority: Optional[str] = None,
    labels: Optional[list[str]] = None,
    due_at: Optional[str] = None,
) -> str:
    """Update an existing task item's fields.

    Args:
        item_id: The ID of the item to update.
        title: New title for the item.
        notes: New notes for the item.
        priority: New priority: 'low', 'medium', or 'high'.
        labels: New list of label names (replaces existing labels).
        due_at: New due date in ISO format, or empty string to clear.
    """
    db = ctx.deps.db
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return f"Item {item_id} not found."

    old_title = item.title
    old_notes = item.notes
    changes = []

    if title is not None:
        item.title = title
        item.title_en = None
        changes.append(f"title → '{title}'")
    if notes is not None:
        item.notes = notes
        item.notes_en = None
        changes.append("notes updated")
    if priority is not None:
        item.priority = ItemPriority(priority)
        changes.append(f"priority → {priority}")
    if labels is not None:
        item.labels = await _resolve_labels(db, item.board_id, labels)
        changes.append(f"labels → {', '.join(labels)}")
    if due_at is not None:
        if due_at == "":
            item.due_at = None
            changes.append("due date cleared")
        else:
            try:
                parsed = datetime.fromisoformat(due_at)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                item.due_at = parsed
                changes.append(f"due date → {parsed.strftime('%Y-%m-%d')}")
            except ValueError:
                return f"Invalid date format: {due_at}."

    item.last_edited_by_user_id = ctx.deps.user_id
    item.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)

    enriched = await enrich_item_with_username(item, db)
    await manager.broadcast_to_board(item.board_id, "item.updated", enriched)

    # Re-translate if text changed
    if title is not None and item.title != old_title or notes is not None and item.notes != old_notes:
        asyncio.create_task(_translate_item(item.id, item.title, item.notes))

    return f"Updated item {item_id}: {', '.join(changes)}."


@agent.tool
async def complete_item(ctx: RunContext[ChatDeps], item_id: int) -> str:
    """Mark a task item as done/completed.

    Args:
        item_id: The ID of the item to complete.
    """
    db = ctx.deps.db
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return f"Item {item_id} not found."

    if item.status == ItemStatus.DONE:
        return f"Item '{item.title}' is already completed."

    item.status = ItemStatus.DONE
    item.completed_at = datetime.now(timezone.utc)
    item.completed_by_user_id = ctx.deps.user_id
    item.last_edited_by_user_id = ctx.deps.user_id
    item.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)

    enriched = await enrich_item_with_username(item, db)
    await manager.broadcast_to_board(item.board_id, "item.updated", enriched)

    response = f"Completed item '{item.title}'."

    # Spawn next occurrence for recurring tasks
    if item.recurrence_type:
        next_due = compute_next_due_date(item.due_at, item.recurrence_type, item.recurrence_days)
        max_pos_result = await db.execute(
            select(func.coalesce(func.max(Item.position), 0)).where(Item.board_id == item.board_id)
        )
        max_pos = max_pos_result.scalar() or 0

        next_item = Item(
            board_id=item.board_id,
            title=item.title,
            notes=item.notes,
            priority=item.priority,
            recurrence_type=item.recurrence_type,
            recurrence_days=item.recurrence_days,
            due_at=next_due,
            position=max_pos + 1,
            last_edited_by_user_id=ctx.deps.user_id,
        )
        next_item.labels = list(item.labels)
        db.add(next_item)
        await db.commit()
        await db.refresh(next_item)

        enriched_next = await enrich_item_with_username(next_item, db)
        await manager.broadcast_to_board(item.board_id, "item.created", enriched_next)
        asyncio.create_task(_translate_item(next_item.id, next_item.title, next_item.notes))

        response += f" Next occurrence created with due date {next_due.strftime('%Y-%m-%d') if next_due else 'none'}."

    return response


@agent.tool
async def delete_item(ctx: RunContext[ChatDeps], item_id: int) -> str:
    """Delete a task item permanently. The agent should ask for user confirmation before calling this.

    Args:
        item_id: The ID of the item to delete.
    """
    db = ctx.deps.db
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return f"Item {item_id} not found."

    board_id = item.board_id
    title = item.title

    await db.delete(item)
    await db.commit()
    await manager.broadcast_to_board(board_id, "item.deleted", {"id": item_id})

    return f"Deleted item '{title}' (id={item_id})."


# ============ LABEL TOOLS ============


@agent.tool
async def list_labels(ctx: RunContext[ChatDeps], board_id: int) -> str:
    """List all labels for a board with their names and English translations.

    Args:
        board_id: The board ID to list labels from.
    """
    db = ctx.deps.db
    result = await db.execute(
        select(Label).where(Label.board_id == board_id).order_by(Label.name)
    )
    labels = result.scalars().all()

    if not labels:
        return f"No labels found for board {board_id}."

    lines = []
    for l in labels:
        en = f" (english: {l.english_name})" if l.english_name else ""
        lines.append(f"- {l.name}{en} (id={l.id})")
    return f"Labels for board {board_id}:\n" + "\n".join(lines)


# ============ SEARCH TOOLS ============


@agent.tool
async def search_items(ctx: RunContext[ChatDeps], query: str) -> str:
    """Search for items across all boards by title or notes (searches both original and English translations).

    Args:
        query: The search query string.
    """
    db = ctx.deps.db
    pattern = f"%{query}%"
    result = await db.execute(
        select(Item).where(
            or_(
                Item.title.ilike(pattern),
                Item.title_en.ilike(pattern),
                Item.notes.ilike(pattern),
                Item.notes_en.ilike(pattern),
            )
        ).order_by(Item.updated_at.desc()).limit(20)
    )
    items = result.scalars().all()

    if not items:
        return f"No items found matching '{query}'."

    lines = []
    for i in items:
        title = i.title_en or i.title
        lines.append(f"- [{i.id}] {title} ({i.status.value}, board {i.board_id})")
    return f"Found {len(items)} items matching '{query}':\n" + "\n".join(lines)


# ============ MEDIA TOOLS ============


@agent.tool
async def list_media(
    ctx: RunContext[ChatDeps],
    board_id: int,
    status: Optional[str] = None,
    media_type: Optional[str] = None,
) -> str:
    """List media items (movies/TV shows) on a media board.

    Args:
        board_id: The media board ID.
        status: Filter by status: 'want_to_watch', 'watching', or 'watched'.
        media_type: Filter by type: 'movie' or 'tv_show'.
    """
    db = ctx.deps.db
    query = select(MediaItem).where(MediaItem.board_id == board_id)

    if status:
        query = query.where(MediaItem.status == status)
    if media_type:
        query = query.where(MediaItem.media_type == media_type)

    query = query.order_by(MediaItem.position.asc())
    result = await db.execute(query)
    items = result.scalars().all()

    if not items:
        return "No media items found matching the filters."

    lines = []
    for m in items:
        title = m.title_en or m.title
        year_str = f" ({m.year})" if m.year else ""
        rating_str = f", rating: {m.rating}/10" if m.rating else ""
        lines.append(f"- [{m.id}] {title}{year_str} [{m.media_type}] status: {m.status}{rating_str}")
    return f"Found {len(items)} media items:\n" + "\n".join(lines)


@agent.tool
async def create_media(
    ctx: RunContext[ChatDeps],
    board_id: int,
    title: str,
    media_type: str,
    status: str = "want_to_watch",
) -> str:
    """Add a movie or TV show to the media board.

    Args:
        board_id: The media board ID.
        title: The title of the movie or TV show.
        media_type: Type: 'movie' or 'tv_show'.
        status: Status: 'want_to_watch', 'watching', or 'watched'. Defaults to 'want_to_watch'.
    """
    db = ctx.deps.db

    # Get max position
    result = await db.execute(
        select(func.coalesce(func.max(MediaItem.position), 0)).where(MediaItem.board_id == board_id)
    )
    max_position = result.scalar() or 0

    media_item = MediaItem(
        board_id=board_id,
        title=title,
        media_type=media_type,
        status=status,
        position=max_position + 1,
        added_by_user_id=ctx.deps.user_id,
    )
    db.add(media_item)
    await db.commit()
    await db.refresh(media_item)

    enriched = await enrich_media_item_with_username(media_item, db)
    await manager.broadcast_to_board(board_id, "media.created", enriched)
    asyncio.create_task(_translate_media_item(media_item.id, media_item.title))
    asyncio.create_task(_enrich_media_item_tmdb(media_item.id, media_item.title, media_item.media_type))

    return f"Added '{title}' ({media_type}) to media board with status '{status}' (id={media_item.id})."


@agent.tool
async def update_media(
    ctx: RunContext[ChatDeps],
    media_item_id: int,
    title: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """Update a media item's title or status.

    Args:
        media_item_id: The ID of the media item to update.
        title: New title for the media item.
        status: New status: 'want_to_watch', 'watching', or 'watched'.
    """
    db = ctx.deps.db
    result = await db.execute(select(MediaItem).where(MediaItem.id == media_item_id))
    media_item = result.scalar_one_or_none()
    if not media_item:
        return f"Media item {media_item_id} not found."

    changes = []
    old_title = media_item.title

    if title is not None:
        media_item.title = title
        media_item.title_en = None
        media_item.year = None
        media_item.genre = None
        media_item.rating = None
        media_item.synopsis = None
        media_item.seasons = None
        media_item.tmdb_id = None
        changes.append(f"title → '{title}'")
    if status is not None:
        media_item.status = status
        changes.append(f"status → {status}")

    await db.commit()
    await db.refresh(media_item)

    enriched = await enrich_media_item_with_username(media_item, db)
    await manager.broadcast_to_board(media_item.board_id, "media.updated", enriched)

    if title is not None and title != old_title:
        asyncio.create_task(_translate_media_item(media_item.id, media_item.title))
        asyncio.create_task(_enrich_media_item_tmdb(media_item.id, media_item.title, media_item.media_type))

    return f"Updated media item {media_item_id}: {', '.join(changes)}."


@agent.tool
async def delete_media(ctx: RunContext[ChatDeps], media_item_id: int) -> str:
    """Delete a media item permanently. The agent should ask for user confirmation before calling this.

    Args:
        media_item_id: The ID of the media item to delete.
    """
    db = ctx.deps.db
    result = await db.execute(select(MediaItem).where(MediaItem.id == media_item_id))
    media_item = result.scalar_one_or_none()
    if not media_item:
        return f"Media item {media_item_id} not found."

    board_id = media_item.board_id
    title = media_item.title

    await db.delete(media_item)
    await db.commit()
    await manager.broadcast_to_board(board_id, "media.deleted", {"id": media_item_id})

    return f"Deleted media item '{title}' (id={media_item_id})."


# ============ SUMMARY TOOL ============


@agent.tool
async def get_summary(ctx: RunContext[ChatDeps]) -> str:
    """Get a summary of all boards including item counts, overdue items, and items due soon."""
    db = ctx.deps.db
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    end_of_week = now + timedelta(days=7)

    result = await db.execute(select(Board).order_by(Board.id))
    boards = result.scalars().all()

    sections = []
    for board in boards:
        if board.board_type == "task":
            # Counts
            todo_r = await db.execute(
                select(func.count(Item.id)).where(
                    Item.board_id == board.id, Item.status == ItemStatus.TODO
                )
            )
            todo_count = todo_r.scalar() or 0

            done_r = await db.execute(
                select(func.count(Item.id)).where(
                    Item.board_id == board.id, Item.status == ItemStatus.DONE
                )
            )
            done_count = done_r.scalar() or 0

            # Overdue
            overdue_r = await db.execute(
                select(Item).where(
                    Item.board_id == board.id,
                    Item.status == ItemStatus.TODO,
                    Item.due_at < now,
                    Item.due_at.isnot(None),
                )
            )
            overdue_items = overdue_r.scalars().all()

            # Due today/tomorrow
            due_soon_r = await db.execute(
                select(Item).where(
                    Item.board_id == board.id,
                    Item.status == ItemStatus.TODO,
                    Item.due_at >= now,
                    Item.due_at <= tomorrow,
                )
            )
            due_soon = due_soon_r.scalars().all()

            # Due this week
            due_week_r = await db.execute(
                select(Item).where(
                    Item.board_id == board.id,
                    Item.status == ItemStatus.TODO,
                    Item.due_at >= now,
                    Item.due_at <= end_of_week,
                )
            )
            due_week = due_week_r.scalars().all()

            # High priority
            high_r = await db.execute(
                select(func.count(Item.id)).where(
                    Item.board_id == board.id,
                    Item.status == ItemStatus.TODO,
                    Item.priority == ItemPriority.HIGH,
                )
            )
            high_count = high_r.scalar() or 0

            section = f"📋 {board.name}: {todo_count} todo, {done_count} done"
            if high_count:
                section += f", {high_count} high priority"
            if overdue_items:
                overdue_names = ", ".join(i.title_en or i.title for i in overdue_items[:5])
                section += f"\n  ⚠️ Overdue ({len(overdue_items)}): {overdue_names}"
            if due_soon:
                soon_names = ", ".join(i.title_en or i.title for i in due_soon[:5])
                section += f"\n  📅 Due today/tomorrow ({len(due_soon)}): {soon_names}"
            if due_week:
                section += f"\n  📆 Due this week: {len(due_week)} items"
            sections.append(section)

        elif board.board_type == "media":
            counts = {}
            for s in ["want_to_watch", "watching", "watched"]:
                r = await db.execute(
                    select(func.count(MediaItem.id)).where(
                        MediaItem.board_id == board.id, MediaItem.status == s
                    )
                )
                counts[s] = r.scalar() or 0

            section = (
                f"🎬 {board.name}: {counts['want_to_watch']} to watch, "
                f"{counts['watching']} watching, {counts['watched']} watched"
            )
            sections.append(section)

    return "Summary:\n" + "\n".join(sections)
