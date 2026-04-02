import enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func

from app.db.engine import Base


class MediaType(str, enum.Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"


class MediaStatus(str, enum.Enum):
    WANT_TO_WATCH = "want_to_watch"
    WATCHING = "watching"
    WATCHED = "watched"


class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    title_en = Column(String(500), nullable=True)
    media_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default="want_to_watch")
    position = Column(Float, default=0.0, nullable=False)
    year = Column(Integer, nullable=True)
    genre = Column(String(500), nullable=True)
    rating = Column(Float, nullable=True)
    synopsis = Column(Text, nullable=True)
    seasons = Column(Integer, nullable=True)
    tmdb_id = Column(Integer, nullable=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
