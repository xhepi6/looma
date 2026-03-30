from pydantic import BaseModel
from typing import Optional


class LabelResponse(BaseModel):
    id: int
    name: str
    color: str
    board_id: int

    model_config = {"from_attributes": True}


class LabelCreate(BaseModel):
    name: str
    color: Optional[str] = None


class LabelUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
