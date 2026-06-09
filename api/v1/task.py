from typing import Annotated, Optional

from fastapi import APIRouter, status, Depends
from fastapi.params import Query

from dependencies import get_user_data, get_task_service
from schemas.task import TaskModelResponse, TaskDateTimeFilter, TaskCreate
from schemas.token import AccessTokenPayload
from services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
JWTUserData = Annotated[AccessTokenPayload, Depends(get_user_data)]
TaskService_ = Annotated[TaskService, Depends(get_task_service)]


@router.get("/", response_model=list[TaskModelResponse], status_code=status.HTTP_200_OK)
async def get_user_tasks(
        user_data: JWTUserData,
        task_service: TaskService_,
        filter_params: Optional[Annotated[TaskDateTimeFilter, Query()]] = None,
):
    return await task_service.get_user_tasks(int(user_data.sub), filter_params)


@router.post("/", response_model=TaskModelResponse, status_code=status.HTTP_201_CREATED)
async def create_user_task(
        user_data: JWTUserData,
        task_service: TaskService_,
        new_task_data: TaskCreate,
):
    new_task = await task_service.create_user_task(user_data, new_task_data)
    return new_task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_user_task(_: JWTUserData, task_service: TaskService_, task_id: int):
    return await task_service.delete_task(task_id)
