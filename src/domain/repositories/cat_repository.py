# domain/repositories/cat_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domain.entities.cat import Cat

class CatRepository(ABC):
    """Repository interface for Cat aggregate"""
    
    @abstractmethod
    def save(self, cat: Cat) -> None:
        pass
    
    @abstractmethod
    def find_by_uuid(self, cat_uuid: UUID) -> Optional[Cat]:
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Cat]:
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> List[Cat]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[Cat]:
        pass
    
    @abstractmethod
    def delete(self, cat_uuid: UUID) -> None:
        pass