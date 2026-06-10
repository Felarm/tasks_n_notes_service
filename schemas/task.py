from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator, AwareDatetime


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_dt: datetime
    end_dt: datetime


class TaskModel(TaskCreate):
    id: int
    state: str
    user_id: int
    real_start_dt: Optional[datetime]
    real_end_dt: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskDateTimeFilter(BaseModel):
    by_date: Optional[date] = None
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_exclusive_groups(self) -> "TaskDateTimeFilter":
        has_date = self.by_date is not None
        has_dt_range = self.start_dt is not None or self.end_dt is not None
        if has_date and has_dt_range:
            raise ValueError("Either by_date or start_dt-end_dt period should be provided")
        if (self.start_dt is not None) != (self.end_dt is not None):
            raise ValueError("Both start_dt and end_dt should be provided")
        return self
