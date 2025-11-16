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
from src.config.config import config
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models.tables import Base, Cat, Note, Mission, Target, targets_cats, mission_cats
from src.infrastructure.database.repositories.cats import CatRepository
from src.infrastructure.database.models.tables import Cat
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
async def test_cat(client: AsyncClient, mock_breed_validation_success):
    """Create a test cat user and return the response"""
    response = await client.post("/api/auth/signup", json={
        "name": "TestCat",
        "years_of_experience": 3,
        "password": "TestPass123!",
        "breed": "Persian",
    })
    return response.json()


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
async def admin_cat(client: AsyncClient, db_session: AsyncSession):
    """Create an admin cat user"""
    admin = Cat(
        name="AdminCat",
        password_hash=password_service("AdminPass123!"),
        breed="British Shorthair",
        years_of_experience=7,
        is_stuff=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, admin_cat):
    """Get admin authentication headers"""
    response = await client.post("/api/auth/login", json={
        "email": "admin@cat.com",
        "password": "AdminPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_breed_validation_success(monkeypatch):
    """Mock successful breed validation"""
    
    async def mock_validate_breed(self, breed_name):
        return True
    
    monkeypatch.setattr(CatRepository, "validate_breed", mock_validate_breed)
