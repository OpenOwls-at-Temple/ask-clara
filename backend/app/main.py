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

app = FastAPI(title="Clara API")

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


@app.on_event("startup")
async def startup_event():
    from app.database import get_mongo_db

    mongo = get_mongo_db()
    await mongo["resumes"].create_index([("user_id", 1)])
    await mongo["assessments"].create_index([("user_id", 1)])
    await mongo["linkedin"].create_index([("user_id", 1)])
    await mongo["posting_materials"].create_index([("user_id", 1)])


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(assessment.router, prefix="/api", tags=["assessment"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(leads.router, prefix="/api", tags=["leads"])
app.include_router(materials.router, prefix="/api", tags=["materials"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
