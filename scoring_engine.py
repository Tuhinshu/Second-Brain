from Models import TaskModel


def calculate_priority_score(task: TaskModel) -> float:
    someone_waiting_score = 5.0 if task.someone_waiting else 0.0
    score = (task.impact * 2.0) + float(task.urgency) + someone_waiting_score + (task.estimated_hours * 1.5)
    return round(score, 2)


def rank_tasks(tasks: list[TaskModel]) -> list[TaskModel]:
    for task in tasks:
        task.priority_score = calculate_priority_score(task)
    in_progress = [t for t in tasks if t.status.lower() == "in progress"]
    remaining = [t for t in tasks if t.status.lower() != "in progress"]
    remaining_sorted = sorted(remaining, key=lambda t: t.priority_score or 0.0, reverse=True)
    return in_progress + remaining_sorted
