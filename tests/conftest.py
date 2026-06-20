from datetime import datetime, UTC, timedelta
from typing import Any, AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker

from config import settings
from database import Base
from dependencies import get_db_session
from main import app
from notes.models import Note
from events.models import OutboxMessage
from tasks.models import Task
from notes.repository import NoteRepository
from events.repository import OutboxRepository
from tasks.repository import TaskRepository
from tokens.schemas import AccessTokenPayload
from notes.service import NoteService
from tasks.service import TaskService


@pytest_asyncio.fixture(scope="function")
async def engine() -> AsyncGenerator[AsyncEngine, Any]:
    engine = create_async_engine(url=settings.test_db_url, echo=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, Any]:
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def tasks_repo(db_session) -> TaskRepository:
    return TaskRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def test_tasks(tasks_repo) -> list[Task]:
    res = list()
    for task_name, period in zip(
        ["test_task_1", "test_task_2", "test_task_3"],
        [(0, 5), (10, 15), (30, 45)],
    ):
        new_task = await tasks_repo.create_task(
            user_id=1,
            name=task_name,
            start_dt=datetime.now(UTC) + timedelta(minutes=period[0]),
            end_dt=datetime.now(UTC) + timedelta(minutes=period[1]),
        )
        res.append(new_task)
    await tasks_repo.db.commit()
    return res


@pytest.fixture(scope="function")
def notes_repo(db_session) -> NoteRepository:
    return NoteRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def test_notes(notes_repo) -> list[Note]:
    res = list()
    for note_name, remind_delta in zip(
        ["test_note_1", "test_note_2", "test_note_3"],
        [-15, 0, 15],
    ):
        new_note = await notes_repo.create_note(
            user_id=1,
            name=note_name,
            remind_at=datetime.now(UTC) + timedelta(minutes=remind_delta)
        )
        res.append(new_note)
    await notes_repo.db.commit()
    return res


@pytest.fixture(scope="function")
def tasks_service(db_session) -> TaskService:
    return TaskService(db_session)


@pytest.fixture(scope="function")
def notes_service(db_session) -> NoteService:
    return NoteService(db_session)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, Any]:
    async def _get_db_override():
        yield db_session
    app.dependency_overrides[get_db_session] = _get_db_override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def access_token_payload() -> AccessTokenPayload:
    return AccessTokenPayload(
        sub="1",
        username="test_user",
        tg_id=1111,
        exp=int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        iat=int(datetime.now(UTC).timestamp()),
        type="access",
        jti=str(uuid4()),
    )

@pytest.fixture(scope="function")
def access_token(access_token_payload) -> str:
    return jwt.encode(access_token_payload.model_dump(), settings.SECRET_KEY, settings.ALGORITHM)


@pytest.fixture(scope="function")
def auth_header(access_token) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.fixture(scope="function")
def outbox_repo(db_session) -> OutboxRepository:
    return OutboxRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def outbox_messages(outbox_repo) -> list[OutboxMessage]:
    res = list()
    for topic_name, jsoned_payload in zip(
        [settings.TASKS_TOPIC_NAME, settings.NOTES_TOPIC_NAME],
        ["test_task_payload", "test_note_payload"],
    ):
        new_msg = outbox_repo.create_message(topic_name, jsoned_payload)
        res.append(new_msg)
    await outbox_repo.db.commit()
    return res