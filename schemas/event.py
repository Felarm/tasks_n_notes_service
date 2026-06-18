from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EventType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class BaseEvent(BaseModel):
    id: int
    user_id: int
    tg_id: Optional[int] = None
    username: str
    name: str
    event_type: str = EventType


class TaskEvent(BaseEvent):
    description: Optional[str] = None
    start_dt: datetime
    end_dt: datetime
    assignee_id: Optional[int] = None


class NoteEvent(BaseEvent):
    description: Optional[str] = None
    remind_at: datetime

