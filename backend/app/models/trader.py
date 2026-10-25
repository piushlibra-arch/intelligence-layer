import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class TraderProfile(Base):
    __tablename__ = "trader_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    default_position_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("500.00"), nullable=False)
    daily_loss_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("5000.00"), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sessions: Mapped[list["TradingSession"]] = relationship("TradingSession", back_populates="trader", cascade="all, delete-orphan")
