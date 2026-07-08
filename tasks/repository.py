from datetime import datetime, UTC
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.models import Task


class TaskRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_task(
            self,
            user_id: int,
            name: str,
            start_dt: datetime,
            end_dt: datetime,
            description: str | None = None,
            assignee_id: int | None = None,
    ) -> Task:
        new_task = Task(
            user_id=user_id,
            name=name,
            start_dt=start_dt.astimezone(UTC),
            end_dt=end_dt.astimezone(UTC),
            description=description,
            assignee_id = assignee_id or user_id,
        )
        self.db.add(new_task)
        await self.db.flush()
        return new_task

    async def get_task_by_id(self, id_: int) -> Optional[Task]:
        res = await self.db.execute(select(Task).where(Task.id == id_))
        return res.scalar_one_or_none()

    async def get_all_user_tasks(self, user_id: int) -> Sequence[Task]:
        res = await self.db.execute(select(Task).where(Task.user_id == user_id))
        return res.scalars().all()

    async def get_user_tasks_for_period(self, user_id: int, p_start: datetime, p_end: datetime) -> Sequence[Task]:
        q = select(Task).where(Task.user_id == user_id).where(Task.start_dt <= p_end).where(Task.end_dt >= p_start)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def delete_task(self, task: Task) -> None:
        await self.db.delete(task)

    def update_task(self, task: Task, update_data: dict[str, str | datetime]):
        for k, v in update_data.items():
            if not hasattr(task, k):
                continue
            if isinstance(v, datetime) and v.tzinfo is None:
                v = v.astimezone(UTC)
            setattr(task, k, v)
        self.db.add(task)

    async def get_tasks_by_params(self, get_params: dict) -> Sequence[Task]:
        q = select(Task)
        for k, v in get_params.items():
            if not hasattr(Task, k):
                continue
            q = q.where(getattr(Task, k) == v)
        res = await self.db.execute(q)
        return res.scalars().all()
