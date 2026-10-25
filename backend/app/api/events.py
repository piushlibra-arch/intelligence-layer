import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.security import require_api_key
from app.models.event import TradeEvent
from app.schemas.events import EventIngestRequest, TradeEventResponse, EventIngestResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/sessions", tags=["events"])

@router.post("/{session_id}/events", response_model=EventIngestResponse, status_code=status.HTTP_200_OK)
async def ingest_session_event(
    session_id: uuid.UUID,
    request: EventIngestRequest,
    db: AsyncSession = Depends(get_db),
    _api_key: str = Depends(require_api_key)
):
    return await EventService.ingest_event(db, session_id, request)

@router.get("/{session_id}/events", response_model=list[TradeEventResponse])
async def list_session_events(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(TradeEvent).where(TradeEvent.session_id == session_id).order_by(TradeEvent.timestamp.asc())
    res = await db.execute(query)
    events = res.scalars().all()
    return [TradeEventResponse.model_validate(e) for e in events]
