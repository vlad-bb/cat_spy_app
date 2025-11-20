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
from src.infrastructure.database.models.tables import Base, Cat
from src.infrastructure.database.repositories.cats import CatRepository
from src.application.password_service import password_service



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
async def test_cat(db_session: AsyncSession, mock_breed_validation_success):
    """Create a test cat user and return the response"""
    test_cat = Cat(
        name="TestCat",
        years_of_experience=3,
        breed="Persian",
    )
    test_cat.password = password_service.get_password_hash("TestPass123!")
    
    db_session.add(test_cat)
    await db_session.commit()
    await db_session.refresh(test_cat)
    return test_cat


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
async def auth_headers(client: AsyncClient, test_cat):
    """Get authentication headers with valid JWT token"""
    response = await client.post("/api/auth/login", data={
        "username": "TestCat",
        "password": "TestPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_cat(db_session: AsyncSession, mock_breed_validation_success):
    """Create an admin cat user"""
    admin_cat = Cat(
        name="AdminCat",
        years_of_experience=7,
        breed="British Shorthair",
        is_staff=True,
    )
    admin_cat.password = password_service.get_password_hash("AdminPass123!")
    
    db_session.add(admin_cat)
    await db_session.commit()
    await db_session.refresh(admin_cat)
    return admin_cat


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, admin_cat):
    """Get admin authentication headers"""
    response = await client.post("/api/auth/login", data={
        "username": "AdminCat",
        "password": "AdminPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
async def mission_data_factory(test_mission, test_target):
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
async def test_note(client: AsyncClient, db_session: AsyncSession):
    """Create a note"""
    return {
        "content": "Target spotted near the warehouse at 3 AM. Very suspicious."
    }
