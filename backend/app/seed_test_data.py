"""
Seed test data for local development.

Usage:
    docker compose -f docker-compose.local.yml exec api python -m app.seed_test_data
"""

import asyncio
import colorsys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

from app.db.engine import async_session_maker
from app.models import User, Board, Item, Label
from app.models.item import ItemStatus, ItemPriority


LABEL_HUES = [0, 25, 45, 120, 180, 200, 280, 320, 340]


def _djb2_hash(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h << 5) + h) ^ ord(c)
    return abs(h)


def _label_color(name: str) -> str:
    h = _djb2_hash(name.lower().strip())
    hue = LABEL_HUES[h % len(LABEL_HUES)]
    r, g, b = colorsys.hls_to_rgb(hue / 360, 0.92, 0.85)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


TEST_ITEMS = [
    # Overdue high-priority
    {
        "title": "Fix leaking kitchen faucet",
        "notes": "The one under the sink has been dripping for a week",
        "priority": ItemPriority.HIGH,
        "label_names": ["home", "urgent"],
        "due_at": datetime.now(timezone.utc) - timedelta(days=2),
    },
    # Due today
    {
        "title": "Buy groceries for dinner",
        "notes": "Pasta, tomatoes, garlic, basil, parmesan",
        "priority": ItemPriority.MEDIUM,
        "label_names": ["errands"],
        "due_at": datetime.now(timezone.utc),
    },
    # Due tomorrow
    {
        "title": "Schedule vet appointment for Luna",
        "priority": ItemPriority.HIGH,
        "label_names": ["pets"],
        "due_at": datetime.now(timezone.utc) + timedelta(days=1),
    },
    # Due in a few days
    {
        "title": "Return package to post office",
        "priority": ItemPriority.LOW,
        "label_names": ["errands"],
        "due_at": datetime.now(timezone.utc) + timedelta(days=3),
    },
    # Recurring daily
    {
        "title": "Water the plants",
        "priority": ItemPriority.LOW,
        "label_names": ["home"],
        "due_at": datetime.now(timezone.utc),
        "recurrence_type": "daily",
    },
    # Recurring weekdays
    {
        "title": "Check mailbox",
        "priority": ItemPriority.LOW,
        "label_names": ["home"],
        "due_at": datetime.now(timezone.utc) + timedelta(days=1),
        "recurrence_type": "weekdays",
    },
    # Recurring weekly
    {
        "title": "Meal prep for the week",
        "notes": "Cook rice, prep veggies, portion out lunches",
        "priority": ItemPriority.MEDIUM,
        "label_names": ["home", "food"],
        "due_at": datetime.now(timezone.utc) + timedelta(days=5),
        "recurrence_type": "weekly",
        "recurrence_days": ["sunday"],
    },
    # No due date, various priorities
    {
        "title": "Research new couch options",
        "notes": "Budget: under $800, needs to fit the living room corner",
        "priority": ItemPriority.LOW,
        "label_names": ["home", "shopping"],
    },
    {
        "title": "Plan weekend trip to the mountains",
        "priority": ItemPriority.MEDIUM,
        "label_names": ["fun"],
    },
    {
        "title": "Call insurance about renewal",
        "priority": ItemPriority.HIGH,
        "label_names": ["admin"],
        "due_at": datetime.now(timezone.utc) + timedelta(days=7),
    },
    # Already completed items
    {
        "title": "Pay electricity bill",
        "priority": ItemPriority.HIGH,
        "label_names": ["admin"],
        "status": ItemStatus.DONE,
        "completed_at": datetime.now(timezone.utc) - timedelta(days=1),
    },
    {
        "title": "Clean the bathroom",
        "priority": ItemPriority.MEDIUM,
        "label_names": ["home"],
        "status": ItemStatus.DONE,
        "completed_at": datetime.now(timezone.utc) - timedelta(hours=5),
    },
]


async def _get_or_create_label(db, board_id: int, name: str) -> Label:
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
            color=_label_color(name),
        )
        db.add(label)
        await db.flush()
    return label


async def main():
    async with async_session_maker() as db:
        # Get default board
        result = await db.execute(select(Board).where(Board.is_default == True))
        board = result.scalar_one_or_none()
        if not board:
            print("Error: No default board found. Run the app first to seed users/board.")
            return

        # Get users for attribution
        result = await db.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        if not users:
            print("Error: No users found. Run the app first to seed users.")
            return

        # Get current max position
        result = await db.execute(
            select(func.coalesce(func.max(Item.position), 0))
            .where(Item.board_id == board.id)
        )
        position = (result.scalar() or 0) + 1

        count = 0
        for i, data in enumerate(TEST_ITEMS):
            user = users[i % len(users)]

            # Resolve labels
            label_objects = []
            for name in data.get("label_names", []):
                label_objects.append(await _get_or_create_label(db, board.id, name))

            item = Item(
                board_id=board.id,
                title=data["title"],
                notes=data.get("notes"),
                priority=data.get("priority", ItemPriority.MEDIUM),
                status=data.get("status", ItemStatus.TODO),
                due_at=data.get("due_at"),
                recurrence_type=data.get("recurrence_type"),
                recurrence_days=data.get("recurrence_days"),
                completed_at=data.get("completed_at"),
                completed_by_user_id=user.id if data.get("status") == ItemStatus.DONE else None,
                last_edited_by_user_id=user.id,
                position=position + i,
            )
            item.labels = label_objects
            db.add(item)
            count += 1

        await db.commit()
        print(f"Seeded {count} test items into board '{board.name}'.")


if __name__ == "__main__":
    asyncio.run(main())
