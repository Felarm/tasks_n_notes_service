from sqlalchemy.ext.asyncio import AsyncSession

from events.schemas import EventType
from exceptions import ResourceNotFoundException
from notes.repository import NoteRepository
from notes.schemas import NoteModel, NoteCreate, NoteUpdate
from tokens.schemas import AccessTokenPayload
from events.service import EventService


class NoteService:
    def __init__(self, db_session: AsyncSession):
        self.note_repo = NoteRepository(db_session)
        self.event_service = EventService(db_session)
        self.db_session = db_session

    async def get_all_user_notes(self, user_id: int) -> list[NoteModel]:
        notes = await self.note_repo.get_all_user_notes(user_id)
        return [NoteModel.model_validate(_) for _ in notes]

    async def create_user_note(self, user_data: AccessTokenPayload, new_note: NoteCreate) -> NoteModel:
        async with self.db_session.begin():
            note = await self.note_repo.create_note(user_id=int(user_data.sub), **new_note.model_dump())
            note_response = NoteModel.model_validate(note)
            self.event_service.create_note_event(user_data, note_response, event_type=EventType.CREATE)
        return note_response

    async def delete_user_note(self, user_data: AccessTokenPayload, note_id: int) -> None:
        async with self.db_session.begin():
            note = await self.note_repo.get_note_by_id(note_id)
            if not note:
                raise ResourceNotFoundException(f"Note with {note_id=} not found")
            note_model = NoteModel.model_validate(note)
            self.event_service.create_note_event(user_data, note_model, event_type=EventType.DELETE)
            await self.note_repo.delete_note(note)

    async def update_user_note(self, user_data: AccessTokenPayload, note_id: int, update_data: NoteUpdate) -> None:
        async with self.db_session.begin():
            note = await self.note_repo.get_note_by_id(note_id)
            if not note:
                raise ResourceNotFoundException(f"Note with {note_id=} not found")
            note_model = NoteModel.model_validate(note)
            self.note_repo.update_note(note, note_model.model_dump(exclude_unset=True))
            self.event_service.create_note_event(user_data, note_model, event_type=EventType.UPDATE)