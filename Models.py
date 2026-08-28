from pydantic import BaseModel, Field
from typing import Optional, Literal

TaskStatus = Literal["Backlog", "Not started", "In progress", "Paused", "Done"]
TaskDomain = Literal["AIESEC", "Academics", "Clients", "Personal"]

# --- Custom Exception Hierarchy ---
class SecondBrainError(Exception):
    """Base exception for Second Brain application errors."""
    pass

class NotionServiceError(SecondBrainError):
    """Raised when an external Notion API operation fails."""
    pass

class TaskValidationError(SecondBrainError):
    """Raised when task data fails domain or validation rules."""
    pass

class TaskLimitError(SecondBrainError):
    """Raised when the active task limit has been reached."""
    pass

class InvalidStateTransitionError(SecondBrainError):
    """Raised when an illegal task state transition is attempted."""
    pass


VALID_STATE_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    "Not started": {"In progress", "Backlog", "Done"},
    "In progress": {"Paused", "Done", "Not started"},
    "Paused": {"In progress", "Done", "Not started"},
    "Backlog": {"Not started", "Done", "In progress"},
    "Done": {"Not started", "Backlog", "In progress"},
}

class TaskModel(BaseModel):
    id: Optional[str] = None
    task_name: str = Field(..., min_length=1)
    status: TaskStatus = "Not started"
    domain: TaskDomain
    impact: int = Field(default=3, ge=1, le=5)
    urgency: int = Field(default=3, ge=1, le=5)
    estimated_hours: float = Field(default=1.0, ge=0.25, le=12.0)
    someone_waiting: bool = False
    state_anchor: Optional[str] = None
    priority_score: Optional[float] = 0.0

class AssetModel(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1)
    type: str = "Docs"
    domain: str = "all"
    url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)