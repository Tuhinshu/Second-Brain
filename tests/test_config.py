import os
import unittest

os.environ["NOTION_API_KEY"] = "dummy_key"
os.environ["NOTION_TASKS_DB_ID"] = "dummy_tasks_db"
os.environ["NOTION_ASSETS_DB_ID"] = "dummy_assets_db"

from config import _parse_max_active_tasks


class TestConfigValidation(unittest.TestCase):
    def test_default_fallback_on_empty(self):
        self.assertEqual(_parse_max_active_tasks(""), 50)
        self.assertEqual(_parse_max_active_tasks("   "), 50)
        self.assertEqual(_parse_max_active_tasks(None), 50)

    def test_valid_integer_parsing(self):
        self.assertEqual(_parse_max_active_tasks("25"), 25)
        self.assertEqual(_parse_max_active_tasks("100"), 100)

    def test_non_integer_raises_actionable_error(self):
        with self.assertRaises(ValueError) as ctx:
            _parse_max_active_tasks("fifty")
        self.assertIn("Invalid configuration for 'MAX_ACTIVE_TASKS'", str(ctx.exception))
        self.assertIn("Expected a positive integer between", str(ctx.exception))

    def test_out_of_bounds_raises_actionable_error(self):
        with self.assertRaises(ValueError) as ctx:
            _parse_max_active_tasks("0")
        self.assertIn("out of allowed bounds", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            _parse_max_active_tasks("9999")
        self.assertIn("out of allowed bounds", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
