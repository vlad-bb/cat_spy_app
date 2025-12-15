from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from uuid import UUID

class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    
    @field_validator('content')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

class NoteResponse(BaseModel):
    uuid: UUID
    content: str
    target_uuid: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes = True)