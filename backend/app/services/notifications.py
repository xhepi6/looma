import asyncio
import logging
from datetime import datetime

import httpx

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
