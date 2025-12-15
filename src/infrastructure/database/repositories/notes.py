from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from fastapi import HTTPException, status
from uuid import UUID

from src.domain.entities.target import TargetStatus
from src.infrastructure.database.models.tables import Mission, Note, Target, Cat

class NoteRepository:
    """Repository for managing Note entities in the database."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, target_uuid: UUID, content: str, cat_uuid: UUID) -> Note:
        cat = await self.db.execute(
            select(Cat).where(Cat.uuid == cat_uuid)
        )   
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cat not found"
            )
        cat = cat.scalar_one_or_none()

        target = await self.db.execute(
            select(Target).where(Target.uuid == target_uuid)
        )
        target = target.scalar_one_or_none()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        cat_mission = await self.db.execute(
            select(Mission)
            .join(Mission.cat)
            .where(Mission.uuid == target.mission_uuid, Cat.uuid == cat_uuid)
        )
        cat_mission = cat_mission.scalar_one_or_none()
        if not cat_mission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cat is not assigned to the mission of this target"
            )

        note = Note(
            content=content,
            target_uuid=target.uuid,
            cat_uuid=cat.uuid
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_note_by_uuid(self, note_uuid: UUID) -> Optional[Note]:
        result = await self.db.execute(
            select(Note).where(Note.uuid == note_uuid)
        )
        return result.scalar_one_or_none()

    async def update_note(self, note_uuid: UUID, new_content: str, cat_uuid: UUID) -> Note:
        note = await self.get_note_by_uuid(note_uuid)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        is_target_completed = await self.db.execute(
            select(Target).where(Target.uuid == note.target_uuid, Target.status == TargetStatus.COMPLETED.value)
        )
        if is_target_completed.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update note for a completed target"
            )
        cat = await self.db.execute(
            select(Cat).where(Cat.uuid == cat_uuid)
        )
        cat = cat.scalar_one_or_none()
        if not cat or note.cat_uuid != cat.uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cat is not the author of this note"
            )

        note.content = new_content
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_all_for_cat(self, cat_uuid: UUID) -> List[Note]:
        result = await self.db.execute(
            select(Note)
            .where(Note.cat_uuid == cat_uuid)
            .options(selectinload(Note.note_cat))
        )
        notes = result.scalars().all()

        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No notes found for this cat"
            )
        return notes
