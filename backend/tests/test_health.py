from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_ok_without_touching_db():
    """The liveness probe must respond without any DB dependency, so it stays
    green even when Mongo/Postgres are unreachable (e.g. Render cold start)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan_creates_index_on_every_collection():
    """Startup indexes user_id on all four Mongo collections."""
    from app.main import _MONGO_INDEXED_COLLECTIONS, lifespan

    collection = MagicMock()
    collection.create_index = AsyncMock()
    mongo = MagicMock()
    mongo.__getitem__.return_value = collection

    with patch("app.database.get_mongo_db", return_value=mongo):
        async with lifespan(app):
            pass

    requested = [call.args[0] for call in mongo.__getitem__.call_args_list]
    assert requested == list(_MONGO_INDEXED_COLLECTIONS)
    assert collection.create_index.await_count == len(_MONGO_INDEXED_COLLECTIONS)


@pytest.mark.asyncio
async def test_lifespan_survives_mongo_outage():
    """A Mongo outage must not block boot — the API still starts (serving routes
    that never touch Mongo, including /api/health) and logs the failure."""
    from app.main import lifespan

    with patch("app.database.get_mongo_db", side_effect=RuntimeError("mongo down")):
        with patch("app.main.logger") as mock_logger:
            async with lifespan(app):
                pass

    mock_logger.exception.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_survives_create_index_failure():
    """Connecting to Mongo but failing to create an index must also not block boot."""
    from app.main import lifespan

    collection = MagicMock()
    collection.create_index = AsyncMock(side_effect=RuntimeError("index failed"))
    mongo = MagicMock()
    mongo.__getitem__.return_value = collection

    with patch("app.database.get_mongo_db", return_value=mongo):
        with patch("app.main.logger") as mock_logger:
            async with lifespan(app):
                pass

    mock_logger.exception.assert_called_once()
