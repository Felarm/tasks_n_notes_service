from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class OutboxMessage(Base):
    __tablename__ = "outbox"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    jsoned_payload: Mapped[str] = mapped_column(String, nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index(
            "idx_outbox_unprocessed",
            "created_at",
            postgresql_where=(processed == False),
        ),
    )