import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from repositories.outbox import OutboxRepository


async def outbox_cleaner(session_maker: async_sessionmaker):
    logger.info(f"outbox cleaner worker started")
    while True:
        try:
            await asyncio.sleep(60 * 60)
            async with session_maker() as db_session:
                outbox_repo = OutboxRepository(db_session)
                deleted_count = await outbox_repo.delete_processed_messages()
                await db_session.commit()
                if deleted_count > 0:
                    logger.info(f"deleted {deleted_count} old outbox messages")
        except Exception as e:
            logger.exception(f"something went wrong\n{e}")