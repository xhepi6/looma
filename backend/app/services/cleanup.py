import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete

logger = logging.getLogger(__name__)


async def delete_old_completed_tasks():
    """Delete tasks with status DONE whose completed_at is more than 30 days ago."""
    from app.db import async_session_maker
    from app.models.item import Item, ItemStatus

    cutoff = datetime.now(ZoneInfo("UTC")) - timedelta(days=30)

    async with async_session_maker() as db:
        result = await db.execute(
            delete(Item).where(
                Item.status == ItemStatus.DONE,
                Item.completed_at.isnot(None),
                Item.completed_at < cutoff,
            )
        )
        count = result.rowcount
        await db.commit()

    logger.info("Cleanup: deleted %d completed tasks older than 30 days", count)
