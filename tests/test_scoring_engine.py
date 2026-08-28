import unittest

from Models import TaskModel
from scoring_engine import calculate_priority_score, rank_tasks


class TestScoringEngine(unittest.TestCase):
    def test_calculate_priority_score_base(self):
        task = TaskModel(
            task_name="Standard Task",
            domain="Personal",
            impact=3,
            urgency=3,
            estimated_hours=2.0,
            someone_waiting=False,
        )
        # Score formula: (impact * 2.0) + urgency + (5.0 if waiting else 0) + (hours * 1.5)
        # (3 * 2.0) + 3.0 + 0.0 + (2.0 * 1.5) = 6.0 + 3.0 + 3.0 = 12.0
        score = calculate_priority_score(task)
        self.assertEqual(score, 12.0)

    def test_calculate_priority_score_with_blocker(self):
        task = TaskModel(
            task_name="Blocked Client Deliverable",
            domain="Clients",
            impact=5,
            urgency=5,
            estimated_hours=4.0,
            someone_waiting=True,
        )
        # (5 * 2) + 5 + 5.0 + (4.0 * 1.5) = 10 + 5 + 5 + 6.0 = 26.0
        score = calculate_priority_score(task)
        self.assertEqual(score, 26.0)

    def test_rank_tasks_in_progress_pinned_to_top(self):
        t1 = TaskModel(
            task_name="Low score task but In Progress",
            domain="Personal",
            status="In progress",
            impact=1,
            urgency=1,
            estimated_hours=1.0,
        )
        t2 = TaskModel(
            task_name="High score backlog task",
            domain="Clients",
            status="Not started",
            impact=5,
            urgency=5,
            estimated_hours=5.0,
            someone_waiting=True,
        )
        t3 = TaskModel(
            task_name="Medium score task",
            domain="AIESEC",
            status="Not started",
            impact=3,
            urgency=3,
            estimated_hours=2.0,
        )

        ranked = rank_tasks([t2, t3, t1])
        # t1 must be first because it is "In progress"
        self.assertEqual(ranked[0].task_name, "Low score task but In Progress")
        # t2 has higher score than t3, so t2 comes second
        self.assertEqual(ranked[1].task_name, "High score backlog task")
        self.assertEqual(ranked[2].task_name, "Medium score task")

    def test_rank_tasks_empty_list(self):
        ranked = rank_tasks([])
        self.assertEqual(ranked, [])


if __name__ == "__main__":
    unittest.main()
