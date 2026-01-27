from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.item import ItemStatus


class ItemCreate(BaseModel):
    title: str
    notes: Optional[str] = None
    due_at: Optional[datetime] = None
    labels: List[str] = Field(default_factory=list)


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[ItemStatus] = None
    due_at: Optional[datetime] = None
    position: Optional[float] = None
    labels: Optional[List[str]] = None


class ItemResponse(BaseModel):
    id: int
    board_id: int
    title: str
    notes: Optional[str] = None
    status: ItemStatus
    due_at: Optional[datetime] = None
    position: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_edited_by_user_id: Optional[int] = None
    labels: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
