from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import require_api_key
from app.database import get_db
from app.scenarios import get_scenario, list_scenarios
from app.schemas.evaluation import ScenarioMetadata
from app.services.replay_service import ReplayService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

@router.get("", response_model=list[ScenarioMetadata])
async def get_all_scenarios():
    return list_scenarios()

@router.get("/{scenario_id}", response_model=ScenarioMetadata)
async def get_scenario_by_id(scenario_id: str):
    s = get_scenario(scenario_id)
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    evs = s.generate_events()
    return ScenarioMetadata(
        id=s.scenario_id,
        name=s.name,
        description=s.description,
        trader_name=s.trader_config.display_name,
        expected_outcome=s.expected_outcome,
        event_count=len(evs)
    )

@router.post("/{scenario_id}/replay")
async def start_scenario_replay(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    _api_key: str = Depends(require_api_key)
):
    session, events = await ReplayService.prepare_scenario_session(db, scenario_id)
    return {
        "session_id": str(session.id),
        "scenario_id": scenario_id,
        "trader_id": str(session.trader_id),
        "total_events": len(events),
        "events": [e.model_dump() for e in events]
    }
