# domain/repositories/mission_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domain.entities.mission import Mission

class MissionRepository(ABC):
    """Repository interface for Mission aggregate"""
    
    @abstractmethod
    def save(self, mission: Mission) -> None:
        pass
    
    @abstractmethod
    def find_by_uuid(self, mission_uuid: UUID) -> Optional[Mission]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[Mission]:
        pass
    
    @abstractmethod
    def delete(self, mission_uuid: UUID) -> None:
        pass