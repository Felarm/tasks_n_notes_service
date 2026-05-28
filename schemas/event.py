from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseEvent(BaseModel):
    id: int
    user_id: int
    tg_id: Optional[int] = None
    username: str
    name: str


class BaseTaskEvent(BaseEvent):
    description: Optional[str] = None
    start_dt: datetime
    end_dt: datetime


class TaskCreateEvent(BaseTaskEvent):
    event_type: str = "create_task"


class BaseNoteEvent(BaseEvent):
    description: Optional[str] = None
    remind_at: datetime


class NoteCreateEvent(BaseNoteEvent):
    event_type: str = "create_note"