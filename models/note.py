from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import TaskAndNoteBase


class Note(TaskAndNoteBase):
    __tablename__ = "notes"

    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)