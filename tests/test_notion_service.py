import unittest
from unittest.mock import MagicMock, patch
import os

os.environ["NOTION_API_KEY"] = "dummy_key"
os.environ["NOTION_TASKS_DB_ID"] = "dummy_tasks_db"
os.environ["NOTION_ASSETS_DB_ID"] = "dummy_assets_db"

import notion_service
from notion_service import (
    execute_with_retry,
    create_task,
    create_new_task,
    update_task_status,
    delete_task,
    inject_template_blocks_if_empty,
    fetch_active_tasks,
    fetch_assets,
)
from Models import TaskModel
from notion_client.errors import APIResponseError
import httpx


class TestNotionServiceMocked(unittest.TestCase):
    def test_execute_with_retry_recovers_on_429(self):
        attempts = 0

        def flaky_operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise APIResponseError(
                    code="rate_limited",
                    status=429,
                    message="Rate limited",
                    headers=httpx.Headers(),
                    raw_body_text="{}",
                )
            return "recovered_value"

        result = execute_with_retry(flaky_operation, max_retries=3, base_delay=0.01)
        self.assertEqual(result, "recovered_value")
        self.assertEqual(attempts, 2)

    def test_execute_with_retry_raises_non_retryable_error(self):
        def bad_request():
            raise APIResponseError(
                code="validation_error",
                status=400,
                message="Invalid payload",
                headers=httpx.Headers(),
                raw_body_text="{}",
            )

        with self.assertRaises(APIResponseError):
            execute_with_retry(bad_request, max_retries=2, base_delay=0.01)

    @patch("notion_service.notion")
    def test_create_task_calls_notion_pages_create(self, mock_notion):
        mock_notion.pages.create.return_value = {"id": "new-page-id-999"}
        task = TaskModel(
            task_name="Integrate Stripe",
            domain="Clients",
            impact=4,
            urgency=4,
            estimated_hours=3.0,
        )
        page_id = create_task(task)
        self.assertEqual(page_id, "new-page-id-999")
        mock_notion.pages.create.assert_called_once()

    @patch("notion_service.create_task")
    @patch("notion_service.fetch_active_tasks")
    def test_create_new_task_success(self, mock_fetch, mock_create):
        mock_fetch.return_value = []
        mock_create.return_value = "created-id"

        success, msg = create_new_task(
            task_name="New Feature",
            domain="Personal",
            impact=3,
            urgency=3,
            estimated_hours=1.0,
        )
        self.assertTrue(success)
        self.assertIn("successfully added", msg)

    @patch("notion_service.fetch_active_tasks")
    def test_create_new_task_empty_title_rejected(self, mock_fetch):
        success, msg = create_new_task(task_name="   ", domain="AIESEC")
        self.assertFalse(success)
        self.assertIn("provide a task title", msg)

    @patch("notion_service.fetch_active_tasks")
    def test_create_new_task_advisory_limit(self, mock_fetch):
        # Return 50 active tasks
        mock_fetch.return_value = [
            TaskModel(task_name=f"Task {i}", domain="Personal") for i in range(50)
        ]

        success, msg = create_new_task(task_name="Task 51", domain="Personal")
        self.assertFalse(success)
        self.assertIn("Active task limit reached", msg)

    @patch("notion_service.notion")
    def test_update_task_status(self, mock_notion):
        update_task_status("page-123", "In progress")
        mock_notion.pages.update.assert_called_with(
            page_id="page-123",
            properties={"Status": {"status": {"name": "In progress"}}},
        )

    @patch("notion_service.notion")
    def test_delete_task(self, mock_notion):
        delete_task("page-123")
        mock_notion.pages.update.assert_called_with(
            page_id="page-123",
            archived=True,
        )

    @patch("notion_service.notion")
    def test_inject_template_blocks_idempotent_when_empty(self, mock_notion):
        mock_notion.blocks.children.list.return_value = {"results": []}
        mock_notion.blocks.children.append.return_value = {"results": [{"id": "b1"}]}

        injected = inject_template_blocks_if_empty("empty-page")
        self.assertTrue(injected)
        mock_notion.blocks.children.append.assert_called_once()

    @patch("notion_service.notion")
    def test_inject_template_blocks_skips_when_marker_exists(self, mock_notion):
        mock_notion.blocks.children.list.return_value = {
            "results": [
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"plain_text": "Execution Scope & Checklist"}
                        ]
                    },
                }
            ]
        }

        injected = inject_template_blocks_if_empty("existing-page")
        self.assertFalse(injected)
        mock_notion.blocks.children.append.assert_not_called()


if __name__ == "__main__":
    unittest.main()
