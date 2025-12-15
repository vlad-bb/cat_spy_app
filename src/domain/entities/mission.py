from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

class MissionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Mission:
    """Mission aggregate root"""
    uuid: UUID
    name: str
    description: str
    status: MissionStatus
    cat_uuids: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now())
    updated_at: datetime = field(default_factory=datetime.now())
    completed_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, name: str, description: str) -> 'Mission':
        """Factory method to create a new Mission"""
        return cls(
            uuid=uuid4(),
            name=name,
            description=description,
            status=MissionStatus.PENDING
        )
    
    def assign_cat(self, cat_uuid: UUID) -> None:
        """Assign a cat to the mission"""
        if cat_uuid not in self.cat_uuids:
            self.cat_uuids.append(cat_uuid)
            self.status = MissionStatus.IN_PROGRESS.value
            self.updated_at = datetime.now()

    def remove_cat(self, cat_uuid: UUID) -> None:
        """Remove a cat from the mission"""
        if cat_uuid in self.cat_uuids:
            self.cat_uuids.remove(cat_uuid)
            self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Mark mission as completed"""
        if self.status in [MissionStatus.PENDING.value, MissionStatus.CANCELLED.value]:
            raise ValueError(f"Cannot complete a {self.status} mission")
        self.status = MissionStatus.COMPLETED.value
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def can_be_assigned(self) -> bool:
        """Check if mission can have cats assigned"""
        return self.status in [MissionStatus.PENDING.value, MissionStatus.IN_PROGRESS.value]