from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    new_password: str
    confirm_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
