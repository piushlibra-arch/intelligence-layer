import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database import Base

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class TradingSession(Base):
    __tablename__ = "trading_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trader_profiles.id"), index=True, nullable=False)
    scenario_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SessionStatus.ACTIVE,
        nullable=False
    )
    peak_pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    current_pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    total_trades: Mapped[int] = mapped_column(default=0, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    trader: Mapped["TraderProfile"] = relationship("TraderProfile", back_populates="sessions")
    events: Mapped[list["TradeEvent"]] = relationship("TradeEvent", back_populates="session", cascade="all, delete-orphan", order_by="TradeEvent.timestamp")
    feature_snapshots: Mapped[list["BehaviouralFeatureSnapshot"]] = relationship("BehaviouralFeatureSnapshot", back_populates="session", cascade="all, delete-orphan")
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship("RiskAssessment", back_populates="session", cascade="all, delete-orphan")
    interventions: Mapped[list["InterventionDecision"]] = relationship("InterventionDecision", back_populates="session", cascade="all, delete-orphan")
