from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from uuid import UUID

from src.domain.entities.target import TargetStatus
from src.domain.entities.mission import MissionStatus
from src.infrastructure.database.models.tables import Target, Mission, mission_cats, targets_cats, Cat


class TargetRepository:
    """Repository for managing Target entities in the database."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign_cat_to_target(self, target_uuid: UUID, cat_uuid: UUID) -> None:
        result = await self.db.execute(
            select(Target).where(Target.uuid == target_uuid)
        )
        target = result.scalar_one_or_none()

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
    
        # Define which statuses allow cat assignment
        ALLOWED_STATUSES_FOR_ASSIGNMENT = [
            TargetStatus.ACTIVE.value,
            TargetStatus.PENDING.value
        ]
        
        if target.status not in ALLOWED_STATUSES_FOR_ASSIGNMENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assign cat to target with status '{target.status}'. "
                    f"Target must be one of: {', '.join(ALLOWED_STATUSES_FOR_ASSIGNMENT)}"
            )
        
        # Assign cat to target
        await self.db.execute(
            targets_cats.insert().values(target_uuid=target_uuid, cat_uuid=cat_uuid)
        )
        
        # If target was pending, set it to active
        if target.status == TargetStatus.PENDING.value:
            target.status = TargetStatus.ACTIVE.value
            
        await self.db.commit()
        await self.db.refresh(target)

        return target

    async def get_target_by_uuid(self, target_uuid: UUID, cat_uuid: UUID) -> Target:
        result = await self.db.execute(
            select(Target)
            .join(targets_cats, Target.uuid == targets_cats.c.target_uuid)
            .where(
                (Target.uuid == target_uuid) &
                (targets_cats.c.cat_uuid == cat_uuid)
            )
        )
        target = result.scalar_one_or_none()
        if not target:
            # First check if the target exists at all
            exists_result = await self.db.execute(
                select(Target).where(Target.uuid == target_uuid)
            )
            exists = exists_result.scalar_one_or_none()
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Target does not belong to this cat"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target not found"
                )
        return target
    
    async def get_all_targets_for_cat(self, cat_uuid: UUID) -> list[Target] | None:
        result = await self.db.execute(
            select(Target)
            .join(targets_cats, Target.uuid == targets_cats.c.target_uuid)
            .where(targets_cats.c.cat_uuid == cat_uuid)
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No targets found for this cat"
            )
        return result.scalars().all()

    async def set_completed_target(self, target_uuid: UUID, current_cat: Cat) -> Target:
        target_result = await self.db.execute(
            select(Target).where(Target.uuid == target_uuid)
        )
        target = target_result.scalar_one_or_none()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        mission_uuid = target.mission_uuid

        # Check if mission of the target is assigned to current cat
        cat_mission_uuid = await self.db.execute(
            select(mission_cats.c.mission_uuid)
            .where(mission_cats.c.cat_uuid == current_cat.uuid)
        )
        cat_mission_uuids = {mid for (mid,) in cat_mission_uuid.all()}
        if target.mission_uuid not in cat_mission_uuids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to complete this target"
            )
        target.status = TargetStatus.COMPLETED.value
        await self.db.flush()

        # Close mission if all targets are completed
        all_targets_result = await self.db.execute(
            select(Target).where(Target.mission_uuid == mission_uuid)
        )
        all_targets = all_targets_result.scalars().all()
        if all(t.status == TargetStatus.COMPLETED.value for t in all_targets):
            mission = await self.db.execute(
                select(Mission).where(Mission.uuid == target.mission_uuid)
            )
            mission = mission.scalar_one_or_none()
            if mission:
                mission.status = MissionStatus.COMPLETED.value
        await self.db.commit()
        await self.db.refresh(target)
        return target
