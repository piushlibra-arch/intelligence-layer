import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeatureSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    computed_at: datetime
    post_loss_reentry_seconds: float | None = None
    baseline_reentry_seconds: float | None = None
    position_size_current: float | None = None
    position_size_baseline: float | None = None
    position_size_limit: float | None = None
    trade_frequency_current: int | None = None
    trade_frequency_baseline: float | None = None
    trade_frequency_window_minutes: int = 30
    consecutive_losses: int = 0
    consecutive_loss_total: float = 0.0
    peak_session_pnl: float = 0.0
    current_session_pnl: float = 0.0
    profit_giveback_pct: float | None = None
    combined_deviation_score: float | None = None
    feature_version: str = "1.0"

class SignalResult(BaseModel):
    name: str
    triggered: bool
    severity: str  # "low", "medium", "high"
    value: float | None = None
    threshold: float | None = None
    description: str
