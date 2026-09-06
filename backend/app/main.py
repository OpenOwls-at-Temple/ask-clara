import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import (
    admin,
    auth,
    profile,
    assessment,
    documents,
    interview_prep,
    leads,
    materials,
    plan,
)

logger = logging.getLogger("clara")

_MONGO_INDEXED_COLLECTIONS = (
    "resumes",
    "assessments",
    "linkedin",
    "posting_materials",
    "interview_preps",
)


async def _ensure_mongo_indexes() -> None:
    """Create the user_id indexes. Idempotent, so retrying on the next boot is free."""
    from app.database import get_mongo_db

    try:
        mongo = get_mongo_db()
        for collection in _MONGO_INDEXED_COLLECTIONS:
            await mongo[collection].create_index([("user_id", 1)])
    except Exception:
        logger.exception("Mongo index creation failed at startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Index creation runs in the background rather than inline. When Mongo is
    # unreachable, create_index blocks for the driver's full server-selection
    # timeout (30s by default) — and until the lifespan startup returns, the app
    # accepts no connections at all, so /api/health would be refused for that
    # whole window and the Render health check would fail exactly when it is
    # most needed. Indexes are a performance concern, not a correctness one, so
    # nothing needs them in place before we start serving.
    app.state.mongo_index_task = asyncio.create_task(_ensure_mongo_indexes())
    try:
        yield
    finally:
        task = app.state.mongo_index_task
        if not task.done():
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Clara API", lifespan=lifespan)

_cors_origins = [settings.frontend_origin]
if settings.environment == "local":
    _cors_origins.append("http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
async def health():
    """Lightweight liveness probe — no DB calls, safe for Render health checks
    and keep-alive pings."""
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(assessment.router, prefix="/api", tags=["assessment"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(leads.router, prefix="/api", tags=["leads"])
app.include_router(materials.router, prefix="/api", tags=["materials"])
app.include_router(interview_prep.router, prefix="/api", tags=["interview-prep"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
