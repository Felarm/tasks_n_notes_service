from datetime import datetime, timedelta, UTC, date
from typing import Optional

import pytest
from fastapi import status

from main import app
from schemas.note import NoteModelResponse, NoteCreate
from schemas.task import TaskCreate, TaskModelResponse, TaskDateTimeFilter
from tests.conftest import auth_header


class TestTaskApi:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="test_filter",
        argvalues=[
            TaskDateTimeFilter(by_date=date.today()),
            TaskDateTimeFilter(
                start_dt=datetime.now() + timedelta(minutes=-60),
                end_dt=datetime.now() + timedelta(minutes=60),
            ),
            None,
        ]
    )
    async def test_get_user_tasks(
            self, async_client, auth_header, test_filter: Optional[TaskDateTimeFilter], test_tasks
    ):
        response = await async_client.get(
            url=app.url_path_for("get_user_tasks"),
            params=test_filter.model_dump_json() if test_filter is not None else None,
            headers=auth_header,
        )
        assert response.status_code == status.HTTP_200_OK
        user_tasks = [TaskModelResponse.model_validate(_) for _ in response.json()]
        assert len(user_tasks) == len(test_tasks)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="url_paths_n_methods",
        argvalues=[
            ("get", app.url_path_for("get_user_tasks")),
            ("post", app.url_path_for("create_user_task")),
            ("delete", app.url_path_for("delete_user_task", task_id=9999))
        ]
    )
    async def test_unauthorized_exception(self, async_client, url_paths_n_methods):
        response = await async_client.__getattribute__(url_paths_n_methods[0])(
            url=url_paths_n_methods[1],
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_user_task(self, async_client, auth_header):
        request_data = TaskCreate(
            name="test_task",
            description="test_description",
            start_dt=datetime.now(),
            end_dt=datetime.now() + timedelta(minutes=5)
        )
        response = await async_client.post(
            url=app.url_path_for("create_user_task"),
            headers={"content-type": "application/json", **auth_header},
            content=request_data.model_dump_json(),
        )
        assert response.status_code == status.HTTP_201_CREATED
        created_task = TaskModelResponse.model_validate(response.json())
        assert created_task.user_id == 1
        assert created_task.name == request_data.name
        assert created_task.start_dt == request_data.start_dt.astimezone(UTC)
        assert created_task.end_dt == request_data.end_dt.astimezone(UTC)

    @pytest.mark.asyncio
    async def test_delete_user_task(self, async_client, test_tasks, auth_header):
        response = await async_client.delete(
            url=app.url_path_for(f"delete_user_task", task_id=test_tasks[0].id),
            headers=auth_header
        )
        assert response.status_code == status.HTTP_200_OK
        response = await async_client.delete(
            url=app.url_path_for("delete_user_task", task_id=99999),
            headers=auth_header
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestNoteApi:
    @pytest.mark.asyncio
    async def test_get_all_user_notes(self, async_client, auth_header, test_notes):
        response = await async_client.get(
            url=app.url_path_for("get_all_user_notes"),
            headers=auth_header,
        )
        assert response.status_code == status.HTTP_200_OK
        users_notes = [NoteModelResponse.model_validate(_) for _ in response.json()]
        assert len(users_notes) == len(test_notes)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="url_paths_n_methods",
        argvalues=[
            ("get", app.url_path_for("get_all_user_notes")),
            ("post", app.url_path_for("create_user_note")),
            ("delete", app.url_path_for("delete_user_note", note_id=9999))
        ]
    )
    async def test_unauthorized_exception(self, async_client, url_paths_n_methods):
        response = await async_client.__getattribute__(url_paths_n_methods[0])(
            url=url_paths_n_methods[1],
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_user_note(self, async_client, auth_header):
        request_data = NoteCreate(
            name="test_note",
            description="test_description",
            remind_at=datetime.now()
        )
        response = await async_client.post(
            url=app.url_path_for("create_user_note"),
            headers={"content-type": "application/json", **auth_header},
            content=request_data.model_dump_json()
        )
        assert response.status_code == status.HTTP_201_CREATED
        new_note = NoteModelResponse.model_validate(response.json())
        assert new_note.user_id == 1
        assert new_note.name == request_data.name
        assert new_note.description == request_data.description
        assert new_note.remind_at == request_data.remind_at.astimezone(UTC)

    @pytest.mark.asyncio
    async def test_delete_user_note(self, async_client, auth_header, test_notes):
        response = await async_client.delete(
            url=app.url_path_for("delete_user_note", note_id=test_notes[0].id),
            headers=auth_header,
        )
        assert response.status_code == status.HTTP_200_OK
        user_notes = await async_client.get(
            url=app.url_path_for("get_all_user_notes"),
            headers=auth_header,
        )
        assert len(user_notes.json()) < len(test_notes)
