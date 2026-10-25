import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RiskBand(str, enum.Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"

class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_DATA = "insufficient_data"

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_sessions.id"), index=True, nullable=False)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trader_profiles.id"), index=True, nullable=False)
    feature_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("behavioural_feature_snapshots.id"), nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    risk_band: Mapped[RiskBand] = mapped_column(
        SQLEnum(RiskBand, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    triggered_signals: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        SQLEnum(ConfidenceLevel, values_callable=lambda x: [e.value for e in x]),
        default=ConfidenceLevel.HIGH,
        nullable=False
    )
    data_sufficiency: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    baseline_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deterministic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    session: Mapped["TradingSession"] = relationship("TradingSession", back_populates="risk_assessments")
    interventions: Mapped[list["InterventionDecision"]] = relationship("InterventionDecision", back_populates="assessment")

    __table_args__ = (
        Index("ix_risk_assess_session_time", "session_id", "assessed_at"),
    )
