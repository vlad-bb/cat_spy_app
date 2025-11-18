from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from src.presentation.schemas.targets import TargetCreate, TargetResponse

class MissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    targets: List[TargetCreate] = Field(..., min_length=1, max_length=3)
    cat_uuids: Optional[List[UUID]] = Field(default=None)
    
    @field_validator('name', 'description')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v
    
    @field_validator('targets')
    @classmethod
    def validate_targets_count(cls, v: List[TargetCreate]) -> List[TargetCreate]:
        if len(v) < 1 or len(v) > 3:
            raise ValueError('Mission must have between 1 and 3 targets')
        return v

class MissionResponse(BaseModel):
    uuid: UUID
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    targets: List[TargetResponse]
    cat_uuids: List[UUID]
    
    model_config = ConfigDict(from_attributes = True)

    @classmethod
    def from_mission(cls, mission):
        return cls(
            uuid=mission.uuid,
            name=mission.name,
            description=mission.description,
            created_at=mission.created_at,
            updated_at=mission.updated_at,
            status=mission.status,
            targets=[
                {
                    "uuid": target.uuid,
                    "name": target.name,
                    "country": target.country,
                    "status": target.status,
                    "mission_uuid": target.mission_uuid,
                    "created_at": target.created_at
                }
                for target in mission.mission_target
            ],
            cat_uuids=[cat.uuid for cat in mission.cat]
        )

class AssignCatsRequest(BaseModel):
    cat_uuids: list[UUID] = Field(..., min_length=1)
