from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MediaItemCreate(BaseModel):
    title: str
    media_type: str
    status: str = "want_to_watch"


class MediaItemUpdate(BaseModel):
    title: Optional[str] = None
    media_type: Optional[str] = None
    status: Optional[str] = None


class MediaItemResponse(BaseModel):
    id: int
    board_id: int
    title: str
    title_en: Optional[str] = None
    media_type: str
    status: str
    position: float
    added_by_user_id: Optional[int] = None
    added_by_username: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
