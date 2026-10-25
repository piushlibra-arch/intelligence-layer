from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.models.event import EventType
from app.schemas.events import EventIngestRequest
from app.scenarios.base import BaseScenario, ScenarioTraderConfig

class HighFrequencyScenario(BaseScenario):
    @property
    def scenario_id(self) -> str:
        return "scenario_c"

    @property
    def name(self) -> str:
        return "Legitimate High-Frequency Trader"

    @property
    def description(self) -> str:
        return "Trader normally executes high-frequency scalping strategies with rapid re-entry. System accounts for personal baseline and suppresses false alerts."

    @property
    def expected_outcome(self) -> str:
        return "Risk score remains in NORMAL band (0–39). Personalized baseline prevents false positive alert."

    @property
    def trader_config(self) -> ScenarioTraderConfig:
        return ScenarioTraderConfig(
            external_id="trader_sam_nakamura",
            display_name="Sam Nakamura",
            historical_sessions_count=30,
            default_position_limit=Decimal("500.00"),
            daily_loss_limit=Decimal("5000.00"),
            baseline_reentry=Decimal("15.0"),       # Normally re-enters in 15 seconds!
            baseline_position=Decimal("50.0"),      # 50 shares
            baseline_frequency=Decimal("12.0")      # 12 trades per 30m naturally
        )

    def generate_events(self, base_time: datetime | None = None) -> list[EventIngestRequest]:
        t0 = base_time or datetime.now(timezone.utc) - timedelta(minutes=30)
        events: list[EventIngestRequest] = []

        events.append(EventIngestRequest(
            event_id="hft_ev_01",
            event_type=EventType.SESSION_STARTED,
            instrument="FINNIFTY",
            timestamp=t0,
            source_id="synthetic_sim"
        ))

        # 6 rapid round-trip trades within 15 minutes, with 15s re-entries, 50 shares
        cur_t = t0 + timedelta(minutes=1)
        for i in range(1, 6):
            pnl = Decimal("300.00") if i % 2 == 1 else Decimal("-250.00")
            events.append(EventIngestRequest(
                event_id=f"hft_ev_order_{i}",
                event_type=EventType.ORDER_SUBMITTED,
                instrument="FINNIFTY",
                timestamp=cur_t,
                side="BUY",
                quantity=Decimal("50.0"),
                price=Decimal("21000.0"),
                source_id="synthetic_sim"
            ))
            cur_t += timedelta(seconds=20)
            events.append(EventIngestRequest(
                event_id=f"hft_ev_close_{i}",
                event_type=EventType.TRADE_CLOSED,
                instrument="FINNIFTY",
                timestamp=cur_t,
                side="SELL",
                quantity=Decimal("50.0"),
                price=Decimal("21005.0"),
                realized_pnl=pnl,
                source_id="synthetic_sim"
            ))
            # Re-entry happens 14-16s later, perfectly normal for this trader
            cur_t += timedelta(seconds=15)

        events.append(EventIngestRequest(
            event_id="hft_ev_end",
            event_type=EventType.SESSION_ENDED,
            instrument="FINNIFTY",
            timestamp=cur_t + timedelta(minutes=2),
            source_id="synthetic_sim"
        ))

        return events
