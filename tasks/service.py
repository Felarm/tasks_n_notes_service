from datetime import datetime, time, UTC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from events.schemas import EventType
from exceptions import ResourceNotFoundException
from tasks.repository import TaskRepository
from tasks.schemas import TaskDateTimeFilter, TaskModel, TaskCreate, TaskUpdate
from tokens.schemas import AccessTokenPayload
from events.service import EventService


class TaskService:
    def __init__(self, db_session: AsyncSession):
        self.task_repo = TaskRepository(db_session)
        self.event_service = EventService(db_session)
        self.db_session = db_session

    async def get_user_tasks(self, user_id: int, filter_: Optional[TaskDateTimeFilter] = None) -> list[TaskModel]:
        if filter_ and filter_.by_date:
            p_start = datetime.combine(filter_.by_date, time.min).astimezone(UTC)
            p_end = datetime.combine(filter_.by_date, time.max).astimezone(UTC)
            tasks = await self.task_repo.get_user_tasks_for_period(user_id, p_start, p_end)
        elif filter_ and (filter_.start_dt and filter_.end_dt):
            tasks = await self.task_repo.get_user_tasks_for_period(user_id, filter_.start_dt.astimezone(UTC), filter_.end_dt.astimezone(UTC))
        else:
            tasks = await self.task_repo.get_all_user_tasks(user_id)
        return [TaskModel.model_validate(_) for _ in tasks]

    async def create_user_task(self, user_data: AccessTokenPayload, new_task: TaskCreate) -> TaskModel:
        async with self.db_session.begin():
            task = await self.task_repo.create_task(user_id=int(user_data.sub), **new_task.model_dump())
            task_response = TaskModel.model_validate(task)
            self.event_service.create_task_event(user_data, task_response, EventType.CREATE)
        return task_response

    async def delete_task(self, user_data: AccessTokenPayload, task_id: int) -> None:
        async with self.db_session.begin():
            task = await self.task_repo.get_task_by_id(task_id)
            if not task:
                raise ResourceNotFoundException(f"Task with {task_id=} not found")
            task_model = TaskModel.model_validate(task)
            self.event_service.create_task_event(user_data, task_model, EventType.DELETE)
            await self.task_repo.delete_task(task)

    async def update_task(self, user_data: AccessTokenPayload, task_id: int, update_data: TaskUpdate) -> None:
        async with self.db_session.begin():
            task = await self.task_repo.get_task_by_id(task_id)
            if not task:
                raise ResourceNotFoundException(f"Task with {task_id=} not found")
            task_model = TaskModel.model_validate(task)
            self.task_repo.update_task(task, update_data.model_dump(exclude_unset=True))
            self.event_service.create_task_event(user_data, task_model, EventType.UPDATE)
