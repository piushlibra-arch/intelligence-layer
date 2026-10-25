import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.session import SessionStatus
from app.schemas.features import FeatureSnapshotResponse
from app.schemas.interventions import InterventionDecisionResponse
from app.schemas.risk import RiskAssessmentResponse


class SessionCreateRequest(BaseModel):
    trader_id: uuid.UUID
    scenario_id: str | None = None
    is_synthetic: bool = True

class TradingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    trader_id: uuid.UUID
    scenario_id: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    status: SessionStatus
    peak_pnl: float
    current_pnl: float
    total_trades: int
    is_synthetic: bool

class SessionStateResponse(BaseModel):
    session: TradingSessionResponse
    current_pnl: float
    peak_pnl: float
    total_trades: int
    open_positions: int
    events_processed: int
    latest_risk: RiskAssessmentResponse | None = None
    latest_features: FeatureSnapshotResponse | None = None
    latest_intervention: InterventionDecisionResponse | None = None
