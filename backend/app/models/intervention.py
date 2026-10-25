import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ActionType(str, enum.Enum):
    MONITOR = "monitor"
    WARNING = "warning"
    COOLDOWN_OFFER = "cooldown_offer"
    REVIEW_RECOMMENDATION = "review_recommendation"
    SESSION_PROTECTION_SIMULATION = "session_protection_simulation"

class InterventionPolicy(Base):
    __tablename__ = "intervention_policies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    min_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    max_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("100.00"), nullable=False)
    min_confidence: Mapped[str] = mapped_column(String(32), default="low", nullable=False)
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

class InterventionDecision(Base):
    __tablename__ = "intervention_decisions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_assessments.id"), index=True, nullable=False)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("intervention_policies.id"), nullable=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_sessions.id"), index=True, nullable=False)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trader_profiles.id"), index=True, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    action_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)

    assessment: Mapped["RiskAssessment"] = relationship("RiskAssessment", back_populates="interventions")
    session: Mapped["TradingSession"] = relationship("TradingSession", back_populates="interventions")

    __table_args__ = (
        Index("ix_interv_dec_session_time", "session_id", "decided_at"),
    )
