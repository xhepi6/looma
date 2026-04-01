"""Backfill English translations for existing items and labels.

Usage:
    docker compose exec api python -m app.commands.backfill_translations

Idempotent — skips records that already have translations.
Safe to interrupt and resume.
"""

import asyncio
import logging

from sqlalchemy import select

from app.db.engine import async_session_maker
from app.models.item import Item
from app.models.label import Label
from app.services.translation import translate_text

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DELAY_BETWEEN_CALLS = 0.5  # seconds


async def backfill():
    async with async_session_maker() as db:
        # --- Labels ---
        result = await db.execute(
            select(Label).where(
                Label.english_name.is_(None),
                Label.name.isnot(None),
            )
        )
        labels = result.scalars().all()
        logger.info("Labels to translate: %d", len(labels))

        for i, label in enumerate(labels, 1):
            english_name = await translate_text(label.name)
            if english_name:
                label.english_name = english_name
                await db.commit()
                logger.info(
                    "Translated label %d/%d: \"%s\" → \"%s\"",
                    i, len(labels), label.name, english_name,
                )
            else:
                logger.warning(
                    "Failed to translate label %d/%d: \"%s\"",
                    i, len(labels), label.name,
                )
            await asyncio.sleep(DELAY_BETWEEN_CALLS)

        # --- Items ---
        result = await db.execute(
            select(Item).where(
                Item.title_en.is_(None),
                Item.title.isnot(None),
            )
        )
        items = result.scalars().all()
        logger.info("Items to translate: %d", len(items))

        for i, item in enumerate(items, 1):
            title_en = await translate_text(item.title)
            if title_en:
                item.title_en = title_en

            if item.notes:
                notes_en = await translate_text(item.notes)
                if notes_en:
                    item.notes_en = notes_en
                await asyncio.sleep(DELAY_BETWEEN_CALLS)

            await db.commit()
            logger.info(
                "Translated item %d/%d: \"%s\" → \"%s\"",
                i, len(items), item.title, title_en or "(failed)",
            )
            await asyncio.sleep(DELAY_BETWEEN_CALLS)

    logger.info("Backfill complete.")


if __name__ == "__main__":
    asyncio.run(backfill())
