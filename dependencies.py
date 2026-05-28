from typing import AsyncGenerator, Any, Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker
from schemas.token import AccessTokenPayload
from services.note import NoteService
from services.security import JWTService
from services.task import TaskService

jwt_bearer = HTTPBearer()


async def get_db_session() -> AsyncGenerator[AsyncSession | Any, Any]:
    async with async_session_maker() as session:
        yield session


async def get_user_data(token: Annotated[HTTPAuthorizationCredentials,Depends(jwt_bearer)]) -> AccessTokenPayload:
    payload = JWTService.get_access_token_payload(token.credentials)
    return payload


def get_task_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> TaskService:
    return TaskService(db)


def get_note_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> NoteService:
    return NoteService(db)

