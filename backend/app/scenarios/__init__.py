from app.scenarios.base import BaseScenario
from app.scenarios.cold_start import ColdStartScenario
from app.scenarios.data_integrity import DataIntegrityScenario
from app.scenarios.escalating_risk import EscalatingRiskScenario
from app.scenarios.high_frequency import HighFrequencyScenario
from app.scenarios.normal_trading import NormalTradingScenario
from app.schemas.evaluation import ScenarioMetadata

SCENARIO_REGISTRY: dict[str, BaseScenario] = {
    "scenario_a": NormalTradingScenario(),
    "scenario_b": EscalatingRiskScenario(),
    "scenario_c": HighFrequencyScenario(),
    "scenario_d": ColdStartScenario(),
    "scenario_e": DataIntegrityScenario(),
}

def get_scenario(scenario_id: str) -> BaseScenario | None:
    return SCENARIO_REGISTRY.get(scenario_id)

def list_scenarios() -> list[ScenarioMetadata]:
    result = []
    for s_id, s in SCENARIO_REGISTRY.items():
        evs = s.generate_events()
        result.append(ScenarioMetadata(
            id=s.scenario_id,
            name=s.name,
            description=s.description,
            trader_name=s.trader_config.display_name,
            expected_outcome=s.expected_outcome,
            event_count=len(evs)
        ))
    return result
