from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.models.event import EventType
from app.schemas.events import EventIngestRequest
from app.scenarios.base import BaseScenario, ScenarioTraderConfig

class DataIntegrityScenario(BaseScenario):
    @property
    def scenario_id(self) -> str:
        return "scenario_e"

    @property
    def name(self) -> str:
        return "Data Integrity & Fault Injection Test"

    @property
    def description(self) -> str:
        return "Stress test evaluating duplicate event rejection, idempotent processing, out-of-order handling, and partial fills."

    @property
    def expected_outcome(self) -> str:
        return "Duplicate events return idempotent response without double-counting P&L. System maintains state integrity."

    @property
    def trader_config(self) -> ScenarioTraderConfig:
        return ScenarioTraderConfig(
            external_id="trader_system_audit",
            display_name="System Auditor",
            historical_sessions_count=10,
            default_position_limit=Decimal("500.00"),
            daily_loss_limit=Decimal("5000.00"),
            baseline_reentry=Decimal("45.0"),
            baseline_position=Decimal("100.0"),
            baseline_frequency=Decimal("5.0")
        )

    def generate_events(self, base_time: datetime | None = None) -> list[EventIngestRequest]:
        t0 = base_time or datetime.now(timezone.utc) - timedelta(minutes=20)
        events: list[EventIngestRequest] = []

        # 1. Session start
        events.append(EventIngestRequest(
            event_id="stress_ev_01",
            event_type=EventType.SESSION_STARTED,
            instrument="NIFTY",
            timestamp=t0,
            source_id="synthetic_sim"
        ))

        # 2. Normal order
        events.append(EventIngestRequest(
            event_id="stress_ev_02",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=2),
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("22000.0"),
            source_id="synthetic_sim"
        ))

        # 3. Partial fill
        events.append(EventIngestRequest(
            event_id="stress_ev_03",
            event_type=EventType.ORDER_PARTIALLY_FILLED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=2, seconds=5),
            side="BUY",
            quantity=Decimal("50.0"),
            price=Decimal("22000.0"),
            source_id="synthetic_sim"
        ))

        # 4. Remaining fill
        events.append(EventIngestRequest(
            event_id="stress_ev_04",
            event_type=EventType.ORDER_FILLED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=2, seconds=10),
            side="BUY",
            quantity=Decimal("50.0"),
            price=Decimal("22000.0"),
            source_id="synthetic_sim"
        ))

        # 5. Closed trade
        events.append(EventIngestRequest(
            event_id="stress_ev_05",
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=5),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("22010.0"),
            realized_pnl=Decimal("1000.00"),
            source_id="synthetic_sim"
        ))

        # 6. DUPLICATE OF EVENT 5 (Identical event_id and source_id)
        events.append(EventIngestRequest(
            event_id="stress_ev_05",  # Duplicate!
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=5),
            side="SELL",
            quantity=Decimal("100.0"),
            price=Decimal("22010.0"),
            realized_pnl=Decimal("1000.00"),
            source_id="synthetic_sim"
        ))

        # 7. Out-of-order timestamp event (timestamp earlier than previous)
        events.append(EventIngestRequest(
            event_id="stress_ev_06",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=4),  # Before event 5
            side="BUY",
            quantity=Decimal("100.0"),
            price=Decimal("22005.0"),
            source_id="synthetic_sim"
        ))

        # 8. Session end
        events.append(EventIngestRequest(
            event_id="stress_ev_07",
            event_type=EventType.SESSION_ENDED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=10),
            source_id="synthetic_sim"
        ))

        return events
