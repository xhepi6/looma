import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select

from app.settings import settings

logger = logging.getLogger(__name__)

PRIORITY_MAP = {
    "low": "low",
    "medium": "default",
    "high": "high",
}

TAG_MAP = {
    "low": "white_circle",
    "medium": "blue_circle",
    "high": "rotating_light",
}


def build_ntfy_body(
    title: str,
    labels: list[str],
    priority: str,
    due_at: datetime | None = None,
    completed_by: str | None = None,
) -> str:
    """Build enriched notification body."""
    line1 = title
    if labels:
        line1 += " " + " ".join(f"[{l}]" for l in labels)

    parts = [f"Priority: {priority.capitalize()}"]
    if due_at:
        parts.append(f"Due: {due_at.strftime('%b %-d')}")
    if completed_by:
        parts.append(f"Completed by {completed_by}")

    line2 = " · ".join(parts)
    return f"{line1}\n{line2}"


async def send_ntfy(title: str, message: str, priority: str = "default", tags: str = ""):
    if not settings.ntfy_username or not settings.ntfy_password:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://ntfy.liesandallies.com/looma",
                content=message,
                headers={
                    "Title": title,
                    "Priority": priority,
                    "Tags": tags,
                },
                auth=(settings.ntfy_username, settings.ntfy_password),
                timeout=5.0,
            )
    except Exception:
        logger.warning("Failed to send ntfy notification", exc_info=True)


REMINDER_PRIORITY_MAP = {
    "overdue": ("urgent", "rotating_light"),
    "today": ("urgent", "rotating_light"),
    "1d": ("high", "warning"),
    "2d": ("default", "blue_circle"),
    "3d": ("low", "white_circle"),
}


def _due_window(days_left: int) -> str | None:
    if days_left < 0:
        return "overdue"
    if days_left == 0:
        return "today"
    if days_left <= 3:
        return f"{days_left}d"
    return None


def _due_label(window: str, due_date) -> str:
    if window == "overdue":
        return f"Overdue (was {due_date.strftime('%b %-d')})"
    if window == "today":
        return "today"
    if window == "1d":
        return "tomorrow"
    return due_date.strftime("%b %-d")


async def check_due_date_reminders():
    """Check for tasks with upcoming due dates and send reminder notifications."""
    from app.db import async_session_maker
    from app.models.item import Item, ItemStatus

    cet = ZoneInfo("Europe/Berlin")
    now_cet = datetime.now(cet)
    today_cet = now_cet.date()

    async with async_session_maker() as db:
        result = await db.execute(
            select(Item).where(
                Item.status == ItemStatus.TODO,
                Item.due_at.isnot(None),
            )
        )
        items = result.scalars().all()

        for item in items:
            due_date = item.due_at.astimezone(cet).date()
            days_left = (due_date - today_cet).days
            window = _due_window(days_left)

            if window is None:
                continue

            if item.reminded_due_window == window:
                continue

            priority, tag = REMINDER_PRIORITY_MAP[window]

            labels_str = ""
            if item.labels:
                labels_str = " " + " ".join(f"[{l}]" for l in item.labels)

            body = f"{item.title}{labels_str}\nDue: {_due_label(window, due_date)}"

            await send_ntfy(
                title="Due Reminder",
                message=body,
                priority=priority,
                tags=tag,
            )

            item.reminded_due_window = window
            item.reminded_at = now_cet
            await db.commit()

    logger.info("Due date reminder check completed")
