from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class TaskModel(BaseModel):
    id: Optional[str] = None
    task_name: str = Field(..., min_length=1)
    status: Literal["Backlog", "Not started", "In progress", "Paused", "Done"] = "Not started"
    domain: Literal["AIESEC", "Academics", "Clients", "Personal"]
    impact: int = Field(default=3, ge=1, le=5)
    urgency: int = Field(default=3, ge=1, le=5)
    estimated_hours: float = Field(default=1.0, ge=0.25, le=12.0)
    someone_waiting: bool = False
    state_anchor: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority_score: Optional[float] = 0.0

class AssetModel(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1)
    type: str = "Docs"
    domain: str = "all"
    url: Optional[str] = None
    tags: list[str] = []