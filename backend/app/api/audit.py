import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.audit import AuditRecord

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("")
async def query_audit_records(
    entity_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditRecord)
    if entity_type:
        query = query.where(AuditRecord.entity_type == entity_type)
    query = query.order_by(AuditRecord.timestamp.desc()).offset(offset).limit(limit)

    res = await db.execute(query)
    records = res.scalars().all()
    return [
        {
            "id": str(r.id),
            "entity_type": r.entity_type,
            "entity_id": str(r.entity_id),
            "action": r.action,
            "timestamp": r.timestamp.isoformat(),
            "actor": r.actor,
            "details": r.details,
            "engine_version": r.engine_version
        }
        for r in records
    ]

@router.get("/{entity_type}/{entity_id}")
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditRecord).where(
        AuditRecord.entity_type == entity_type,
        AuditRecord.entity_id == entity_id
    ).order_by(AuditRecord.timestamp.asc())

    res = await db.execute(query)
    records = res.scalars().all()
    return [
        {
            "id": str(r.id),
            "entity_type": r.entity_type,
            "entity_id": str(r.entity_id),
            "action": r.action,
            "timestamp": r.timestamp.isoformat(),
            "actor": r.actor,
            "details": r.details,
            "engine_version": r.engine_version
        }
        for r in records
    ]
