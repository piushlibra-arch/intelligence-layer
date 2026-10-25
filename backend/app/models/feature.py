import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Numeric, Integer, DateTime, ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class BehaviouralFeatureSnapshot(Base):
    __tablename__ = "behavioural_feature_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_sessions.id"), index=True, nullable=False)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trader_profiles.id"), index=True, nullable=False)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("risk_assessments.id", use_alter=True), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    
    # Feature 1: Post-loss re-entry latency
    post_loss_reentry_seconds: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    baseline_reentry_seconds: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Feature 2: Position-size escalation
    position_size_current: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    position_size_baseline: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    position_size_limit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    # Feature 3: Trade-frequency escalation
    trade_frequency_current: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trade_frequency_baseline: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    trade_frequency_window_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Feature 4: Consecutive-loss pattern
    consecutive_losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consecutive_loss_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)

    # Feature 5: Profit giveback
    peak_session_pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    current_session_pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    profit_giveback_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Feature 6: Combined behavioural deviation
    combined_deviation_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    feature_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)

    session: Mapped["TradingSession"] = relationship("TradingSession", back_populates="feature_snapshots")

    __table_args__ = (
        Index("ix_feat_snap_session_computed", "session_id", "computed_at"),
    )
