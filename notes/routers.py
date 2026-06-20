from typing import Annotated

from fastapi import APIRouter, status, Depends

from dependencies import get_user_data, get_note_service
from notes.schemas import NoteModel, NoteCreate
from tokens.schemas import AccessTokenPayload
from notes.service import NoteService

router = APIRouter(prefix="/notes", tags=["Notes"])
JWTUserData = Annotated[AccessTokenPayload, Depends(get_user_data)]
NoteService_ = Annotated[NoteService, Depends(get_note_service)]


@router.get("/", response_model=list[NoteModel], status_code=status.HTTP_200_OK)
async def get_all_user_notes(user_data: JWTUserData, note_service: NoteService_):
    return await note_service.get_all_user_notes(int(user_data.sub))


@router.post("/", response_model=NoteModel, status_code=status.HTTP_201_CREATED)
async def create_user_note(user_data: JWTUserData, note_service: NoteService_, new_task_data: NoteCreate):
    return await note_service.create_user_note(user_data, new_task_data)


@router.delete("/{note_id}", status_code=status.HTTP_200_OK)
async def delete_user_note(_: JWTUserData, note_service: NoteService_, note_id: int):
    return await note_service.delete_user_note(note_id)
