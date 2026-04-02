from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BoardCreate(BaseModel):
    name: str
    board_type: str = "task"


class BoardResponse(BaseModel):
    id: int
    name: str
    board_type: str = "task"
    created_by_user_id: Optional[int] = None
    is_default: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
