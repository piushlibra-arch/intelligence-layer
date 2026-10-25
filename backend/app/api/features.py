import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.feature import BehaviouralFeatureSnapshot
from app.schemas.features import FeatureSnapshotResponse

router = APIRouter(prefix="/sessions", tags=["features"])

@router.get("/{session_id}/features", response_model=list[FeatureSnapshotResponse])
async def list_session_features(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(BehaviouralFeatureSnapshot).where(
        BehaviouralFeatureSnapshot.session_id == session_id
    ).order_by(BehaviouralFeatureSnapshot.computed_at.asc())
    res = await db.execute(query)
    snapshots = res.scalars().all()
    return [FeatureSnapshotResponse.model_validate(s) for s in snapshots]

@router.get("/{session_id}/features/latest", response_model=FeatureSnapshotResponse)
async def get_latest_session_features(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(BehaviouralFeatureSnapshot).where(
        BehaviouralFeatureSnapshot.session_id == session_id
    ).order_by(BehaviouralFeatureSnapshot.computed_at.desc()).limit(1)
    res = await db.execute(query)
    snapshot = res.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No feature snapshot found for session")
    return FeatureSnapshotResponse.model_validate(snapshot)
