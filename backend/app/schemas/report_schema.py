from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    file_path: str
    grand_total_inr: float
    total_days: float
    generated_at: datetime

    model_config = {"from_attributes": True}
