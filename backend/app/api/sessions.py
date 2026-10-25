import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import require_api_key
from app.database import get_db
from app.models.session import TradingSession
from app.schemas.sessions import SessionCreateRequest, SessionStateResponse, TradingSessionResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=TradingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    _api_key: str = Depends(require_api_key)
):
    return await SessionService.create_session(
        db=db,
        trader_id=request.trader_id,
        scenario_id=request.scenario_id,
        is_synthetic=request.is_synthetic
    )

@router.get("", response_model=list[TradingSessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    query = select(TradingSession).order_by(TradingSession.started_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    sessions = res.scalars().all()
    return [TradingSessionResponse.model_validate(s) for s in sessions]

@router.get("/{session_id}", response_model=TradingSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(TradingSession).where(TradingSession.id == session_id)
    res = await db.execute(query)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return TradingSessionResponse.model_validate(session)

@router.get("/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await SessionService.get_session_state(db, session_id)
