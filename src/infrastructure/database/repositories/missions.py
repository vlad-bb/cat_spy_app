from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from fastapi import HTTPException, status
from uuid import UUID

from src.infrastructure.database.models.tables import Mission, Target, Cat, mission_cats
from src.domain.entities.mission import MissionStatus, Mission as MissionEntity
from src.presentation.schemas.missions import MissionCreate

class MissionRepository:
    """Repository for managing Mission entities in the database."""
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, body: MissionCreate) -> Mission:
        """Create mission with targets and optional cat assignments"""
        existing_mission = await self.get_by_name(body.name)
        if existing_mission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mission with this name {body.name} already exists."
            )
       # Assign cats if provided
        if body.cat_uuids:
            mission_status = MissionStatus.IN_PROGRESS.value
            result = await self.db.execute(
                select(Cat).where(Cat.uuid.in_(body.cat_uuids))
            )
            cats = result.scalars().all()

            if len(cats) != len(body.cat_uuids):
                found_uuids = {cat.uuid for cat in cats}
                missing_uuids = set(body.cat_uuids) - found_uuids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cats not found: {missing_uuids}"
                )
            # Check if any cat is already assigned to a mission
            cats_with_missions = [] #TODO add missions status check (must be in_progress)
            for cat in cats:
                # Check if cat has any missions assigned
                mission_check = await self.db.execute(
                    select(mission_cats).where(mission_cats.c.cat_uuid == cat.uuid)
                )
                if mission_check.first():
                    cats_with_missions.append(cat.uuid)

            if cats_with_missions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cats with UUID {cats_with_missions[0]} are already assigned to missions. Each cat can only have one mission."
                )
        # Create mission with targets relationship
        mission = Mission(
            name=body.name,
            description=body.description,
            status=mission_status if body.cat_uuids else MissionStatus.PENDING.value,
            mission_target=[
                Target(
                    name=target.name,
                    country=target.country
                )
                for target in body.targets
            ]
        )
        
        # Assign cats after validation
        if body.cat_uuids:
            mission.cat.extend(cats)
        
        self.db.add(mission)
        await self.db.flush()
        mission_uuid = mission.uuid  # Access UUID after flush
        await self.db.commit()

        result = await self.db.execute(
        select(Mission)
        .where(Mission.uuid == mission_uuid)
        .options(selectinload(Mission.mission_target))
        .options(selectinload(Mission.cat))
    )
        return result.scalar_one()

    async def get_by_uuid(self, mission_uuid: UUID) -> Optional[Mission]:
        """Get mission by uuid with all relationships loaded"""
        result = await self.db.execute(
            select(Mission)
            .where(Mission.uuid == mission_uuid)
            .options(selectinload(Mission.mission_target))
            .options(selectinload(Mission.cat))
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Mission]:
        """Check if mission with this name already exists"""
        result = await self.db.execute(
            select(Mission).where(Mission.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_missions(self) -> List[Mission]:
        """Get all missions with relationships loaded"""
        result = await self.db.execute(
            select(Mission)
            .options(selectinload(Mission.mission_target))
            .options(selectinload(Mission.cat))
        )
        return result.scalars().all()

    async def delete_mission_by_uuid(self, mission_uuid: UUID) -> None:
        mission = await self.get_by_uuid(mission_uuid)
        if not mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mission not found"
            )
        if mission.cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete mission assigned to cats"
            )
        await self.db.delete(mission)
        await self.db.commit()

    async def set_completed_mission(self, mission_uuid: UUID) -> Mission:
        mission = await self.get_by_uuid(mission_uuid)
        if not mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mission not found"
            )
        domain_mission = MissionEntity(
            uuid=mission.uuid,
            name=mission.name,
            description=mission.description,
            status=mission.status,
            created_at=mission.created_at,
            updated_at=mission.updated_at,
            completed_at=mission.completed_at,
            cat_uuids=[cat.uuid for cat in mission.cat]
        )
        domain_mission.complete()
        mission.status = domain_mission.status
        mission.updated_at = domain_mission.updated_at
        mission.completed_at = domain_mission.completed_at
        await self.db.commit()
        return await self.get_by_uuid(mission_uuid)


    async def assign_cats_to_mission(self, mission_uuid: UUID, cat_uuids: List[UUID]) -> Mission:
        mission = await self.get_by_uuid(mission_uuid)
        if not mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mission not found"
            )

        if mission.status in [MissionStatus.COMPLETED.value, MissionStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assign cats to a {mission.status} mission"
            )

        result = await self.db.execute(
            select(Cat).where(Cat.uuid.in_(cat_uuids))
        )
        cats = result.scalars().all()
        
        if len(cats) != len(cat_uuids):
            found_uuids = {cat.uuid for cat in cats}
            missing_uuids = set(cat_uuids) - found_uuids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cats not found: {missing_uuids}"
            )

        # Check if any cat is already assigned to a mission
        cats_with_missions = [] #TODO add missions status check (must be in_progress)
        for cat in cats:
            # Check if cat has any missions assigned
            mission_check = await self.db.execute(
                select(mission_cats).where(mission_cats.c.cat_uuid == cat.uuid)
            )
            if mission_check.first():
                cats_with_missions.append(cat.uuid)

        if cats_with_missions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cats with UUID {cats_with_missions[0]} are already assigned to missions. Each cat can only have one mission."
            )             
        
        mission.cat.extend(cats)
        mission.status = MissionStatus.IN_PROGRESS.value
        await self.db.commit()
        return await self.get_by_uuid(mission_uuid)

    async def set_completed_target(self, target_uuid: UUID) -> Target:
        result = await self.db.execute(
            select(Target).where(Target.uuid == target_uuid)
        )
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        target.is_completed = True
        await self.db.commit()
        await self.db.refresh(target)
        return target
