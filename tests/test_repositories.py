from datetime import datetime, timedelta, UTC

import pytest
from sqlalchemy.exc import IntegrityError, DBAPIError

from tasks.models import TaskState


class TestTaskRepository:
    @pytest.mark.asyncio
    async def test_create_task(self, tasks_repo):
        new_task = await tasks_repo.create_task(
            user_id=1,
            name="test_task",
            start_dt=datetime.now(),
            end_dt=datetime.now() + timedelta(minutes=5),
            description="test_description",
        )
        assert new_task.id is not None

    @pytest.mark.asyncio
    async def test_create_task_fails(self, tasks_repo):
        with pytest.raises(IntegrityError):
            await tasks_repo.create_task(
                user_id=1,
                name="test_task",
                start_dt=datetime.now() + timedelta(minutes=5),
                end_dt=datetime.now(),
            )

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, tasks_repo, test_tasks):
        for task in test_tasks:
            task_from_db = await tasks_repo.get_task_by_id(id_=task.id)
            assert task_from_db == task
        none_res = await tasks_repo.get_task_by_id(9999)
        assert none_res is None

    @pytest.mark.asyncio
    async def test_get_user_tasks(self, tasks_repo, test_tasks):
        user_tasks = await tasks_repo.get_all_user_tasks(user_id=1)
        for task in user_tasks:
            assert task in test_tasks
        empty_res = await tasks_repo.get_all_user_tasks(user_id=9999)
        assert len(empty_res) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_period", [(0, 5), (10, 15), (30, 45)])
    async def test_get_user_tasks_for_period(
            self, tasks_repo, test_tasks, test_period: tuple[int, int]
    ):
        curr_user_tasks = await tasks_repo.get_user_tasks_for_period(
            user_id=1,
            p_start=datetime.now() + timedelta(minutes=test_period[0]),
            p_end=datetime.now() + timedelta(minutes=test_period[1]),
        )
        assert len(curr_user_tasks) == 1

    @pytest.mark.asyncio
    async def test_delete_task(self, tasks_repo, test_tasks):
        await tasks_repo.delete_task(test_tasks[0])
        # await tasks_repo.db.commit()
        user_tasks = await tasks_repo.get_all_user_tasks(user_id=1)
        assert len(user_tasks) == 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="test_update_data",
        argvalues=[
            {"name": "updated_test"},
            {"name": "updated_test", "description": "updated_description"},
            {"start_dt": datetime.now(), "end_dt": datetime.now() + timedelta(minutes=5)},
            {"assignee_id": 9999},
            {"state": TaskState.done}
        ]
    )
    async def test_update_task_success(
            self, tasks_repo, test_tasks, test_update_data: dict[str, str | datetime]
    ):
        tasks_repo.update_task(test_tasks[0], test_update_data)
        await tasks_repo.db.commit()
        await tasks_repo.db.refresh(test_tasks[0])
        for k, v in test_update_data.items():
            if isinstance(v, datetime):
                v = v.astimezone(UTC)
            assert getattr(test_tasks[0], k) == v

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="test_update_data",
        argvalues=[
            {"start_dt": datetime.now(UTC) + timedelta(minutes=5), "end_dt": datetime.now(UTC)},
            {"assignee_id": "9999"},
            {"start_dt": datetime.now() + timedelta(days=100)},
        ]
    )
    async def test_update_task_fail(
            self, tasks_repo, test_tasks, test_update_data: dict[str, datetime | str]
    ):
        tasks_repo.update_task(test_tasks[0], test_update_data)
        with pytest.raises((IntegrityError, DBAPIError)):
            await tasks_repo.db.commit()


class TestNoteRepository:
    @pytest.mark.asyncio
    async def test_create_note(self, notes_repo):
        new_task = await notes_repo.create_note(
            user_id=1,
            name="test_note",
            remind_at=datetime.now(),
            description="test_description",
        )
        assert new_task.id is not None

    @pytest.mark.asyncio
    async def test_get_note_by_id(self, notes_repo, test_notes):
        for note in test_notes:
            task_from_db = await notes_repo.get_note_by_id(id_=note.id)
            assert task_from_db == note
        none_res = await notes_repo.get_note_by_id(9999)
        assert none_res is None

    @pytest.mark.asyncio
    async def test_get_all_user_notes(self, notes_repo, test_notes):
        db_notes = await notes_repo.get_all_user_notes(user_id=1)
        for note in db_notes:
            assert note in test_notes
        empty_res = await notes_repo.get_all_user_notes(user_id=9999)
        assert len(empty_res) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_period", [(-20, -10), (-5, 5), (10, 20)])
    async def test_get_user_notes_for_period(
            self, notes_repo, test_notes, test_period: tuple[int, int]
    ):
        curr_user_tasks = await notes_repo.get_user_notes_for_period(
            user_id=1,
            p_start=datetime.now() + timedelta(minutes=test_period[0]),
            p_end=datetime.now() + timedelta(minutes=test_period[1]),
        )
        assert len(curr_user_tasks) == 1

    @pytest.mark.asyncio
    async def test_get_user_upcoming_notes(self, notes_repo, test_notes):
        upcoming_notes = await notes_repo.get_user_upcoming_notes(user_id=1)
        assert len(upcoming_notes) == 1

    @pytest.mark.asyncio
    async def test_get_user_expired_notes(self, notes_repo, test_notes):
        upcoming_notes = await notes_repo.get_user_expired_notes(user_id=1)
        assert len(upcoming_notes) == 2

    @pytest.mark.asyncio
    async def test_delete_note(self, notes_repo, test_notes):
        await notes_repo.delete_note(test_notes[0])
        await notes_repo.db.commit()
        user_notes = await notes_repo.get_all_user_notes(user_id=1)
        assert len(user_notes) == 2


class TestOutboxRepository:
    pass
