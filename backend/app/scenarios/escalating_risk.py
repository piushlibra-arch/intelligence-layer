from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.models.event import EventType
from app.schemas.events import EventIngestRequest
from app.scenarios.base import BaseScenario, ScenarioTraderConfig

class EscalatingRiskScenario(BaseScenario):
    @property
    def scenario_id(self) -> str:
        return "scenario_b"

    @property
    def name(self) -> str:
        return "Escalating Risk After Losses"

    @property
    def description(self) -> str:
        return "Trader experiences a loss followed by fast re-entry (3x faster), doubled position size, trade frequency spike, and profit giveback."

    @property
    def expected_outcome(self) -> str:
        return "Risk score transitions from NORMAL to ELEVATED to HIGH (>=70). Recommends voluntary cooldown."

    @property
    def trader_config(self) -> ScenarioTraderConfig:
        return ScenarioTraderConfig(
            external_id="trader_jordan_rivera",
            display_name="Jordan Rivera",
            historical_sessions_count=20,
            default_position_limit=Decimal("500.00"),
            daily_loss_limit=Decimal("5000.00"),
            baseline_reentry=Decimal("60.0"),       # 60s baseline
            baseline_position=Decimal("100.0"),     # 100 shares baseline
            baseline_frequency=Decimal("3.0")       # 3 trades per 30m
        )

    def generate_events(self, base_time: datetime | None = None) -> list[EventIngestRequest]:
        t0 = base_time or datetime.now(timezone.utc) - timedelta(minutes=60)
        events: list[EventIngestRequest] = []

        # 1. Session start
        events.append(EventIngestRequest(
            event_id="esc_ev_01",
            event_type=EventType.SESSION_STARTED,
            instrument="BANKNIFTY",
            timestamp=t0,
            source_id="synthetic_sim"
        ))

        # 2. Trade 1: Initial nice profit (+₹2500), baseline size 100
        events.append(EventIngestRequest(
            event_id="esc_ev_02",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=5),
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("48000.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="esc_ev_03",
            event_type=EventType.TRADE_CLOSED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=15),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("48025.0"),
            realized_pnl=Decimal("2500.00"),
            source_id="synthetic_sim"
        ))

        # 3. Trade 2: Loss 1 (-₹1500)
        events.append(EventIngestRequest(
            event_id="esc_ev_04",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=22),
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("48050.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="esc_ev_05",
            event_type=EventType.TRADE_CLOSED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=27),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("48035.0"),
            realized_pnl=Decimal("-1500.00"),
            source_id="synthetic_sim"
        ))

        # 4. Trade 3: Fast re-entry (15s after loss vs 60s baseline) & Escalated Size (200 shares = 2x baseline)
        events.append(EventIngestRequest(
            event_id="esc_ev_06",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=27, seconds=15),  # 15 seconds!
            side="BUY",
            quantity=Decimal("200.0"),                       # 2x size!
            price=Decimal("48030.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="esc_ev_07",
            event_type=EventType.TRADE_CLOSED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=31),
            side="SELL",
            quantity=Decimal("200.0"),
            price=Decimal("48020.0"),
            realized_pnl=Decimal("-2000.00"),               # Loss 2! Giveback now 140% of peak!
            source_id="synthetic_sim"
        ))

        # 5. Trade 4: Very fast re-entry (10s), escalated size (300 shares = 3x baseline), loss 3
        events.append(EventIngestRequest(
            event_id="esc_ev_08",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=31, seconds=10),  # 10s!
            side="BUY",
            quantity=Decimal("300.0"),                       # 3x size!
            price=Decimal("48010.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="esc_ev_09",
            event_type=EventType.TRADE_CLOSED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=34),
            side="SELL",
            quantity=Decimal("300.0"),
            price=Decimal("47990.0"),
            realized_pnl=Decimal("-2000.00"),               # Loss 3! (Consecutive losses = 3)
            source_id="synthetic_sim"
        ))

        # 6. Trade 5: High frequency spike (4th order within 10 minutes) & Loss 4
        events.append(EventIngestRequest(
            event_id="esc_ev_10",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=34, seconds=20),
            side="BUY",
            quantity=Decimal("350.0"),
            price=Decimal("47980.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="esc_ev_11",
            event_type=EventType.TRADE_CLOSED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=38),
            side="SELL",
            quantity=Decimal("350.0"),
            price=Decimal("47970.0"),
            realized_pnl=Decimal("-1500.00"),               # Loss 4!
            source_id="synthetic_sim"
        ))

        # Session end
        events.append(EventIngestRequest(
            event_id="esc_ev_12",
            event_type=EventType.SESSION_ENDED,
            instrument="BANKNIFTY",
            timestamp=t0 + timedelta(minutes=45),
            source_id="synthetic_sim"
        ))

        return events
