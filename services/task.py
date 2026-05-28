from datetime import datetime, time, UTC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from exceptions import ResourceNotFoundException
from repositories.outbox import OutboxRepository
from repositories.task import TaskRepository
from schemas.event import TaskCreateEvent
from schemas.task import TaskDateTimeFilter, TaskModelResponse, TaskCreate
from schemas.token import AccessTokenPayload


class TaskService:
    def __init__(self, db_session: AsyncSession):
        self.task_repo = TaskRepository(db_session)
        self.outbox_repo = OutboxRepository(db_session)
        self.db_session = db_session

    async def get_user_tasks(self, user_id: int, filter_: Optional[TaskDateTimeFilter] = None) -> list[TaskModelResponse]:
        if filter_ and filter_.by_date:
            p_start = datetime.combine(filter_.by_date, time.min).astimezone(UTC)
            p_end = datetime.combine(filter_.by_date, time.max).astimezone(UTC)
            tasks = await self.task_repo.get_user_tasks_for_period(user_id, p_start, p_end)
        elif filter_ and (filter_.start_dt and filter_.end_dt):
            tasks = await self.task_repo.get_user_tasks_for_period(user_id, filter_.start_dt.astimezone(UTC), filter_.end_dt.astimezone(UTC))
        else:
            tasks = await self.task_repo.get_user_tasks(user_id)
        return [TaskModelResponse.model_validate(_) for _ in tasks]

    async def create_user_task(self, user_data: AccessTokenPayload, new_task: TaskCreate) -> TaskModelResponse:
        async with self.db_session.begin():
            task = await self.task_repo.create_task(user_id=int(user_data.sub), **new_task.model_dump())
            event_payload = TaskCreateEvent(
                id=task.id,
                user_id=task.user_id,
                tg_id=user_data.tg_id,
                username=user_data.username,
                name=task.name,
                description=task.description,
                start_dt=task.start_dt,
                end_dt=task.end_dt,
            )
            self.outbox_repo.create_message(
                topic=settings.TASKS_TOPIC_NAME,
                jsoned_payload=event_payload.model_dump_json(),
            )
        return TaskModelResponse.model_validate(task)

    async def delete_task(self, task_id: int) -> None:
        task = await self.task_repo.get_task_by_id(task_id)
        if not task:
            raise ResourceNotFoundException(f"Task with {task_id=} not found")
        await self.task_repo.delete_task(task)
        await self.db_session.commit()


