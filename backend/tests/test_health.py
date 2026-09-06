import asyncio
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
            await app.state.mongo_index_task

    requested = [call.args[0] for call in mongo.__getitem__.call_args_list]
    assert requested == list(_MONGO_INDEXED_COLLECTIONS)
    assert collection.create_index.await_count == len(_MONGO_INDEXED_COLLECTIONS)


@pytest.mark.asyncio
async def test_lifespan_does_not_block_startup_on_unreachable_mongo():
    """Startup must not wait on Mongo. create_index blocks for the driver's full
    server-selection timeout (30s) when Mongo is down, and the app accepts no
    connections until lifespan startup returns — so an inline await would make
    /api/health unreachable for exactly the window the health check exists for."""
    from app.main import lifespan

    async def never_returns(*args, **kwargs):
        await asyncio.sleep(3600)

    collection = MagicMock()
    collection.create_index = AsyncMock(side_effect=never_returns)
    mongo = MagicMock()
    mongo.__getitem__.return_value = collection

    with patch("app.database.get_mongo_db", return_value=mongo):
        cm = lifespan(app)
        # Entering the context manager runs startup. Bounded by an explicit
        # timeout so an inline-await regression fails here in seconds rather
        # than hanging the whole suite.
        async with asyncio.timeout(5):
            await cm.__aenter__()

        task = app.state.mongo_index_task
        # Startup returned while the index call is still outstanding — which is
        # the point: the app is already serving /api/health.
        assert not task.done()
        await cm.__aexit__(None, None, None)

    assert task.cancelled()


@pytest.mark.asyncio
async def test_lifespan_survives_mongo_outage():
    """A Mongo outage must not take down boot — the failure is logged and the API
    still serves routes that never touch Mongo, including /api/health."""
    from app.main import lifespan

    with patch("app.database.get_mongo_db", side_effect=RuntimeError("mongo down")):
        with patch("app.main.logger") as mock_logger:
            async with lifespan(app):
                await app.state.mongo_index_task

    mock_logger.exception.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_survives_create_index_failure():
    """Connecting to Mongo but failing to create an index must also not break boot."""
    from app.main import lifespan

    collection = MagicMock()
    collection.create_index = AsyncMock(side_effect=RuntimeError("index failed"))
    mongo = MagicMock()
    mongo.__getitem__.return_value = collection

    with patch("app.database.get_mongo_db", return_value=mongo):
        with patch("app.main.logger") as mock_logger:
            async with lifespan(app):
                await app.state.mongo_index_task

    mock_logger.exception.assert_called_once()
