from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImageResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    image_type: str
    file_path: str
    mime_type: str
    file_size_kb: int | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ImageListResponseSchema(BaseModel):
    images: list[ImageResponseSchema]
