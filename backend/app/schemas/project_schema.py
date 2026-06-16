from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateProjectSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class UpdateProjectSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ScaleAnchorSchema(BaseModel):
    user_front_width_ft: float = Field(..., gt=0)


class ProjectResponseSchema(BaseModel):
    id: UUID
    name: str
    status: str
    scale_factor: float
    user_front_width_ft: float | None
    approx_front_width_ft: float | None
    num_floors: int | None
    house_description: str | None = None
    renovation_needs: list[str] | None = None
    renovation_suggestions: list[str] | None = None
    style_hint: str | None = None
    dimension_hints: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ProjectListResponseSchema(BaseModel):
    projects: list[ProjectResponseSchema]
