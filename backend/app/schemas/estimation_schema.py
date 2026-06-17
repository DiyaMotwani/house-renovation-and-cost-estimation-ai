from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
    zone_label: str | None = None
    material_id: str
    material_name: str | None = None
    category: str | None = None
    area_sqft: float
    qty_required: float
    unit: str
    coverage_sqft_per_unit: float | None = None
    coats_required: float | None = None
    wastage_pct: float | None = None
    base_unit_price_inr: float | None = None
    applied_unit_price_inr: float | None = None
    unit_price_overridden: bool = False
    base_labour_rate_inr: float | None = None
    applied_labour_rate_inr: float | None = None
    labour_overridden: bool = False
    material_cost_inr: float
    labour_cost_inr: float
    total_cost_inr: float
    estimated_days: float
    custom_unit_price_inr: float | None = None
    custom_labour_rate_inr: float | None = None
    dimension_anchor_used: str | None = None
    dimension_confidence: float | None = None
    dimension_reasoning: str | None = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class EstimationSummarySchema(BaseModel):
    items: list[EstimationItemSchema]
    material_subtotal_inr: float = 0.0
    labour_subtotal_inr: float = 0.0
    grand_total_inr: float
    gst_pct: float = 0.0
    gst_amount_inr: float = 0.0
    total_payable_inr: float = 0.0
    total_days: float
