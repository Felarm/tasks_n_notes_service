import asyncio
import signal

from loguru import logger

from database import async_session_maker
from events.broker import kafka_broker
from events.models.outbox_cleaner import outbox_cleaner
from events.models.outbox_kafka_relay import outbox_relay_worker


async def main():
    logger.info("workers initializing")
    await kafka_broker.connect()
    relay_task = asyncio.create_task(outbox_relay_worker(async_session_maker))
    cleaner_task = asyncio.create_task(outbox_cleaner(async_session_maker))
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    def _shutdown_handler():
        logger.info("shutting down workers")
        stop_event.set()
    for sig in (signal.SIGTERM,signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown_handler)
    await stop_event.wait()
    relay_task.cancel()
    cleaner_task.cancel()
    await asyncio.gather(relay_task, cleaner_task, return_exceptions=True)
    await kafka_broker.stop()
    logger.info("workers stopped")


if __name__ == "__main__":
    asyncio.run(main())
