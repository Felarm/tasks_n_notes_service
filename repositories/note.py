from datetime import datetime, UTC
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.note import Note


class NoteRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_note(
            self,
            user_id: int,
            name: str,
            remind_at: datetime,
            description: str | None = None,
    ) -> Note:
        new_note = Note(
            user_id=user_id,
            name=name,
            remind_at=remind_at.astimezone(UTC),
            description=description,
        )
        self.db.add(new_note)
        await self.db.flush()
        return new_note

    async def get_note_by_id(self, id_: int) -> Optional[Note]:
        res = await self.db.execute(select(Note).where(Note.id == id_))
        return res.scalar_one_or_none()

    async def get_all_user_notes(self, user_id: int) -> Sequence[Note]:
        res = await self.db.execute(select(Note).where(Note.user_id == user_id))
        return res.scalars().all()

    async def get_user_notes_for_period(self, user_id: int, p_start: datetime, p_end: datetime) -> Sequence[Note]:
        q = select(Note).where(Note.user_id == user_id).where(Note.remind_at.between(p_start, p_end))
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_user_expired_notes(self, user_id: int) -> Sequence[Note]:
        q = select(Note).where(Note.user_id == user_id).where(Note.remind_at < datetime.now(UTC))
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_user_upcoming_notes(self, user_id: int) -> Sequence[Note]:
        q = select(Note).where(Note.user_id == user_id).where(Note.remind_at >= datetime.now(UTC))
        res = await self.db.execute(q)
        return res.scalars().all()

    async def delete_note(self, note: Note) -> None:
        await self.db.delete(note)
