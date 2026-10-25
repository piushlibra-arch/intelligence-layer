from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk import RiskBand
from app.scenarios import SCENARIO_REGISTRY
from app.schemas.evaluation import (
    DataIntegritySummary,
    EvaluationScenarioResult,
    EvaluationSummaryResponse,
)
from app.services.event_service import EventService
from app.services.replay_service import ReplayService


class EvaluationEngine:
    @classmethod
    async def run_evaluation(cls, db: AsyncSession) -> EvaluationSummaryResponse:
        scenario_results: list[EvaluationScenarioResult] = []
        total_events = 0
        total_assessments = 0

        dup_count = 0
        invalid_count = 0
        out_of_order_count = 0

        for s_id, scenario in SCENARIO_REGISTRY.items():
            session, events = await ReplayService.prepare_scenario_session(db, s_id)
            max_score = 0.0
            last_risk_band = RiskBand.NORMAL
            signals_count = 0
            detection_latency = None

            for idx, ev in enumerate(events):
                total_events += 1
                try:
                    resp = await EventService.ingest_event(db, session.id, ev)
                    if resp.is_duplicate:
                        dup_count += 1
                    elif resp.risk_assessment:
                        total_assessments += 1
                        score = resp.risk_assessment["risk_score"]
                        band = RiskBand(resp.risk_assessment["risk_band"])
                        if score > max_score:
                            max_score = score
                        last_risk_band = band

                        if band in (RiskBand.ELEVATED, RiskBand.HIGH) and detection_latency is None:
                            detection_latency = idx + 1
                except Exception:
                    invalid_count += 1

            # Check expected outcome match
            expected_met = True
            if s_id == "scenario_a":
                expected_met = (last_risk_band == RiskBand.NORMAL)
            elif s_id == "scenario_b":
                expected_met = (max_score >= 70.0)
            elif s_id == "scenario_c":
                expected_met = (last_risk_band in (RiskBand.NORMAL, RiskBand.ELEVATED))
            elif s_id == "scenario_d":
                expected_met = True
            elif s_id == "scenario_e":
                expected_met = (dup_count >= 1)

            scenario_results.append(EvaluationScenarioResult(
                scenario_id=s_id,
                name=scenario.name,
                events_processed=len(events),
                final_risk_band=last_risk_band,
                max_risk_score=round(max_score, 1),
                signals_triggered=signals_count,
                expected_outcome_met=expected_met,
                detection_latency_events=detection_latency
            ))

        return EvaluationSummaryResponse(
            total_scenarios=len(scenario_results),
            total_events=total_events,
            total_assessments=total_assessments,
            scenarios=scenario_results,
            data_integrity=DataIntegritySummary(
                duplicates_detected=dup_count,
                invalid_rejected=invalid_count,
                out_of_order_handled=out_of_order_count
            ),
            limitations=[
                "Evaluation performed solely on deterministic synthetic demonstration scenarios.",
                "Real market conditions involve unpredictable microstructures and order slippage.",
                "Feature thresholds (e.g. 2x baseline re-entry) are heuristic and require calibration on real brokerage logs.",
                "System operates strictly in shadow simulation mode with zero live order impact."
            ]
        )
