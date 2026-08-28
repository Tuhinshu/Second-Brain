import unittest
import os

# Set dummy environment variables for configuration loading before import
os.environ["NOTION_API_KEY"] = "dummy_key"
os.environ["NOTION_TASKS_DB_ID"] = "dummy_tasks_db"
os.environ["NOTION_ASSETS_DB_ID"] = "dummy_assets_db"

from notion_service import (
    _extract_plain_text,
    _parse_int_prop,
    _parse_float_prop,
    parse_task_page,
    parse_asset_page,
)
from app import escape_markdown


class TestNotionParsing(unittest.TestCase):
    def test_extract_plain_text_normal(self):
        prop = {"title": [{"plain_text": "  Complete Architecture Docs  "}]}
        self.assertEqual(_extract_plain_text(prop, key="title"), "Complete Architecture Docs")

    def test_extract_plain_text_empty_and_malformed(self):
        self.assertEqual(_extract_plain_text(None), "")
        self.assertEqual(_extract_plain_text({}), "")
        self.assertEqual(_extract_plain_text({"title": []}), "")
        self.assertEqual(_extract_plain_text({"title": "not-a-list"}), "")

    def test_parse_int_prop_explicit_none_and_bounds(self):
        self.assertEqual(_parse_int_prop(None, default=3), 3)
        self.assertEqual(_parse_int_prop({}, default=3), 3)
        self.assertEqual(_parse_int_prop({"number": None}, default=3), 3)
        self.assertEqual(_parse_int_prop({"number": 4}), 4)
        self.assertEqual(_parse_int_prop({"number": 99}, min_val=1, max_val=5), 5)
        self.assertEqual(_parse_int_prop({"number": -10}, min_val=1, max_val=5), 1)
        self.assertEqual(_parse_int_prop({"number": "bad_string"}, default=3), 3)

    def test_parse_float_prop_explicit_none_and_bounds(self):
        self.assertEqual(_parse_float_prop(None, default=1.0), 1.0)
        self.assertEqual(_parse_float_prop({"number": None}, default=1.0), 1.0)
        self.assertEqual(_parse_float_prop({"number": 2.5}), 2.5)
        self.assertEqual(_parse_float_prop({"number": 25.0}, min_val=0.25, max_val=12.0), 12.0)
        self.assertEqual(_parse_float_prop({"number": 0.05}, min_val=0.25, max_val=12.0), 0.25)

    def test_parse_task_page_full(self):
        raw_page = {
            "id": "page-uuid-123",
            "properties": {
                "Task Name": {"title": [{"plain_text": "Draft Proposal"}]},
                "Status": {"status": {"name": "In progress"}},
                "Domain": {"select": {"name": "Clients"}},
                "Impact": {"number": 5},
                "Urgency": {"number": 4},
                "Estimated Hours": {"number": 3.5},
                "Someone Waiting?": {"checkbox": True},
                "State Anchor": {"rich_text": [{"plain_text": "Open section 3 and add pricing"}]},
            },
        }
        task = parse_task_page(raw_page)
        self.assertEqual(task.id, "page-uuid-123")
        self.assertEqual(task.task_name, "Draft Proposal")
        self.assertEqual(task.status, "In progress")
        self.assertEqual(task.domain, "Clients")
        self.assertEqual(task.impact, 5)
        self.assertEqual(task.urgency, 4)
        self.assertEqual(task.estimated_hours, 3.5)
        self.assertTrue(task.someone_waiting)
        self.assertEqual(task.state_anchor, "Open section 3 and add pricing")

    def test_parse_task_page_resilient_defaults(self):
        # Empty properties dict
        task = parse_task_page({"id": "empty-page", "properties": {}})
        self.assertEqual(task.task_name, "Untitled Task")
        self.assertEqual(task.status, "Not started")
        self.assertEqual(task.domain, "Personal")
        self.assertEqual(task.impact, 3)
        self.assertEqual(task.urgency, 3)
        self.assertEqual(task.estimated_hours, 1.0)
        self.assertFalse(task.someone_waiting)
        self.assertIsNone(task.state_anchor)

    def test_parse_asset_page(self):
        raw_asset = {
            "id": "asset-uuid-456",
            "properties": {
                "Title": {"title": [{"plain_text": "AIESEC Brand Guidelines"}]},
                "Type": {"select": {"name": "Brand"}},
                "Domain": {"select": {"name": "AIESEC"}},
                "URL": {"url": "https://brand.aiesec.org"},
                "Tags": {"multi_select": [{"name": "design"}, {"name": "guidelines"}]},
            },
        }
        asset = parse_asset_page(raw_asset)
        self.assertEqual(asset.id, "asset-uuid-456")
        self.assertEqual(asset.title, "AIESEC Brand Guidelines")
        self.assertEqual(asset.type, "Brand")
        self.assertEqual(asset.domain, "AIESEC")
        self.assertEqual(asset.url, "https://brand.aiesec.org")
        self.assertEqual(asset.tags, ["design", "guidelines"])

    def test_escape_markdown(self):
        self.assertEqual(escape_markdown("Hello *World*"), "Hello \\*World\\*")
        self.assertEqual(escape_markdown("[Link](url)"), "\\[Link\\]\\(url\\)")
        self.assertEqual(escape_markdown("# Heading"), "\\# Heading")
        self.assertEqual(escape_markdown(""), "")
        self.assertEqual(escape_markdown(None), "")


if __name__ == "__main__":
    unittest.main()
