from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from src.application.auth import get_current_admin
from src.presentation.schemas.cats import CatResponse
from src.presentation.schemas.missions import MissionCreate, MissionResponse, AssignCatsRequest
from src.infrastructure.database.models.tables import Cat
from src.infrastructure.database.repositories.cats import (
    CatRepository,
)
from src.infrastructure.database.repositories.missions import (
    MissionRepository,
)
from src.presentation.dependencies import (
    get_cat_repository,
    get_mission_repository,
)


router = APIRouter(prefix="/admin", tags=["Admins"])

    
@router.get("/cats")
async def get_all_cats(
    cat_repository: CatRepository = Depends(get_cat_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Get all cats in the system. Admin access required."""
    return await cat_repository.get_all_cats()

@router.get("/cats/name", response_model=list[CatResponse])
async def get_cat_by_name(
    search_query: str = Query(..., min_length=1),
    cat_repository: CatRepository = Depends(get_cat_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Get a cat by its name. Admin access required."""
    cats_by_query = await cat_repository.search_by_name(search_query)
    if not cats_by_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )
    return cats_by_query

@router.put("/cats/update/{cat_uuid}", response_model=CatResponse)
async def update_cat_salary(
    cat_uuid: UUID,
    salary: int = Query(..., ge=0),
    cat_repository: CatRepository = Depends(get_cat_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Update a cat's salary. Admin access required."""
    cat = await cat_repository.get_by_uuid(cat_uuid)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )
    updated_cat = await cat_repository.update_salary(cat, salary)
    return updated_cat

@router.delete("/cats/delete/{cat_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cat_by_uuid(
    cat_uuid: UUID,
    cat_repository: CatRepository = Depends(get_cat_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Delete a cat by its UUID. Admin access required."""
    cat = await cat_repository.get_by_uuid(cat_uuid)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )
    await cat_repository.delete_by_uuid(cat_uuid)
    return

@router.get("/cats/{cat_uuid}")
async def get_cat_by_uuid(
    cat_uuid: UUID,
    cat_repository: CatRepository = Depends(get_cat_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Get a cat by its UUID. Admin access required."""
    cat = await cat_repository.get_by_uuid(cat_uuid)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )
    return cat

@router.post("/mission/create", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    body: MissionCreate,
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Create a new mission. Admin access required."""
    new_mission = await mission_repository.create(body)
    return MissionResponse.from_mission(new_mission)

@router.get("/missions", response_model=list[MissionResponse])
async def get_all_missions(
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Get all missions in the system. Admin access required."""
    missions = await mission_repository.get_all_missions()
    return [MissionResponse.from_mission(mission) for mission in missions]


@router.delete("/mission/delete/{mission_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission_by_uuid(
    mission_uuid: UUID,
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Delete a mission by its UUID. Admin access required."""
    mission = await mission_repository.get_by_uuid(mission_uuid)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )
    await mission_repository.delete_mission_by_uuid(mission_uuid)

@router.put("/mission/{mission_uuid}/complete", response_model=MissionResponse)
async def complete_mission_by_uuid(
    mission_uuid: UUID,
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Mark a mission as completed by its UUID. Admin access required."""
    mission = await mission_repository.set_completed_mission(mission_uuid)
    return MissionResponse.from_mission(mission)

@router.put("/mission/{mission_uuid}/assign", response_model=MissionResponse)
async def assign_cats_to_mission(
    mission_uuid: UUID,
    request: AssignCatsRequest,
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Assign cats to a mission. Admin access required."""
    mission = await mission_repository.assign_cats_to_mission(mission_uuid, request.cat_uuids)
    return MissionResponse.from_mission(mission)


@router.get("/mission/{mission_uuid}", response_model=MissionResponse)
async def get_mission_by_uuid(
    mission_uuid: UUID,
    mission_repository: MissionRepository = Depends(get_mission_repository),
    current_cat: Cat = Depends(get_current_admin),
):
    """Get a mission by its UUID. Admin access required."""
    mission = await mission_repository.get_by_uuid(mission_uuid)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )
    return MissionResponse.from_mission(mission)