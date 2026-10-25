import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventType(str, enum.Enum):
    SESSION_STARTED = "session_started"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_ACCEPTED = "order_accepted"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    TRADE_CLOSED = "trade_closed"
    PNL_UPDATED = "pnl_updated"
    EXPOSURE_UPDATED = "exposure_updated"
    SESSION_ENDED = "session_ended"

class ProcessingStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"

class TradeEvent(Base):
    __tablename__ = "trade_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), default="synthetic_sim", nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_sessions.id"), index=True, nullable=False)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trader_profiles.id"), index=True, nullable=False)
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    instrument: Mapped[str] = mapped_column(String(32), default="NIFTY", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    side: Mapped[str | None] = mapped_column(String(8), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    realized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProcessingStatus.ACCEPTED,
        nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    session: Mapped["TradingSession"] = relationship("TradingSession", back_populates="events")

    __table_args__ = (
        Index("ix_trade_events_event_source", "event_id", "source_id", unique=True),
        Index("ix_trade_events_session_timestamp", "session_id", "timestamp"),
    )
