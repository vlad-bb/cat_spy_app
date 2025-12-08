import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from src.main import app 
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models.tables import Base, Cat, Target, targets_cats
from src.infrastructure.database.repositories.cats import CatRepository
from src.infrastructure.database.repositories.missions import MissionRepository
from src.presentation.schemas.missions import MissionCreate
from src.application.password_service import password_service
from uuid import uuid4



TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    poolclass=NullPool,  # Important for SQLite
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test"""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create test client with overridden database dependency"""
    
    async def override_get_db():
        yield db_session
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create async client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def cat_factory(db_session: AsyncSession, mock_breed_validation_success):
    """Factory to create and save cat users to test database."""
    async def _factory(**kwargs):
        # Default values
        defaults = {
            "name": "TestCat",
            "years_of_experience": 3,
            "breed": "Maine Coon",
        }

        # Update defaults with provided kwargs
        for key, value in defaults.items():
            if key not in kwargs:
                kwargs[key] = value

        # Extract password
        password = kwargs.pop("password", "TestPass123!")

        # Create cat
        cat = Cat(
            uuid=uuid4(),
            **kwargs
        )

        # Set password hash
        cat.password = password_service.get_password_hash(password)

        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        # Return both cat and plain password
        return cat, password
    
    return _factory


@pytest_asyncio.fixture
async def multiple_test_cats(db_session: AsyncSession, mock_breed_validation_success):
    """Create multiple test cats"""
    cats_data = [
        {"name": "TestCat1", "years_of_experience": 3, "breed": "Persian"},
        {"name": "TestCat2", "years_of_experience": 2, "breed": "Siamese"},
        {"name": "TestCat3", "years_of_experience": 5, "breed": "Maine Coon"}
    ]
    
    test_cats = []
    for cat_data in cats_data:
        cat = Cat(
            name=cat_data["name"],
            years_of_experience=cat_data["years_of_experience"],
            breed=cat_data["breed"],
        )
        cat.password = password_service.get_password_hash("TestPass123!")
        db_session.add(cat)
        test_cats.append(cat)
    
    await db_session.commit()
    
    for cat in test_cats:
        await db_session.refresh(cat)
    
    return test_cats


@pytest_asyncio.fixture
async def auth_headers_factory(client: AsyncClient):
    """Factory fixture to create auth headers for any user"""
    async def _create_headers(username, password):
        response = await client.post("/api/auth/login", data={
            "username": username,
            "password": password
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _create_headers


# Basic authenticated user
@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, cat_factory, auth_headers_factory):
    """Auth headers for a regular cat user"""
    cat, password = await cat_factory()
    return await auth_headers_factory(cat.name, password)

# Admin authenticated user
@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, cat_factory, auth_headers_factory):
    """Auth headers for an admin cat user"""
    cat, password = await cat_factory(
        name="AdminCat",
        is_staff=True,
        password="AdminPass123!"
    )
    return await auth_headers_factory(cat.name, password)


@pytest.fixture
def mock_breed_validation_success(monkeypatch: pytest.MonkeyPatch):
    """Mock successful breed validation"""
    
    async def mock_validate_breed(self, breed_name):
        return True
    
    monkeypatch.setattr(CatRepository, "validate_breed", mock_validate_breed)


@pytest_asyncio.fixture
async def test_mission(client: AsyncClient, db_session: AsyncSession):
    """Create a mission"""
    return {
        "name": "Operation Red Laser",
        "description": "Investigate suspicious laser pointer activity in warehouse district"
    }


@pytest_asyncio.fixture
async def test_target(client: AsyncClient, db_session: AsyncSession):
    """Create a target"""
    return {
        "name": "The Red Dot Mastermind", 
        "country": "Japan"
    }


@pytest_asyncio.fixture
async def mission_factory(test_mission, test_target):
    """Factory to create mission data with customizations"""
    def _factory(targets: list = None, cat_uuids: list = None, **overrides):
        base_data = {
            "name": test_mission["name"],
            "description": test_mission["description"],
            "targets": targets or [test_target],
            "cat_uuids": cat_uuids or []
        }
        return {**base_data, **overrides}
    return _factory


@pytest_asyncio.fixture
async def mission_db_factory(db_session: AsyncSession, mission_factory):
    """Factory to create and save mission entities to test database"""
    async def _factory(**kwargs):
        # Generate unique mission names
        if 'name' not in kwargs:
            kwargs['name'] = f"Test Mission {uuid4().hex[:8]}"

        # Use the existing factory to generate mission data
        mission_data = mission_factory(**kwargs)
        
        # Convert to MissionCreate schema
        mission_create = MissionCreate(**mission_data)

        # Use repository to create and save mission
        repository = MissionRepository(db_session)
        mission = await repository.create(mission_create)
        
        db_session.add(mission)
        await db_session.commit()
        await db_session.refresh(mission)

        return mission
    
    return _factory


@pytest_asyncio.fixture
async def target_db_factory(db_session: AsyncSession, test_target, mission_db_factory):
    """Factory to create and save target entities to test database"""
    async def _factory(mission=None, **kwargs):
        # Create a mission if not provided (Target requires a mission)
        if mission is None:
            mission = await mission_db_factory()
        
        # Generate unique target name if not provided
        if 'name' not in kwargs:
            kwargs['name'] = test_target["name"]
        if 'country' not in kwargs:
            kwargs['country'] = test_target["country"]
        
        # Create target with mission_uuid
        target = Target(
            uuid=uuid4(),
            mission_uuid=mission.uuid,
            **kwargs
        )
        
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)
        
        return target
    
    return _factory


@pytest_asyncio.fixture
async def cat_mission_target_factory(cat_factory, mission_db_factory, target_db_factory, auth_headers_factory, db_session):
    """Create a complete setup: cat, mission with cat assigned, target, and auth headers"""
    async def _factory(assign_to_target=False,**kwargs):
        # Extract custom parameters with defaults
        cat_kwargs = kwargs.get('cat_kwargs', {})
        mission_kwargs = kwargs.get('mission_kwargs', {})
        target_kwargs = kwargs.get('target_kwargs', {})
        
        # 1. Create cat
        cat, password = await cat_factory(**cat_kwargs)
        
        # 2. Create mission with this cat assigned
        mission = await mission_db_factory(
            cat_uuids=[cat.uuid],
            **mission_kwargs
        )
        
        # 3. Create target for this mission
        target = await target_db_factory(
            mission=mission,
            **target_kwargs
        )
        # 4. Optionally assign cat to target
        if assign_to_target:
            await db_session.execute(
            targets_cats.insert().values(
                target_uuid=target.uuid,
                cat_uuid=cat.uuid
            )
        )
        
            await db_session.commit()
        
        # Refresh relationships
        await db_session.refresh(target, ['cats'])
        
        # 5. Create auth headers for the cat
        headers = await auth_headers_factory(cat.name, password)
        
        return {
            'cat': cat,
            'password': password,
            'mission': mission,
            'target': target,
            'headers': headers,
            'db_data': {
                'cat_uuid': cat.uuid,
                'mission_uuid': mission.uuid,
                'target_uuid': target.uuid
            }
        }
    
    return _factory


@pytest_asyncio.fixture
async def test_note(client: AsyncClient, db_session: AsyncSession):
    """Create a note"""
    return {
        "content": "Target spotted near the warehouse at 3 AM. Very suspicious."
    }
