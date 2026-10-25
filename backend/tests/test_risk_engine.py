from decimal import Decimal
import uuid
from app.models.risk import RiskBand, ConfidenceLevel
from app.models.intervention import ActionType
from app.schemas.features import SignalResult
from app.engine.baseline_engine import TraderBaseline
from app.engine.risk_engine import RiskEngine
from app.engine.intervention_engine import InterventionEngine

def test_risk_score_determinism_and_bands():
    baseline = TraderBaseline(
        trader_id=uuid.uuid4(),
        historical_sessions_count=20,
        confidence=ConfidenceLevel.HIGH,
        data_sufficiency=Decimal("1.00"),
        is_cold_start=False,
        baseline_version="abc123",
        reentry_seconds=Decimal("60.0"),
        position_size=Decimal("100.0"),
        trade_frequency_per_30m=Decimal("4.0"),
        observations_reentry=20,
        observations_position=20,
        observations_frequency=20
    )

    # All signals false -> score is 0 -> NORMAL
    no_signals = [
        SignalResult(name="post_loss_reentry", triggered=False, severity="low", value=60.0, threshold=30.0, description=""),
        SignalResult(name="position_size_escalation", triggered=False, severity="low", value=100.0, threshold=150.0, description=""),
    ]
    res1 = RiskEngine.evaluate_risk(no_signals, baseline)
    assert res1.risk_score == Decimal("0.00")
    assert res1.risk_band == RiskBand.NORMAL

    # Multiple high severity signals -> score >= 70 -> HIGH
    multi_signals = [
        SignalResult(name="post_loss_reentry", triggered=True, severity="high", value=15.0, threshold=30.0, description="Fast reentry"),
        SignalResult(name="position_size_escalation", triggered=True, severity="high", value=250.0, threshold=150.0, description="Size escalated"),
        SignalResult(name="trade_frequency", triggered=True, severity="high", value=10.0, threshold=6.0, description="Frequency"),
        SignalResult(name="consecutive_losses", triggered=True, severity="high", value=4.0, threshold=3.0, description="4 losses"),
    ]
    res2 = RiskEngine.evaluate_risk(multi_signals, baseline)
    assert res2.risk_score >= Decimal("70.00")
    assert res2.risk_band == RiskBand.HIGH

    # Determinism: evaluate again with exact same inputs
    res3 = RiskEngine.evaluate_risk(multi_signals, baseline)
    assert res2.risk_score == res3.risk_score
    assert res2.explanation == res3.explanation

def test_intervention_recommendation_graduated():
    # Normal risk -> MONITOR
    r1 = InterventionEngine.recommend_intervention(
        risk_band=RiskBand.NORMAL,
        risk_score=Decimal("15.0"),
        confidence=ConfidenceLevel.HIGH,
        current_pnl=Decimal("500.00")
    )
    assert r1.action_type == ActionType.MONITOR
    assert r1.is_simulated is True

    # Elevated risk with high confidence -> WARNING
    r2 = InterventionEngine.recommend_intervention(
        risk_band=RiskBand.ELEVATED,
        risk_score=Decimal("55.0"),
        confidence=ConfidenceLevel.HIGH,
        current_pnl=Decimal("-1000.00")
    )
    assert r2.action_type == ActionType.WARNING

    # High risk with high confidence -> COOLDOWN_OFFER
    r3 = InterventionEngine.recommend_intervention(
        risk_band=RiskBand.HIGH,
        risk_score=Decimal("85.0"),
        confidence=ConfidenceLevel.HIGH,
        current_pnl=Decimal("-2500.00")
    )
    assert r3.action_type == ActionType.COOLDOWN_OFFER

    # Hard loss limit reached -> SESSION_PROTECTION_SIMULATION
    r4 = InterventionEngine.recommend_intervention(
        risk_band=RiskBand.HIGH,
        risk_score=Decimal("80.0"),
        confidence=ConfidenceLevel.HIGH,
        current_pnl=Decimal("-5000.00"),
        daily_loss_limit=Decimal("5000.00")
    )
    assert r4.action_type == ActionType.SESSION_PROTECTION_SIMULATION
    assert r4.action_details.get("is_hard_limit_trigger") is True
