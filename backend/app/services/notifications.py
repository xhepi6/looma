import asyncio
import logging

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

PRIORITY_MAP = {
    "low": "low",
    "medium": "default",
    "high": "high",
}


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
