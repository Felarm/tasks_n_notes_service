from typing import Annotated, Optional

from fastapi import APIRouter, status, Depends
from fastapi.params import Query

from dependencies import get_user_data, get_task_service
from tasks.schemas import TaskModel, TaskDateTimeFilter, TaskCreate, TaskUpdate
from tokens.schemas import AccessTokenPayload
from tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
JWTUserData = Annotated[AccessTokenPayload, Depends(get_user_data)]
TaskService_ = Annotated[TaskService, Depends(get_task_service)]


@router.get("/", response_model=list[TaskModel], status_code=status.HTTP_200_OK)
async def get_user_tasks(
        user_data: JWTUserData,
        task_service: TaskService_,
        filter_params: Optional[Annotated[TaskDateTimeFilter, Query()]] = None,
):
    return await task_service.get_user_tasks(int(user_data.sub), filter_params)


@router.post("/", response_model=TaskModel, status_code=status.HTTP_201_CREATED)
async def create_user_task(
        user_data: JWTUserData,
        task_service: TaskService_,
        new_task_data: TaskCreate,
):
    new_task = await task_service.create_user_task(user_data, new_task_data)
    return new_task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_user_task(user_data: JWTUserData, task_service: TaskService_, task_id: int):
    return await task_service.delete_task(user_data, task_id)


@router.patch("/{task_id}", status_code=status.HTTP_200_OK)
async def update_user_task(user_data: JWTUserData, task_service: TaskService_, task_id: int, update_data: TaskUpdate):
    await task_service.update_task(user_data, task_id, update_data)

