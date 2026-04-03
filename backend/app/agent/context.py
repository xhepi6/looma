from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ChatDeps:
    user_id: int
    db: AsyncSession
