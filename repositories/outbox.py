from datetime import datetime, UTC, timedelta
from typing import Optional, Sequence

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.outbox import OutboxMessage


class OutboxRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def create_message(self, topic: str, jsoned_payload: str, key: Optional[str] = None) -> OutboxMessage:
        new_msg = OutboxMessage(
            topic=topic,
            jsoned_payload=jsoned_payload,
            key=key,
        )
        self.db.add(new_msg)
        return new_msg

    async def get_unprocessed_messages(self, limit: Optional[int] = None) -> Sequence[OutboxMessage]:
        q = select(OutboxMessage).where(OutboxMessage.processed == False).order_by(OutboxMessage.created_at.asc())
        if limit is not None:
            q = q.limit(limit)
        q = q.with_for_update(skip_locked=True)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def delete_processed_messages(self, days_to_keep: int = 1) -> int:
        keep_time = datetime.now(UTC) - timedelta(days=days_to_keep)
        q = delete(OutboxMessage).where(
            OutboxMessage.processed == True,
            OutboxMessage.created_at < keep_time,
        )
        await self.db.execute(q)

    async def set_processed(self, msg: OutboxMessage) -> None:
        q = update(OutboxMessage).where(OutboxMessage.id == msg.id).values(processed=True)
        await self.db.execute(q)