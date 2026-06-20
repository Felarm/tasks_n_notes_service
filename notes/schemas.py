from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    remind_at: datetime


class NoteModel(NoteCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)