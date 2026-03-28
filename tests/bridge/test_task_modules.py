"""Tests for task management modules"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from apflow.bridge.task_modules import (
    TaskCreateModule,
    TaskDeleteModule,
    TaskExecuteModule,
    TaskGetModule,
    TaskListModule,
)


def _mock_task(task_id="abc-123", name="test_task", status="pending"):
    task = MagicMock()
    task.id = task_id
    task.name = name
    task.status = status
    task.created_at = MagicMock(isoformat=MagicMock(return_value="2026-01-01T00:00:00"))
    task.to_dict.return_value = {"id": task_id, "name": name, "status": status}
    return task


def _mock_repo(tasks=None, task=None):
    """Create a mock async repo with correct method names."""
    repo = MagicMock()
    repo.query_tasks = AsyncMock(return_value=tasks or [])
    repo.get_task_by_id = AsyncMock(return_value=task)
    repo.delete_task = AsyncMock(return_value=True)
    return repo


class TestTaskCreateModule:
    @pytest.mark.asyncio
    async def test_create_valid(self):
        creator = MagicMock()
        creator.create_task_trees_from_array = AsyncMock(return_value=[_mock_task()])
        repo = _mock_repo()

        module = TaskCreateModule(creator, repo)
        result = await module.execute({"name": "test_task"})
        assert result["id"] == "abc-123"
        assert result["name"] == "test_task"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_empty_name_raises(self):
        module = TaskCreateModule(MagicMock(), MagicMock())
        with pytest.raises(ValueError, match="non-empty"):
            await module.execute({"name": ""})

    @pytest.mark.asyncio
    async def test_create_missing_name_raises(self):
        module = TaskCreateModule(MagicMock(), MagicMock())
        with pytest.raises(ValueError, match="non-empty"):
            await module.execute({})


class TestTaskExecuteModule:
    @pytest.mark.asyncio
    async def test_execute_valid(self):
        manager = MagicMock()
        manager.execute_task = AsyncMock(return_value={"task_id": "abc", "status": "completed"})

        module = TaskExecuteModule(manager)
        result = await module.execute({"task_id": "abc"})
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_empty_id_raises(self):
        module = TaskExecuteModule(MagicMock())
        with pytest.raises(ValueError):
            await module.execute({"task_id": ""})


class TestTaskListModule:
    @pytest.mark.asyncio
    async def test_list_defaults(self):
        repo = _mock_repo(tasks=[_mock_task()])

        module = TaskListModule(repo)
        result = await module.execute({})
        assert "tasks" in result
        assert "total" in result
        assert result["total"] == 1
        repo.query_tasks.assert_called_once_with(user_id=None, status=None, limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_list_clamps_limit(self):
        repo = _mock_repo()
        module = TaskListModule(repo)

        await module.execute({"limit": 0})
        repo.query_tasks.assert_called_with(user_id=None, status=None, limit=1, offset=0)

        await module.execute({"limit": 5000})
        repo.query_tasks.assert_called_with(user_id=None, status=None, limit=1000, offset=0)


class TestTaskGetModule:
    @pytest.mark.asyncio
    async def test_get_valid(self):
        repo = _mock_repo(task=_mock_task())

        module = TaskGetModule(repo)
        result = await module.execute({"task_id": "abc-123"})
        assert result["id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        repo = _mock_repo(task=None)

        module = TaskGetModule(repo)
        with pytest.raises(KeyError, match="not found"):
            await module.execute({"task_id": "nonexistent"})

    @pytest.mark.asyncio
    async def test_get_empty_id_raises(self):
        module = TaskGetModule(MagicMock())
        with pytest.raises(ValueError):
            await module.execute({"task_id": ""})


class TestTaskDeleteModule:
    @pytest.mark.asyncio
    async def test_delete_valid(self):
        repo = _mock_repo(task=_mock_task())

        module = TaskDeleteModule(repo)
        result = await module.execute({"task_id": "abc-123"})
        assert result["deleted"] is True
        repo.delete_task.assert_called_once_with("abc-123")

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        repo = _mock_repo(task=None)

        module = TaskDeleteModule(repo)
        with pytest.raises(KeyError, match="not found"):
            await module.execute({"task_id": "nonexistent"})
