from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.engine import Base
import secrets


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, default=lambda: secrets.token_hex(32))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
