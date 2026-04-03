from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageSend(BaseModel):
    content: str = Field(..., max_length=2000)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime
