from datetime import date, datetime, timedelta, UTC
from typing import Optional

import pytest

from exceptions import ResourceNotFoundException
from events.schemas import TaskEvent, NoteEvent, EventType
from notes.schemas import NoteCreate, NoteUpdate
from tasks.schemas import TaskDateTimeFilter, TaskCreate, TaskUpdate
from tokens.schemas import AccessTokenPayload
from tokens.service import JWTService


class TestTaskService:
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
            self, tasks_service, test_tasks, test_filter: Optional[TaskDateTimeFilter]
    ):
        user_tasks = await tasks_service.get_user_tasks(
            user_id=1,
            filter_=test_filter,
        )
        assert len(user_tasks) == len(test_tasks)  # todo test at 0:00 for timezones

    @pytest.mark.asyncio
    async def test_create_user_task(self, tasks_service, access_token_payload, outbox_repo):
        task_start = datetime.now()
        task_end = datetime.now() + timedelta(minutes=30)
        new_task_data = TaskCreate(
            name="test_task",
            start_dt=task_start,
            end_dt=task_end,
        )
        new_task = await tasks_service.create_user_task(user_data=access_token_payload, new_task=new_task_data)
        assert new_task.start_dt == task_start.astimezone(UTC)
        assert new_task.end_dt == task_end.astimezone(UTC)
        assert new_task.user_id == 1
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 1
        msg_event = TaskEvent.model_validate_json(outbox_msgs[0].jsoned_payload)
        assert msg_event.id == new_task.id
        assert msg_event.start_dt == new_task.start_dt
        assert msg_event.end_dt == new_task.end_dt
        assert msg_event.user_id == 1
        assert msg_event.username == access_token_payload.username
        assert msg_event.event_type == EventType.CREATE

    @pytest.mark.asyncio
    async def test_delete_task(
            self,
            tasks_service,
            test_tasks,
            access_token_payload,
            outbox_repo
    ):
        await tasks_service.delete_task(access_token_payload, test_tasks[0].id)
        tasks_from_db = await tasks_service.get_user_tasks(user_id=1)
        assert len(tasks_from_db) < len(test_tasks)
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 1
        msg_event = TaskEvent.model_validate_json(outbox_msgs[0].jsoned_payload)
        assert msg_event.event_type == EventType.DELETE

    @pytest.mark.asyncio
    async def test_delete_task_exception(
            self,
            tasks_service,
            test_tasks,
            access_token_payload,
            outbox_repo
    ):
        with pytest.raises(ResourceNotFoundException):
            await tasks_service.delete_task(access_token_payload, 9999)
            outbox_msgs = await outbox_repo.get_unprocessed_messages()
            assert len(outbox_msgs) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="test_update_data",
        argvalues=[
            TaskUpdate(name="updated_name"),
            TaskUpdate(end_dt=datetime.now() + timedelta(days=100))
        ]
    )
    async def test_update_task(
            self,
            tasks_service,
            test_tasks,
            test_update_data: TaskUpdate,
            access_token_payload: AccessTokenPayload,
            outbox_repo,
    ):
        await tasks_service.update_task(access_token_payload, test_tasks[0].id, test_update_data)
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 1
        msg_event = TaskEvent.model_validate_json(outbox_msgs[0].jsoned_payload)
        assert msg_event.event_type == EventType.UPDATE

    @pytest.mark.asyncio
    async def test_update_task_exception(
            self,
            tasks_service,
            outbox_repo,
            access_token_payload,
    ):
        with pytest.raises(ResourceNotFoundException):
            await tasks_service.update_task(access_token_payload, 9999, TaskUpdate(name="fail update"))
            outbox_msgs = await outbox_repo.get_unprocessed_messages()
            assert len(outbox_msgs) == 0


class TestNoteService:
    @pytest.mark.asyncio
    async def test_get_user_notes(self, notes_service,test_notes):
        users_notes = await notes_service.get_all_user_notes(user_id=1)
        assert len(users_notes) == len(test_notes)
        for note_model, note_obj in zip(users_notes, test_notes):
            assert note_model.id == note_obj.id
            assert note_model.user_id == note_obj.user_id
            assert note_model.remind_at == note_obj.remind_at
            assert note_model.description == note_obj.description
        empty_res = await notes_service.get_all_user_notes(user_id=9999)
        assert len(empty_res) == 0

    @pytest.mark.asyncio
    async def test_create_user_note(self, notes_service, access_token_payload, outbox_repo):
        new_note_data = NoteCreate(
            name="test_note",
            description="test_description",
            remind_at=datetime.now() + timedelta(minutes=5)
        )
        await notes_service.create_user_note(user_data=access_token_payload, new_note=new_note_data)
        user_notes = await notes_service.get_all_user_notes(user_id=1)
        assert len(user_notes) == 1
        new_note = user_notes[0]
        assert new_note.user_id == 1
        assert new_note.name == new_note_data.name
        assert new_note.description == new_note_data.description
        assert new_note.remind_at == new_note_data.remind_at.astimezone(UTC)
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 1
        msg_payload = NoteEvent.model_validate_json(outbox_msgs[0].jsoned_payload)
        assert msg_payload.user_id == 1
        assert msg_payload.username == access_token_payload.username
        assert msg_payload.remind_at == new_note.remind_at
        assert msg_payload.event_type == EventType.CREATE

    @pytest.mark.asyncio
    async def test_delete_note(
            self,
            notes_service,
            test_notes,
            access_token_payload,
            outbox_repo,
    ):
        await notes_service.delete_user_note(access_token_payload, test_notes[0].id)
        notes_from_db = await notes_service.get_all_user_notes(user_id=1)
        assert len(notes_from_db) < len(test_notes)
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 1
        msg_payload = NoteEvent.model_validate_json(outbox_msgs[0].jsoned_payload)
        assert msg_payload.event_type == EventType.DELETE

    @pytest.mark.asyncio
    async def test_delete_note_exception(
            self,
            notes_service,
            test_notes,
            access_token_payload,
            outbox_repo
    ):
        with pytest.raises(ResourceNotFoundException):
            await notes_service.delete_user_note(access_token_payload, 9999)
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="test_update_data",
        argvalues=[
            NoteUpdate(name="updated_name", description="test_description"),
            NoteUpdate(remind_at=datetime.now() + timedelta(days=100))
        ]
    )
    async def test_update_note(
            self,
            notes_service,
            test_notes,
            test_update_data: NoteUpdate,
            access_token_payload: AccessTokenPayload,
            outbox_repo
    ):
        await notes_service.update_user_note(access_token_payload, test_notes[0].id, test_update_data)
        outbox_msgs = await outbox_repo.get_unprocessed_messages()
        assert len(outbox_msgs) == 1
        msg_payload = NoteEvent.model_validate_json(outbox_msgs[0].jsoned_payload)
        assert msg_payload.event_type == EventType.UPDATE

    @pytest.mark.asyncio
    async def test_update_note_exception(
            self,
            notes_service,
            test_notes,
            access_token_payload,
            outbox_repo):
        with pytest.raises(ResourceNotFoundException):
            await notes_service.update_user_note(access_token_payload, 9999, NoteUpdate(name="updated_name"))
            outbox_msgs = await outbox_repo.get_unprocessed_messages()
            assert len(outbox_msgs) == 0


class TestJWTService:
    def test_get_access_token_payload(self, access_token):
        access_token_payload = JWTService.get_access_token_payload(access_token)
        assert isinstance(access_token_payload, AccessTokenPayload)
        assert access_token_payload.sub == "1"
        assert access_token_payload.username == "test_user"
        assert access_token_payload.tg_id == 1111
        assert access_token_payload.exp <= int((datetime.now(UTC) + timedelta(minutes=15)).timestamp())
