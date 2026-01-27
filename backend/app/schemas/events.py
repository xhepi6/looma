from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


class WSEvent(BaseModel):
    type: str  # item.created, item.updated, item.deleted, snapshot
    board_id: int
    ts: datetime
    item: Optional[Any] = None
    items: Optional[list] = None
