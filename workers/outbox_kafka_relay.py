import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from config import settings
from kafka import task_events_publisher, note_events_publisher
from repositories.outbox import OutboxRepository


async def process_outbox_messages(outbox_repo: OutboxRepository) -> None:
    unprocessed_messages = await outbox_repo.get_unprocessed_messages(limit=100)
    if not unprocessed_messages:
        return
    for msg in unprocessed_messages:
        if msg.topic == settings.TASKS_TOPIC_NAME:
            await task_events_publisher.publish(
                message=msg.jsoned_payload,
                key=msg.key.encode() if msg.key else None,
            )
        elif msg.topic == settings.NOTES_TOPIC_NAME:
            await note_events_publisher.publish(
                message=msg.jsoned_payload,
                key=msg.key.encode() if msg.key else None,
            )
        else:
            continue
        await outbox_repo.set_processed(msg)
    await outbox_repo.db.commit()


async def outbox_relay_worker(session_maker: async_sessionmaker):
    logger.info("outbox kafka relay started")
    while True:
        try:
            async with session_maker() as db_session:
                outbox_repo = OutboxRepository(db_session)
                await process_outbox_messages(outbox_repo)
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.exception(f"Something went wrong\n{e}")
