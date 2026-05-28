from faststream.kafka import KafkaBroker

from config import settings


broker = KafkaBroker(
    bootstrap_servers=settings.KAFKA_URL,
    client_id=settings.CLIENT_ID,
    acks="all",
    retry_backoff_ms=500,
    enable_idempotence=True,
)


task_events_publisher = broker.publisher("task_events")
note_events_publisher = broker.publisher("note_events")