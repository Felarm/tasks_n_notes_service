import pytest
from faststream.kafka import TestKafkaBroker

from config import settings
from kafka import broker
from workers.outbox_kafka_relay import process_outbox_messages


@broker.subscriber(settings.TASKS_TOPIC_NAME)
async def tasks_subscriber() -> None:
    print("Yo from tasks_subscriber")


@broker.subscriber(settings.NOTES_TOPIC_NAME)
async def notes_subscriber() -> None:
    print("Yo from notes_subscriber")


@pytest.mark.asyncio
async def test_process_outbox_messages(outbox_repo, outbox_messages):
    async with TestKafkaBroker(broker) as test_broker:
        await process_outbox_messages(outbox_repo)
        tasks_subscriber.mock.assert_called_once_with("test_task_payload")
        notes_subscriber.mock.assert_called_once_with("test_note_payload")
    for message in outbox_messages:
        await outbox_repo.db.refresh(message)
        assert message.processed is True
