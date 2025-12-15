from fastapi import APIRouter, Depends, status
from uuid import UUID

from src.infrastructure.database.models.tables import Cat
from src.infrastructure.database.repositories.cats import (
    CatRepository
)
from src.infrastructure.database.repositories.missions import (
    MissionRepository
)
from src.infrastructure.database.repositories.notes import (
    NoteRepository
)
from src.infrastructure.database.repositories.targets import (
    TargetRepository
)
from src.application.auth import get_current_cat
from src.presentation.schemas.cats import CatProfile
from src.presentation.schemas.missions import MissionResponse
from src.presentation.schemas.notes import NoteCreate, NoteResponse
from src.presentation.schemas.targets import TargetResponse
from src.presentation.dependencies import (
    get_cat_repository,
    get_mission_repository,
    get_target_repository,
    get_note_repository,
)


router = APIRouter(prefix="/cats", tags=["Cats"])


@router.get("/me")
async def get_my_cat(
    cat_repository: CatRepository = Depends(get_cat_repository),
    current_cat: Cat = Depends(get_current_cat),
) -> CatProfile:
    my_cat = CatProfile(
        name=current_cat.name,
        years_of_experience=current_cat.years_of_experience,
        breed=current_cat.breed,
        salary=current_cat.salary,
        created_at=current_cat.created_at,
    )
    return my_cat

@router.get("/missions", response_model=list[MissionResponse])
async def get_all_missions_for_cat(
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    missions = await mission_repository.get_all_missions_for_cat(current_cat.uuid)
    return [MissionResponse.from_mission(mission) for mission in missions]

@router.put("/target/{target_uuid}/assign", response_model=TargetResponse, status_code=status.HTTP_200_OK)
async def assign_cat_to_target(
    target_uuid: UUID,
    target_repository: TargetRepository = Depends(get_target_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    target = await target_repository.assign_cat_to_target(target_uuid, current_cat.uuid)
    return target

@router.get("/target/{target_uuid}", response_model=TargetResponse)
async def get_target_by_uuid(
    target_uuid: UUID,
    target_repository: TargetRepository = Depends(get_target_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    target = await target_repository.get_target_by_uuid(target_uuid, current_cat.uuid)
    return target

@router.get("/targets", response_model=list[TargetResponse])
async def get_my_targets(
    target_repository: TargetRepository = Depends(get_target_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    targets = await target_repository.get_all_targets_for_cat(current_cat.uuid)
    return targets

@router.put("/target/complete/{target_uuid}", response_model=TargetResponse, status_code=status.HTTP_200_OK)
async def complete_target(
    target_uuid: UUID,
    target_repository: TargetRepository = Depends(get_target_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    target = await target_repository.set_completed_target(
        target_uuid=target_uuid,
        current_cat=current_cat
    )
    return target

@router.post("/target-note/{target_uuid}", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note_for_target(
    target_uuid: UUID,
    note_create: NoteCreate,
    note_repository: NoteRepository = Depends(get_note_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    note = await note_repository.create(
        target_uuid=target_uuid,
        content=note_create.content,
        cat_uuid=current_cat.uuid
    )
    return note

@router.get("/notes", response_model=list[NoteResponse])
async def get_notes(
    note_repository: NoteRepository = Depends(get_note_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    return await note_repository.get_all_for_cat(current_cat.uuid)

@router.put("/note/{note_uuid}", response_model=NoteResponse)
async def update_note(
    note_uuid: UUID,
    note_update: NoteCreate,
    note_repository: NoteRepository = Depends(get_note_repository),
    current_cat: Cat = Depends(get_current_cat),
):
    updated_note = await note_repository.update_note(
        note_uuid=note_uuid,
        new_content=note_update.content,
        cat_uuid=current_cat.uuid
    )
    return updated_note

