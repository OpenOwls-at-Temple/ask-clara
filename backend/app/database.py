from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.environment == "local")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

_mongo_client: AsyncIOMotorClient | None = None


def _get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    return _mongo_client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return _get_mongo_client()["clara"]


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
