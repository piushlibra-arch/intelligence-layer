import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.risk import RiskAssessment
from app.schemas.risk import RiskAssessmentResponse
from app.schemas.features import SignalResult

router = APIRouter(prefix="/sessions", tags=["risk"])

def _to_response(a: RiskAssessment) -> RiskAssessmentResponse:
    signals = [SignalResult(**s) for s in a.triggered_signals]
    return RiskAssessmentResponse(
        id=a.id,
        session_id=a.session_id,
        assessed_at=a.assessed_at,
        risk_score=float(a.risk_score),
        risk_band=a.risk_band,
        triggered_signals=signals,
        explanation=a.explanation,
        confidence=a.confidence,
        data_sufficiency=float(a.data_sufficiency),
        engine_version=a.engine_version,
        baseline_version=a.baseline_version
    )

@router.get("/{session_id}/risk", response_model=list[RiskAssessmentResponse])
async def list_session_risk_assessments(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(RiskAssessment).where(
        RiskAssessment.session_id == session_id
    ).order_by(RiskAssessment.assessed_at.asc())
    res = await db.execute(query)
    assessments = res.scalars().all()
    return [_to_response(a) for a in assessments]

@router.get("/{session_id}/risk/latest", response_model=RiskAssessmentResponse)
async def get_latest_risk_assessment(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(RiskAssessment).where(
        RiskAssessment.session_id == session_id
    ).order_by(RiskAssessment.assessed_at.desc()).limit(1)
    res = await db.execute(query)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="No risk assessment found for session")
    return _to_response(assessment)
