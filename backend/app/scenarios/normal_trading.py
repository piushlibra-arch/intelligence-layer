from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.models.event import EventType
from app.schemas.events import EventIngestRequest
from app.scenarios.base import BaseScenario, ScenarioTraderConfig

class NormalTradingScenario(BaseScenario):
    @property
    def scenario_id(self) -> str:
        return "scenario_a"

    @property
    def name(self) -> str:
        return "Normal Trading Session"

    @property
    def description(self) -> str:
        return "Trader experiences an ordinary loss and subsequently places a trade consistent with established personal pattern. No alert triggered."

    @property
    def expected_outcome(self) -> str:
        return "Risk score remains in NORMAL band (0–39). Single loss does not infer risk escalation."

    @property
    def trader_config(self) -> ScenarioTraderConfig:
        return ScenarioTraderConfig(
            external_id="trader_alex_chen",
            display_name="Alex Chen",
            historical_sessions_count=25,
            default_position_limit=Decimal("500.00"),
            daily_loss_limit=Decimal("5000.00"),
            baseline_reentry=Decimal("65.0"),       # ~65s baseline reentry
            baseline_position=Decimal("100.0"),     # 100 shares baseline
            baseline_frequency=Decimal("4.0")       # 4 trades per 30m
        )

    def generate_events(self, base_time: datetime | None = None) -> list[EventIngestRequest]:
        t0 = base_time or datetime.now(timezone.utc) - timedelta(minutes=45)
        events: list[EventIngestRequest] = []

        # 1. Session Started
        events.append(EventIngestRequest(
            event_id="norm_ev_01",
            event_type=EventType.SESSION_STARTED,
            instrument="NIFTY",
            timestamp=t0,
            source_id="synthetic_sim"
        ))

        # 2. Trade 1: Normal Win (+₹1200)
        events.append(EventIngestRequest(
            event_id="norm_ev_02",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=5),
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("22000.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="norm_ev_03",
            event_type=EventType.ORDER_FILLED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=5, seconds=2),
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("22000.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="norm_ev_04",
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=15),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("22012.0"),
            realized_pnl=Decimal("1200.00"),
            source_id="synthetic_sim"
        ))

        # 3. Trade 2: Ordinary Loss (-₹800)
        events.append(EventIngestRequest(
            event_id="norm_ev_05",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=22),
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("22020.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="norm_ev_06",
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=28),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("22012.0"),
            realized_pnl=Decimal("-800.00"),
            source_id="synthetic_sim"
        ))

        # 4. Trade 3: Normal Post-loss Re-entry (waited ~70s, size is normal 100 shares)
        events.append(EventIngestRequest(
            event_id="norm_ev_07",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=29, seconds=10), # 70s after loss
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("22015.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="norm_ev_08",
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=36),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("22025.0"),
            realized_pnl=Decimal("1000.00"),
            source_id="synthetic_sim"
        ))

        # 5. Session End
        events.append(EventIngestRequest(
            event_id="norm_ev_09",
            event_type=EventType.SESSION_ENDED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=40),
            source_id="synthetic_sim"
        ))

        return events
