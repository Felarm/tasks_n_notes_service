from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from exceptions import ResourceNotFoundException
from repositories.note import NoteRepository
from repositories.outbox import OutboxRepository
from schemas.event import NoteCreateEvent
from schemas.note import NoteModelResponse, NoteCreate
from schemas.token import AccessTokenPayload


class NoteService:
    def __init__(self, db_session: AsyncSession):
        self.note_repo = NoteRepository(db_session)
        self.outbox_repo = OutboxRepository(db_session)
        self.db_session = db_session

    async def get_all_user_notes(self, user_id: int) -> list[NoteModelResponse]:
        notes = await self.note_repo.get_all_user_notes(user_id)
        return [NoteModelResponse.model_validate(_) for _ in notes]

    async def create_user_note(self, user_data: AccessTokenPayload, new_note: NoteCreate) -> NoteModelResponse:
        async with self.db_session.begin():
            note = await self.note_repo.create_note(user_id=int(user_data.sub), **new_note.model_dump())
            event_payload = NoteCreateEvent(
                id=note.id,
                user_id=note.user_id,
                tg_id=user_data.tg_id,
                username=user_data.username,
                name=note.name,
                description=note.description,
                remind_at=note.remind_at,
            )
            self.outbox_repo.create_message(
                topic=settings.NOTES_TOPIC_NAME,
                jsoned_payload=event_payload.model_dump_json(),
            )
        return NoteModelResponse.model_validate(note)

    async def delete_user_note(self, note_id: int) -> None:
        note = await self.note_repo.get_note_by_id(note_id)
        if not note:
            raise ResourceNotFoundException(f"Note with {note_id=} not found")
        await self.note_repo.delete_note(note)
        await self.db_session.commit()
