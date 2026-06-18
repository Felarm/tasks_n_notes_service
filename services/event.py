from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from repositories.outbox import OutboxRepository
from schemas.event import NoteEvent, TaskEvent, EventType
from schemas.note import NoteModel
from schemas.task import TaskModel
from schemas.token import AccessTokenPayload


class EventService:
    def __init__(self, db_session: AsyncSession):
        self.outbox_repo = OutboxRepository(db_session)

    def create_note_event(self, user_data: AccessTokenPayload, new_note: NoteModel):
        event_payload = NoteEvent(
            id=new_note.id,
            user_id=int(user_data.sub),
            tg_id=user_data.tg_id,
            username=user_data.username,
            name=new_note.name,
            description=new_note.description,
            remind_at=new_note.remind_at,
            event_type=EventType.CREATE,
        )
        self.outbox_repo.create_message(
            topic=settings.NOTES_TOPIC_NAME,
            jsoned_payload=event_payload.model_dump_json(),
        )

    def create_task_event(self, user_data: AccessTokenPayload, new_task: TaskModel):
        event_payload = TaskEvent(
            id=new_task.id,
            user_id=int(user_data.sub),
            tg_id=user_data.tg_id,
            username=user_data.username,
            name=new_task.name,
            description=new_task.description,
            start_dt=new_task.start_dt,
            end_dt=new_task.end_dt,
            event_type=EventType.CREATE,
            assignee_id=new_task.assignee_id,
        )
        self.outbox_repo.create_message(
            topic=settings.TASKS_TOPIC_NAME,
            jsoned_payload=event_payload.model_dump_json(),
        )