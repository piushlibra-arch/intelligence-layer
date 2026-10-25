from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid
import pytest
from app.models.event import TradeEvent, EventType, ProcessingStatus
from app.engine.feature_engine import FeatureEngine
from app.schemas.features import SignalResult

def make_event(ev_type: EventType, ts: datetime, pnl: Decimal | None = None, qty: Decimal | None = None) -> TradeEvent:
    return TradeEvent(
        id=uuid.uuid4(),
        event_id=str(uuid.uuid4()),
        source_id="test",
        session_id=uuid.uuid4(),
        trader_id=uuid.uuid4(),
        event_type=ev_type,
        instrument="NIFTY",
        timestamp=ts,
        side="BUY",
        quantity=qty or Decimal("100.0"),
        price=Decimal("22000.0"),
        realized_pnl=pnl,
        processing_status=ProcessingStatus.ACCEPTED
    )

def test_post_loss_reentry_calculation():
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    # Loss at 10:05:00
    e1 = make_event(EventType.TRADE_CLOSED, t0 + timedelta(minutes=5), pnl=Decimal("-1000.00"))
    # Re-entry at 10:05:15 (15 seconds later)
    e2 = make_event(EventType.ORDER_SUBMITTED, t0 + timedelta(minutes=5, seconds=15))

    # Baseline is 60s -> ratio is 60 / 15 = 4x
    res = FeatureEngine.calculate_post_loss_reentry([e1, e2], baseline_seconds=Decimal("60.0"))
    assert res.reentry_seconds == Decimal("15.0")
    assert res.deviation_ratio == Decimal("4.00")
    assert res.signal.triggered is True
    assert res.signal.severity == "high"

def test_post_loss_reentry_normal():
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    e1 = make_event(EventType.TRADE_CLOSED, t0 + timedelta(minutes=5), pnl=Decimal("-1000.00"))
    e2 = make_event(EventType.ORDER_SUBMITTED, t0 + timedelta(minutes=6, seconds=30))  # 90s later

    # Baseline is 60s -> ratio 60/90 = 0.67x (slower than baseline)
    res = FeatureEngine.calculate_post_loss_reentry([e1, e2], baseline_seconds=Decimal("60.0"))
    assert res.signal.triggered is False

def test_position_size_escalation():
    # Baseline 100, Limit 500, Current 250 -> 2.5x baseline -> high severity
    res = FeatureEngine.calculate_position_size_escalation(
        current_quantity=Decimal("250.0"),
        baseline_quantity=Decimal("100.0"),
        configured_limit=Decimal("500.0")
    )
    assert res.escalation_ratio == Decimal("2.50")
    assert res.signal.triggered is True
    assert res.signal.severity == "high"

def test_position_size_normal():
    res = FeatureEngine.calculate_position_size_escalation(
        current_quantity=Decimal("100.0"),
        baseline_quantity=Decimal("100.0"),
        configured_limit=Decimal("500.0")
    )
    assert res.signal.triggered is False

def test_trade_frequency_escalation():
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    # 8 orders within 30 min window vs baseline of 3
    events = [
        make_event(EventType.ORDER_SUBMITTED, t0 + timedelta(minutes=i*3))
        for i in range(8)
    ]
    res = FeatureEngine.calculate_trade_frequency(events, window_minutes=30, baseline_frequency=Decimal("3.0"))
    assert res.current_count == 8
    assert res.frequency_ratio == Decimal("2.67")
    assert res.signal.triggered is True

def test_consecutive_losses():
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    events = [
        make_event(EventType.TRADE_CLOSED, t0 + timedelta(minutes=1), pnl=Decimal("500.00")),
        make_event(EventType.TRADE_CLOSED, t0 + timedelta(minutes=2), pnl=Decimal("-400.00")),
        make_event(EventType.TRADE_CLOSED, t0 + timedelta(minutes=3), pnl=Decimal("-600.00")),
        make_event(EventType.TRADE_CLOSED, t0 + timedelta(minutes=4), pnl=Decimal("-800.00")),
    ]
    res = FeatureEngine.calculate_consecutive_losses(events)
    assert res.consecutive_count == 3
    assert res.cumulative_loss == Decimal("-1800.00")
    assert res.signal.triggered is True

def test_profit_giveback():
    peak_pnl = Decimal("2000.00")
    current_pnl = Decimal("500.00")  # Drawdown of 1500 = 75% giveback
    res = FeatureEngine.calculate_profit_giveback(peak_pnl, current_pnl)
    assert res.giveback_pct == Decimal("75.00")
    assert res.signal.triggered is True
    assert res.signal.severity == "high"

def test_combined_deviation():
    sig1 = SignalResult(name="post_loss_reentry", triggered=True, severity="high", value=15.0, threshold=30.0, description="Fast reentry")
    sig2 = SignalResult(name="position_size_escalation", triggered=True, severity="medium", value=200.0, threshold=150.0, description="Size escalated")
    sig3 = SignalResult(name="trade_frequency", triggered=True, severity="medium", value=8.0, threshold=6.0, description="High frequency")
    sig4 = SignalResult(name="consecutive_losses", triggered=False, severity="low", value=1.0, threshold=3.0, description="1 loss")

    res = FeatureEngine.calculate_combined_deviation([sig1, sig2, sig3, sig4])
    assert res.active_signals_count == 3
    assert res.signal.triggered is True
    assert res.score >= Decimal("50.0")
