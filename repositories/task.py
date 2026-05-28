from datetime import datetime, UTC
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task, TaskState


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
    ) -> Task:
        new_task = Task(
            user_id=user_id,
            name=name,
            start_dt=start_dt.astimezone(UTC),
            end_dt=end_dt.astimezone(UTC),
            description=description,
        )
        self.db.add(new_task)
        await self.db.flush()
        return new_task

    async def get_task_by_id(self, id_: int) -> Optional[Task]:
        res = await self.db.execute(select(Task).where(Task.id == id_))
        return res.scalar_one_or_none()

    async def get_user_tasks(self, user_id: int) -> Sequence[Task]:
        res = await self.db.execute(select(Task).where(Task.user_id == user_id))
        return res.scalars().all()

    async def get_user_tasks_for_period(self, user_id: int, p_start: datetime, p_end: datetime) -> Sequence[Task]:
        q = select(Task).where(Task.user_id == user_id).where(Task.start_dt <= p_end).where(Task.end_dt >= p_start)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_user_tasks_by_state(self, user_id: int, state: TaskState) -> Sequence[Task]:
        res = await self.db.execute(select(Task).where(Task.user_id == user_id).where(Task.state == state))
        return res.scalars().all()

    async def delete_task(self, task: Task) -> None:
        await self.db.delete(task)

    def set_state(self, task: Task, state: TaskState) -> None:
        task.state = state
        self.db.add(task)
