from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateVariantSchema(BaseModel):
    name: str | None = None
    copy_from_active: bool = True


class RenameVariantSchema(BaseModel):
    name: str


class VariantResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VariantComparisonItemSchema(BaseModel):
    variant: VariantResponseSchema
    generated_image_path: str | None = None
    grand_total_inr: float | None = None
    total_payable_inr: float | None = None
    total_days: float | None = None
