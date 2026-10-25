from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.event import EventType
from app.scenarios.base import BaseScenario, ScenarioTraderConfig
from app.schemas.events import EventIngestRequest


class ColdStartScenario(BaseScenario):
    @property
    def scenario_id(self) -> str:
        return "scenario_d"

    @property
    def name(self) -> str:
        return "Cold-Start Trader (No History)"

    @property
    def description(self) -> str:
        return "New trader with zero historical sessions. System flags insufficient history, uses absolute fallback rules, and avoids fabricating personal baselines."

    @property
    def expected_outcome(self) -> str:
        return "Confidence reports 'insufficient_data'. Personal baselines remain null. Absolute thresholds applied."

    @property
    def trader_config(self) -> ScenarioTraderConfig:
        return ScenarioTraderConfig(
            external_id="trader_taylor_kim",
            display_name="Taylor Kim",
            historical_sessions_count=0,             # 0 historical sessions
            default_position_limit=Decimal("300.00"),
            daily_loss_limit=Decimal("3000.00"),
            baseline_reentry=None,                  # No baseline
            baseline_position=None,
            baseline_frequency=None
        )

    def generate_events(self, base_time: datetime | None = None) -> list[EventIngestRequest]:
        t0 = base_time or datetime.now(UTC) - timedelta(minutes=25)
        events: list[EventIngestRequest] = []

        events.append(EventIngestRequest(
            event_id="cold_ev_01",
            event_type=EventType.SESSION_STARTED,
            instrument="NIFTY",
            timestamp=t0,
            source_id="synthetic_sim"
        ))

        # Trade 1
        events.append(EventIngestRequest(
            event_id="cold_ev_02",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=3),
            side="BUY",
            quantity=Decimal("50.0"),
            price=Decimal("22000.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="cold_ev_03",
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=7),
            side="SELL",
            quantity=Decimal("50.0"),
            price=Decimal("22010.0"),
            realized_pnl=Decimal("500.00"),
            source_id="synthetic_sim"
        ))

        # Trade 2: loss
        events.append(EventIngestRequest(
            event_id="cold_ev_04",
            event_type=EventType.ORDER_SUBMITTED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=12),
            side="BUY",
            quantity=Decimal("50.0"),
            price=Decimal("22015.0"),
            source_id="synthetic_sim"
        ))
        events.append(EventIngestRequest(
            event_id="cold_ev_05",
            event_type=EventType.TRADE_CLOSED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=16),
            side="SELL",
            quantity=Decimal("50.0"),
            price=Decimal("22005.0"),
            realized_pnl=Decimal("-500.00"),
            source_id="synthetic_sim"
        ))

        events.append(EventIngestRequest(
            event_id="cold_ev_06",
            event_type=EventType.SESSION_ENDED,
            instrument="NIFTY",
            timestamp=t0 + timedelta(minutes=20),
            source_id="synthetic_sim"
        ))

        return events
