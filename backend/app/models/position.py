import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_sessions.id"), index=True, nullable=False)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trader_profiles.id"), index=True, nullable=False)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)  # "BUY" or "SELL" or "FLAT"
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.00"), nullable=False)
    avg_entry_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.00"), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_pos_snap_session_time", "session_id", "snapshot_at"),
    )
