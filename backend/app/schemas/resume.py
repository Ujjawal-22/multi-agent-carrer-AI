import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    extraction_method: str
    char_count: int
    uploaded_at: datetime
