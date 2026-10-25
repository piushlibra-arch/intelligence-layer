import uuid
from pydantic import BaseModel, ConfigDict

class BaselineFeatureStats(BaseModel):
    avg_reentry_seconds: float | None = None
    avg_position_size: float | None = None
    avg_trade_frequency: float | None = None
    observations_reentry: int = 0
    observations_position: int = 0
    observations_frequency: int = 0

class BaselineInfoResponse(BaseModel):
    trader_id: uuid.UUID
    historical_sessions: int
    is_cold_start: bool
    baseline_version: str | None = None
    last_updated: str | None = None
    features: BaselineFeatureStats

class TraderProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    external_id: str
    display_name: str
    created_at: str
    default_position_limit: float
    daily_loss_limit: float
    is_synthetic: bool
