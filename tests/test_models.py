import unittest
from pydantic import ValidationError
from Models import TaskModel, AssetModel, VALID_STATE_TRANSITIONS


class TestTaskModel(unittest.TestCase):
    def test_valid_task_creation(self):
        task = TaskModel(
            task_name="Write Unit Tests",
            domain="Personal",
            impact=4,
            urgency=5,
            estimated_hours=2.5,
            someone_waiting=True,
        )
        self.assertEqual(task.task_name, "Write Unit Tests")
        self.assertEqual(task.domain, "Personal")
        self.assertEqual(task.status, "Not started")
        self.assertEqual(task.impact, 4)
        self.assertEqual(task.urgency, 5)
        self.assertEqual(task.estimated_hours, 2.5)
        self.assertTrue(task.someone_waiting)
        self.assertIsNone(task.state_anchor)

    def test_task_impact_out_of_bounds(self):
        with self.assertRaises(ValidationError):
            TaskModel(task_name="Bad Impact", domain="AIESEC", impact=6)
        with self.assertRaises(ValidationError):
            TaskModel(task_name="Bad Impact Low", domain="AIESEC", impact=0)

    def test_task_urgency_out_of_bounds(self):
        with self.assertRaises(ValidationError):
            TaskModel(task_name="Bad Urgency", domain="Academics", urgency=10)

    def test_task_hours_out_of_bounds(self):
        with self.assertRaises(ValidationError):
            TaskModel(task_name="Too short", domain="Clients", estimated_hours=0.1)
        with self.assertRaises(ValidationError):
            TaskModel(task_name="Too long", domain="Clients", estimated_hours=15.0)

    def test_empty_task_name_rejected(self):
        with self.assertRaises(ValidationError):
            TaskModel(task_name="", domain="Personal")


class TestAssetModel(unittest.TestCase):
    def test_valid_asset_creation(self):
        asset = AssetModel(
            title="Q3 Strategy Playbook",
            type="Docs",
            domain="AIESEC",
            url="https://notion.so/playbook",
            tags=["strategy", "q3"],
        )
        self.assertEqual(asset.title, "Q3 Strategy Playbook")
        self.assertEqual(asset.type, "Docs")
        self.assertEqual(asset.domain, "AIESEC")
        self.assertEqual(len(asset.tags), 2)

    def test_empty_asset_title_rejected(self):
        with self.assertRaises(ValidationError):
            AssetModel(title="")


class TestStateTransitions(unittest.TestCase):
    def test_valid_transitions_map(self):
        self.assertIn("In progress", VALID_STATE_TRANSITIONS["Not started"])
        self.assertIn("Paused", VALID_STATE_TRANSITIONS["In progress"])
        self.assertIn("Done", VALID_STATE_TRANSITIONS["In progress"])
        self.assertIn("In progress", VALID_STATE_TRANSITIONS["Paused"])


if __name__ == "__main__":
    unittest.main()
