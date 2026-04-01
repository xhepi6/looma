from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


class WSEvent(BaseModel):
    type: str  # item.created, item.updated, item.deleted, label.created, label.updated, label.deleted, snapshot
    board_id: int
    ts: datetime
    item: Optional[Any] = None
    items: Optional[list] = None
    label: Optional[Any] = None
