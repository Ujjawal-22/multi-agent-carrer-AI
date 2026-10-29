import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobDescriptionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Job description text cannot be blank.")
        return value


class JobDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    source: str
    char_count: int
    created_at: datetime
