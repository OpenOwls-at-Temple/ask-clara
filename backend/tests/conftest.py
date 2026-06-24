import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import get_db
from app.main import app
from app.config import settings

# Use the same local Postgres DB, but all modifications run in a rolled-back transaction
import pytest_asyncio

# Use the same local Postgres DB, but all modifications run in a rolled-back transaction
TEST_DATABASE_URL = settings.database_url


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.connect() as connection:
        # Start the outer transaction
        transaction = await connection.begin()
        
        # Bind the session to the connection running in the transaction
        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            class_=AsyncSession
        )
        session = session_factory()
        
        yield session
        
        await session.close()
        # Roll back all changes made during the test
        await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
