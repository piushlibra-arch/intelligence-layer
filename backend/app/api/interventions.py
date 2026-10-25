from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.security import require_api_key
from app.models.intervention import InterventionDecision
from app.schemas.interventions import (
    InterventionDecisionResponse,
    InterventionAcknowledgeRequest
)

router = APIRouter(tags=["interventions"])

@router.get("/sessions/{session_id}/interventions", response_model=list[InterventionDecisionResponse])
async def list_session_interventions(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(InterventionDecision).where(
        InterventionDecision.session_id == session_id
    ).order_by(InterventionDecision.decided_at.asc())
    res = await db.execute(query)
    decisions = res.scalars().all()
    return [InterventionDecisionResponse.model_validate(d) for d in decisions]

@router.post("/interventions/{decision_id}/acknowledge", response_model=InterventionDecisionResponse)
async def acknowledge_intervention(
    decision_id: uuid.UUID,
    req: InterventionAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    _api_key: str = Depends(require_api_key)
):
    query = select(InterventionDecision).where(InterventionDecision.id == decision_id)
    res = await db.execute(query)
    decision = res.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Intervention decision not found")

    decision.acknowledged = req.acknowledged
    decision.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(decision)
    return InterventionDecisionResponse.model_validate(decision)
