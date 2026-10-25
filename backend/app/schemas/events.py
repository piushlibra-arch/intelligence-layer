from datetime import datetime
from decimal import Decimal
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from app.models.event import EventType, ProcessingStatus

class EventIngestRequest(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=128, description="Unique ID for event in source system")
    event_type: EventType
    instrument: str = Field(default="NIFTY", min_length=1, max_length=32)
    timestamp: datetime = Field(..., description="UTC event timestamp")
    side: str | None = Field(default=None, max_length=8)
    quantity: Decimal | None = Field(default=None, description="Trade or order quantity")
    price: Decimal | None = Field(default=None, description="Trade or order price")
    realized_pnl: Decimal | None = Field(default=None, description="Realized PnL if trade closed")
    unrealized_pnl: Decimal | None = Field(default=None, description="Unrealized PnL")
    source_id: str = Field(default="synthetic_sim", max_length=64)
    schema_version: str = Field(default="1.0", max_length=16)
    payload: dict | None = Field(default=None)

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str | None) -> str | None:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ("BUY", "SELL"):
                raise ValueError("Side must be 'BUY' or 'SELL'")
            return v_upper
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Quantity must be positive")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Price must be positive")
        return v

    @model_validator(mode="after")
    def validate_event_specific_fields(self) -> "EventIngestRequest":
        if self.event_type in (EventType.ORDER_SUBMITTED, EventType.ORDER_FILLED):
            if self.quantity is None:
                raise ValueError(f"Quantity required for {self.event_type.value}")
        if self.event_type == EventType.TRADE_CLOSED:
            if self.realized_pnl is None:
                raise ValueError("realized_pnl required for trade_closed")
        return self

class TradeEventResponse(BaseModel):
    id: uuid.UUID
    event_id: str
    session_id: uuid.UUID
    trader_id: uuid.UUID
    event_type: EventType
    instrument: str
    timestamp: datetime
    ingested_at: datetime
    side: str | None = None
    quantity: float | None = None
    price: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    source_id: str
    schema_version: str
    processing_status: ProcessingStatus
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)

class EventIngestResponse(BaseModel):
    event: TradeEventResponse
    is_duplicate: bool
    risk_assessment: dict | None = None
    intervention: dict | None = None
