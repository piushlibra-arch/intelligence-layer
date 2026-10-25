import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engine.baseline_engine import BaselineEngine
from app.models.session import TradingSession
from app.models.trader import TraderProfile
from app.schemas.baselines import BaselineInfoResponse, TraderProfileResponse

router = APIRouter(tags=["baselines"])

@router.get("/traders", response_model=list[TraderProfileResponse])
async def list_traders(db: AsyncSession = Depends(get_db)):
    query = select(TraderProfile).order_by(TraderProfile.created_at.asc())
    res = await db.execute(query)
    traders = res.scalars().all()
    return [
        TraderProfileResponse(
            id=t.id,
            external_id=t.external_id,
            display_name=t.display_name,
            created_at=t.created_at.isoformat(),
            default_position_limit=float(t.default_position_limit),
            daily_loss_limit=float(t.daily_loss_limit),
            is_synthetic=t.is_synthetic
        )
        for t in traders
    ]

@router.get("/traders/{trader_id}", response_model=TraderProfileResponse)
async def get_trader(trader_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    query = select(TraderProfile).where(TraderProfile.id == trader_id)
    res = await db.execute(query)
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Trader not found")
    return TraderProfileResponse(
        id=t.id,
        external_id=t.external_id,
        display_name=t.display_name,
        created_at=t.created_at.isoformat(),
        default_position_limit=float(t.default_position_limit),
        daily_loss_limit=float(t.daily_loss_limit),
        is_synthetic=t.is_synthetic
    )

@router.get("/traders/{trader_id}/baseline", response_model=BaselineInfoResponse)
async def get_trader_baseline(trader_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    baseline = await BaselineEngine.compute_baseline(db, trader_id)
    return BaselineEngine.to_schema_response(baseline)

@router.get("/sessions/{session_id}/baseline", response_model=BaselineInfoResponse)
async def get_session_baseline(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session_q = select(TradingSession).where(TradingSession.id == session_id)
    session_res = await db.execute(session_q)
    session = session_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    baseline = await BaselineEngine.compute_baseline(
        db=db,
        trader_id=session.trader_id,
        before_timestamp=session.started_at
    )
    return BaselineEngine.to_schema_response(baseline)
