from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class MediaItemCreate(BaseModel):
    title: str
    media_type: Literal["movie", "tv_show"]
    status: Literal["want_to_watch", "watching", "watched"] = "want_to_watch"


class MediaItemUpdate(BaseModel):
    title: Optional[str] = None
    media_type: Optional[Literal["movie", "tv_show"]] = None
    status: Optional[Literal["want_to_watch", "watching", "watched"]] = None


class MediaItemResponse(BaseModel):
    id: int
    board_id: int
    title: str
    title_en: Optional[str] = None
    media_type: str
    status: str
    position: float
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    synopsis: Optional[str] = None
    seasons: Optional[int] = None
    tmdb_id: Optional[int] = None
    added_by_user_id: Optional[int] = None
    added_by_username: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
