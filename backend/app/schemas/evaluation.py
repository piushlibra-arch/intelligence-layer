from datetime import datetime
import uuid
from pydantic import BaseModel
from app.models.risk import RiskBand

class EvaluationScenarioResult(BaseModel):
    scenario_id: str
    name: str
    events_processed: int
    final_risk_band: RiskBand
    max_risk_score: float
    signals_triggered: int
    expected_outcome_met: bool | None = None
    detection_latency_events: int | None = None

class DataIntegritySummary(BaseModel):
    duplicates_detected: int = 0
    invalid_rejected: int = 0
    out_of_order_handled: int = 0

class EvaluationSummaryResponse(BaseModel):
    total_scenarios: int
    total_events: int
    total_assessments: int
    scenarios: list[EvaluationScenarioResult]
    data_integrity: DataIntegritySummary
    limitations: list[str]

class ScenarioMetadata(BaseModel):
    id: str
    name: str
    description: str
    trader_name: str
    expected_outcome: str
    event_count: int
