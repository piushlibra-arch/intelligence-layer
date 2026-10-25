import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditRecord


class AuditService:
    @staticmethod
    async def log_record(
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor: str = "system",
        details: dict | None = None,
        engine_version: str | None = "1.0.0"
    ) -> AuditRecord:
        record = AuditRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            timestamp=datetime.now(UTC),
            actor=actor,
            details=details or {},
            engine_version=engine_version
        )
        db.add(record)
        return record
