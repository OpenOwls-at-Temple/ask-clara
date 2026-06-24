from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, profile, assessment, documents, leads

app = FastAPI(title="Clara API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(assessment.router, prefix="/api", tags=["assessment"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(leads.router, prefix="/api", tags=["leads"])
