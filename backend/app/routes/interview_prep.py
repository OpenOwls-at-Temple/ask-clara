"""Feature 9: interview prep guidance.

POST /interview-prep — generate prep for one ranked target role or for a
    posting the student supplied by link or manual entry (quota-gated).
GET /interview-prep — list the student's saved prep guides (cached — viewing
    never re-calls the model).

The lead-scoped variant lives in routes/leads.py
(POST /leads/:id/interview-prep) and shares the quota helpers in
routes/materials.py.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.documents.interview_prep import get_interview_preps_for_user
from app.models.user import User
from app.routes.materials import consume_quota_slot, refund_quota_slot
from app.schemas.interview_prep import InterviewPrepOut, InterviewPrepRequest
from app.services import interview_prep_service

router = APIRouter()


@router.post("/interview-prep", response_model=InterviewPrepOut)
async def generate_interview_prep(
    body: InterviewPrepRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await consume_quota_slot(db, user.id)

    mongo = get_mongo_db()
    try:
        if body.target_rank is not None:
            doc = await interview_prep_service.generate_for_role(
                db, mongo, user.id, body.target_rank
            )
        else:
            doc = await interview_prep_service.generate_for_posting(
                db, mongo, user.id, body.posting.model_dump()
            )
    except Exception as exc:
        await refund_quota_slot(db, user.id)
        if isinstance(exc, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return InterviewPrepOut(**doc)


@router.get("/interview-prep", response_model=list[InterviewPrepOut])
async def list_interview_preps(
    user: User = Depends(get_current_user),
):
    mongo = get_mongo_db()
    docs = await get_interview_preps_for_user(mongo, str(user.id))
    return [InterviewPrepOut(**doc) for doc in docs]
