from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.risk import RiskBand, ConfidenceLevel
from app.schemas.features import SignalResult

class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    assessed_at: datetime
    risk_score: float
    risk_band: RiskBand
    triggered_signals: list[SignalResult]
    explanation: str
    confidence: ConfidenceLevel
    data_sufficiency: float
    engine_version: str
    baseline_version: str | None = None
