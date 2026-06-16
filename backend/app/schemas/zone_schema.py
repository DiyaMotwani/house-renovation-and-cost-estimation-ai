from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UpdateZoneSchema(BaseModel):
    estimated_sqft: float = Field(..., gt=0)


class ZoneMaterialAssignmentSchema(BaseModel):
    zone_id: UUID
    material_id: str


class BulkAssignMaterialsSchema(BaseModel):
    assignments: list[ZoneMaterialAssignmentSchema]


class AssignMaterialSchema(BaseModel):
    material_id: str


class MaterialAssignmentResponseSchema(BaseModel):
    id: UUID
    zone_id: UUID
    material_id: str
    assigned_at: datetime

    model_config = {"from_attributes": True}


class ZoneResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    zone_key: str
    label: str
    description: str | None
    estimated_sqft: float | None
    box_2d: dict | None = None
    display_order: int
    created_at: datetime
    material_assignment: MaterialAssignmentResponseSchema | None = None

    model_config = {"from_attributes": True}


class ZoneListResponseSchema(BaseModel):
    zones: list[ZoneResponseSchema]
