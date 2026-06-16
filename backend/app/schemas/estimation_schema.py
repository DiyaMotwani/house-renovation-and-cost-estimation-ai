from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EstimationOverrideSchema(BaseModel):
    zone_id: UUID
    custom_unit_price_inr: float | None = None
    custom_labour_rate_inr: float | None = None


class RecalculateEstimationSchema(BaseModel):
    overrides: list[EstimationOverrideSchema] = []


class EstimationItemSchema(BaseModel):
    id: UUID
    project_id: UUID
    zone_id: UUID
    material_id: str
    area_sqft: float
    qty_required: float
    unit: str
    material_cost_inr: float
    labour_cost_inr: float
    total_cost_inr: float
    estimated_days: float
    custom_unit_price_inr: float | None
    custom_labour_rate_inr: float | None
    dimension_anchor_used: str | None = None
    dimension_confidence: float | None = None
    dimension_reasoning: str | None = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class EstimationSummarySchema(BaseModel):
    items: list[EstimationItemSchema]
    grand_total_inr: float
    total_days: float
