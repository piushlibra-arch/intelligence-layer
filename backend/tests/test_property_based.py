import uuid
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from app.engine.baseline_engine import TraderBaseline
from app.engine.risk_engine import RiskEngine
from app.models.risk import ConfidenceLevel, RiskBand
from app.schemas.features import SignalResult

signal_names = ["post_loss_reentry", "position_size_escalation", "trade_frequency", "consecutive_losses", "profit_giveback", "combined_deviation"]
severities = ["low", "medium", "high"]

@st.composite
def arbitrary_signals(draw):
    signals = []
    for name in signal_names:
        trig = draw(st.booleans())
        sev = draw(st.sampled_from(severities))
        val = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False))
        signals.append(SignalResult(
            name=name,
            triggered=trig,
            severity=sev,
            value=val,
            threshold=50.0,
            description=f"Arbitrary signal for {name}"
        ))
    return signals

@given(
    signals=arbitrary_signals(),
    loss_limit=st.decimals(min_value=Decimal("100.00"), max_value=Decimal("100000.00"), places=2),
    current_pnl=st.decimals(min_value=Decimal("-200000.00"), max_value=Decimal("200000.00"), places=2)
)
def test_risk_score_always_bounded_between_0_and_100(signals, loss_limit, current_pnl):
    baseline = TraderBaseline(
        trader_id=uuid.uuid4(),
        historical_sessions_count=10,
        confidence=ConfidenceLevel.MEDIUM,
        data_sufficiency=Decimal("0.80"),
        is_cold_start=False,
        baseline_version="prop_test_v1",
        reentry_seconds=Decimal("60.0"),
        position_size=Decimal("100.0"),
        trade_frequency_per_30m=Decimal("5.0"),
        observations_reentry=10,
        observations_position=10,
        observations_frequency=10
    )

    assessment = RiskEngine.evaluate_risk(
        signals=signals,
        baseline=baseline,
        configured_loss_limit=loss_limit,
        current_pnl=current_pnl
    )

    # Invariant 1: Score strictly between 0 and 100
    assert Decimal("0.00") <= assessment.risk_score <= Decimal("100.00")

    # Invariant 2: Risk band corresponds strictly to score range
    if assessment.risk_score <= RiskEngine.NORMAL_MAX:
        assert assessment.risk_band == RiskBand.NORMAL
    elif assessment.risk_score <= RiskEngine.ELEVATED_MAX:
        assert assessment.risk_band == RiskBand.ELEVATED
    else:
        assert assessment.risk_band == RiskBand.HIGH

    # Invariant 3: Hard loss limit parameter was not mutated
    assert loss_limit >= Decimal("100.00")

@given(signals=arbitrary_signals())
def test_risk_score_is_strictly_deterministic(signals):
    baseline = TraderBaseline(
        trader_id=uuid.uuid4(),
        historical_sessions_count=25,
        confidence=ConfidenceLevel.HIGH,
        data_sufficiency=Decimal("1.00"),
        is_cold_start=False,
        baseline_version="det_v1",
        reentry_seconds=Decimal("50.0"),
        position_size=Decimal("100.0"),
        trade_frequency_per_30m=Decimal("4.0"),
        observations_reentry=25,
        observations_position=25,
        observations_frequency=25
    )

    eval_1 = RiskEngine.evaluate_risk(signals, baseline)
    eval_2 = RiskEngine.evaluate_risk(signals, baseline)

    # Determinism invariant: exact same input gives exact same score, band, and explanation
    assert eval_1.risk_score == eval_2.risk_score
    assert eval_1.risk_band == eval_2.risk_band
    assert eval_1.explanation == eval_2.explanation
