from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class TaskStatusResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    celery_task_id: str
    task_type: str
    status: str
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class GenerationStatusResponseSchema(BaseModel):
    status: str
    task: TaskStatusResponseSchema | None = None
