import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from database import TaskAndNoteBase


class TaskState(enum.Enum):
    created = "created"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"


class Task(TaskAndNoteBase):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("start_dt < end_dt", name="task_period"),
    )

    start_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[TaskState] = mapped_column(Enum(TaskState), default=TaskState.created, nullable=False)
    real_start_dt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    real_end_dt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
