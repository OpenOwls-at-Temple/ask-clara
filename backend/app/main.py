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
    leads,
    materials,
    plan,
)

logger = logging.getLogger("clara")

_MONGO_INDEXED_COLLECTIONS = ("resumes", "assessments", "linkedin", "posting_materials")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Mongo indexes exist, but never let a transient Mongo outage block
    # boot — create_index is idempotent, and gating startup on it would take the
    # whole API (including routes that don't touch Mongo) down on a cold start.
    from app.database import get_mongo_db

    try:
        mongo = get_mongo_db()
        for collection in _MONGO_INDEXED_COLLECTIONS:
            await mongo[collection].create_index([("user_id", 1)])
    except Exception:
        logger.exception("Mongo index creation failed at startup")
    yield


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
app.include_router(admin.router, prefix="/api", tags=["admin"])
