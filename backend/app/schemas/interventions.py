import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.intervention import ActionType


class InterventionDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    assessment_id: uuid.UUID
    session_id: uuid.UUID
    decided_at: datetime
    action_type: ActionType
    action_details: dict
    is_simulated: bool
    acknowledged: bool
    engine_version: str

class InterventionAcknowledgeRequest(BaseModel):
    acknowledged: bool = True
