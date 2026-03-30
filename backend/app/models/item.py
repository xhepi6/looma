from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.engine import Base
from app.models.label import item_labels

import enum


class ItemStatus(str, enum.Enum):
    TODO = "todo"
    DONE = "done"


class ItemPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrenceType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEKDAYS = "weekdays"
    CUSTOM = "custom"


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(Enum(ItemStatus), default=ItemStatus.TODO, nullable=False)
    priority = Column(Enum(ItemPriority), default=ItemPriority.MEDIUM, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    position = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_edited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Reminder tracking
    reminded_due_window = Column(String(20), nullable=True)
    reminded_at = Column(DateTime(timezone=True), nullable=True)

    # Labels (many-to-many via item_labels)
    labels = relationship("Label", secondary=item_labels, lazy="selectin")

    # Recurrence
    recurrence_type = Column(String(20), nullable=True)
    recurrence_days = Column(JSON, nullable=True)
