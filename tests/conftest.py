import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from uuid import uuid4

from src.main import app 
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models.tables import Base, Cat, Target, Note, targets_cats
from src.infrastructure.database.repositories.cats import CatRepository
from src.infrastructure.database.repositories.missions import MissionRepository
from src.presentation.schemas.missions import MissionCreate
from src.application.password_service import password_service


# ============================================================================
# Database Configuration
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ============================================================================
# Core Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create test client with overridden database dependency"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_breed_validation_success(monkeypatch: pytest.MonkeyPatch):
    """Mock successful breed validation"""
    async def mock_validate_breed(self, breed_name):
        return True
    
    monkeypatch.setattr(CatRepository, "validate_breed", mock_validate_breed)


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def auth_headers_factory(client: AsyncClient):
    """Factory fixture to create auth headers for any user"""
    async def _create_headers(username: str, password: str) -> dict:
        response = await client.post("/api/auth/login", data={
            "username": username,
            "password": password
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _create_headers


@pytest_asyncio.fixture
async def auth_headers(cat_factory, auth_headers_factory):
    """Auth headers for a regular cat user"""
    cat, password = await cat_factory()
    return await auth_headers_factory(cat.name, password)


@pytest_asyncio.fixture
async def admin_headers(cat_factory, auth_headers_factory):
    """Auth headers for an admin cat user"""
    cat, password = await cat_factory(
        name="AdminCat",
        is_staff=True,
        password="AdminPass123!"
    )
    return await auth_headers_factory(cat.name, password)


# ============================================================================
# Entity Factories
# ============================================================================

@pytest_asyncio.fixture
async def cat_factory(db_session: AsyncSession, mock_breed_validation_success):
    """Factory to create and save cat users to test database."""
    async def _factory(**kwargs) -> tuple[Cat, str]:
        defaults = {
            "name": "TestCat",
            "years_of_experience": 3,
            "breed": "Maine Coon",
        }
        
        # Merge defaults with kwargs
        cat_data = {**defaults, **kwargs}
        password = cat_data.pop("password", "TestPass123!")

        cat = Cat(
            uuid=uuid4(),
            **cat_data
        )
        cat.password = password_service.get_password_hash(password)

        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        return cat, password
    
    return _factory


@pytest_asyncio.fixture
async def mission_factory():
    """Factory to create mission data dictionaries (not persisted)"""
    def _factory(targets: list = None, cat_uuids: list = None, **overrides) -> dict:
        defaults = {
            "name": "Operation Red Laser",
            "description": "Investigate suspicious laser pointer activity in warehouse district",
            "targets": targets or [{
                "name": "The Red Dot Mastermind",
                "country": "Japan"
            }],
            "cat_uuids": cat_uuids or []
        }
        return {**defaults, **overrides}
    return _factory


@pytest_asyncio.fixture
async def mission_db_factory(db_session: AsyncSession, mission_factory):
    """Factory to create and persist mission entities"""
    async def _factory(**kwargs) -> object:
        if 'name' not in kwargs:
            kwargs['name'] = f"Test Mission {uuid4().hex[:8]}"

        mission_data = mission_factory(**kwargs)
        mission_create = MissionCreate(**mission_data)

        repository = MissionRepository(db_session)
        mission = await repository.create(mission_create)
        
        db_session.add(mission)
        await db_session.commit()
        await db_session.refresh(mission)

        return mission
    
    return _factory


@pytest_asyncio.fixture
async def target_db_factory(db_session: AsyncSession, mission_db_factory):
    """Factory to create and persist target entities"""
    async def _factory(mission=None, assign_cat=None, **kwargs) -> Target:
        if mission is None:
            mission = await mission_db_factory()
        
        defaults = {
            "name": "The Red Dot Mastermind",
            "country": "Japan"
        }
        target_data = {**defaults, **kwargs}
        
        target = Target(
            uuid=uuid4(),
            mission_uuid=mission.uuid,
            **target_data
        )

        db_session.add(target)
        await db_session.commit()

        # Assign cat to target if specified
        if assign_cat:
            await db_session.execute(
                targets_cats.insert().values(
                    target_uuid=target.uuid,
                    cat_uuid=assign_cat.uuid
                )
            )
            await db_session.commit()
        
        await db_session.refresh(target)
        return target
    
    return _factory


@pytest_asyncio.fixture
async def note_db_factory(db_session: AsyncSession):
    """Factory to create and persist note entities"""
    async def _factory(cat_uuid, target_uuid, **kwargs) -> Note:
        defaults = {
            "content": "Target spotted near the warehouse at 3 AM. Very suspicious."
        }
        note_data = {**defaults, **kwargs}

        note = Note(
            uuid=uuid4(),
            target_uuid=target_uuid,
            cat_uuid=cat_uuid,
            **note_data
        )
        
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)
        
        return note
    
    return _factory


# ============================================================================
# Convenience Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def multiple_test_cats(db_session: AsyncSession, cat_factory):
    """Create multiple test cats with different attributes"""
    cats_data = [
        {"name": "TestCat1", "years_of_experience": 3, "breed": "Persian"},
        {"name": "TestCat2", "years_of_experience": 2, "breed": "Siamese"},
        {"name": "TestCat3", "years_of_experience": 5, "breed": "Maine Coon"}
    ]
    
    cats = []
    for cat_data in cats_data:
        cat, _ = await cat_factory(**cat_data)
        cats.append(cat)
    
    return cats


@pytest_asyncio.fixture
async def cat_mission_target_factory(
    cat_factory, 
    mission_db_factory, 
    target_db_factory, 
    note_db_factory, 
    auth_headers_factory,
    db_session
):
    """Create complete test setup: cat, mission, target, and optional note"""
    async def _factory(assign_to_target: bool = False, create_note: bool = False, **kwargs) -> dict:
        cat_kwargs = kwargs.get("cat_kwargs", {})
        mission_kwargs = kwargs.get("mission_kwargs", {})
        target_kwargs = kwargs.get("target_kwargs", {})
        note_kwargs = kwargs.get("note_kwargs", {})
        
        # Create cat
        cat, password = await cat_factory(**cat_kwargs)
        
        # Create mission with cat assigned
        mission = await mission_db_factory(
            cat_uuids=[cat.uuid],
            **mission_kwargs
        )
        
        # Create target
        target = await target_db_factory(
            mission=mission,
            assign_cat=cat if assign_to_target else None,
            **target_kwargs
        )
        
        # Refresh to load relationships
        if assign_to_target:
            await db_session.refresh(target, ['cats'])

        # Create note if requested
        note = None
        if create_note:
            note = await note_db_factory(
                target_uuid=target.uuid,
                cat_uuid=cat.uuid,
                **note_kwargs
            )
        
        # Create auth headers
        headers = await auth_headers_factory(cat.name, password)
        
        return {
            "cat": cat,
            "password": password,
            "mission": mission,
            "target": target,
            "note": note,
            "headers": headers,
            "db_data": {
                "cat_uuid": cat.uuid,
                "mission_uuid": mission.uuid,
                "target_uuid": target.uuid
            }
        }
    
    return _factory
