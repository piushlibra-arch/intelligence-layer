import hashlib
from datetime import datetime, timezone
from decimal import Decimal
import statistics
import uuid
from typing import NamedTuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import TradingSession, SessionStatus
from app.models.event import TradeEvent, EventType
from app.models.risk import ConfidenceLevel
from app.schemas.baselines import BaselineInfoResponse, BaselineFeatureStats

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class TraderBaseline(NamedTuple):
    trader_id: uuid.UUID
    historical_sessions_count: int
    confidence: ConfidenceLevel
    data_sufficiency: Decimal
    is_cold_start: bool
    baseline_version: str | None
    reentry_seconds: Decimal | None
    position_size: Decimal | None
    trade_frequency_per_30m: Decimal | None
    observations_reentry: int
    observations_position: int
    observations_frequency: int

class BaselineEngine:
    MIN_RELIABLE_SESSIONS = 5
    HIGH_CONFIDENCE_SESSIONS = 20

    @classmethod
    async def compute_baseline(
        cls,
        db: AsyncSession,
        trader_id: uuid.UUID,
        before_timestamp: datetime | None = None
    ) -> TraderBaseline:
        """
        Compute personal baseline from completed historical sessions.
        Strictly excludes any session active or starting after before_timestamp to avoid future leak.
        """
        query = select(TradingSession).where(
            TradingSession.trader_id == trader_id,
            TradingSession.status == SessionStatus.COMPLETED
        )
        if before_timestamp:
            query = query.where(TradingSession.started_at < before_timestamp)

        result = await db.execute(query.order_by(TradingSession.started_at.asc()))
        historical_sessions = list(result.scalars().all())

        count = len(historical_sessions)

        # Confidence determination
        if count == 0:
            confidence = ConfidenceLevel.INSUFFICIENT_DATA
            data_sufficiency = Decimal("0.05")
            is_cold_start = True
        elif count < cls.MIN_RELIABLE_SESSIONS:
            confidence = ConfidenceLevel.LOW
            data_sufficiency = Decimal(str(round(count / cls.MIN_RELIABLE_SESSIONS * 0.4, 2)))
            is_cold_start = False
        elif count < cls.HIGH_CONFIDENCE_SESSIONS:
            confidence = ConfidenceLevel.MEDIUM
            data_sufficiency = Decimal(str(round(0.4 + (count / cls.HIGH_CONFIDENCE_SESSIONS * 0.4), 2)))
            is_cold_start = False
        else:
            confidence = ConfidenceLevel.HIGH
            data_sufficiency = Decimal("1.00")
            is_cold_start = False

        if count == 0:
            return TraderBaseline(
                trader_id=trader_id,
                historical_sessions_count=0,
                confidence=confidence,
                data_sufficiency=data_sufficiency,
                is_cold_start=True,
                baseline_version=None,
                reentry_seconds=None,
                position_size=None,
                trade_frequency_per_30m=None,
                observations_reentry=0,
                observations_position=0,
                observations_frequency=0
            )

        # Gather session IDs for version hashing
        session_ids_str = ",".join(str(s.id) for s in historical_sessions)
        baseline_version = hashlib.sha256(session_ids_str.encode()).hexdigest()[:16]

        # Fetch events for these sessions
        hist_session_ids = [s.id for s in historical_sessions]
        events_query = select(TradeEvent).where(
            TradeEvent.session_id.in_(hist_session_ids)
        ).order_by(TradeEvent.timestamp.asc())
        events_result = await db.execute(events_query)
        all_events = list(events_result.scalars().all())

        # Group events by session
        session_events: dict[uuid.UUID, list[TradeEvent]] = {}
        for ev in all_events:
            session_events.setdefault(ev.session_id, []).append(ev)

        reentry_samples: list[float] = []
        position_samples: list[float] = []
        frequency_samples: list[float] = []

        for s_id, s_evs in session_events.items():
            # 1. Re-entry samples
            sorted_s_evs = sorted(s_evs, key=lambda x: ensure_utc(x.timestamp))
            for i, ev in enumerate(sorted_s_evs):
                if ev.event_type == EventType.TRADE_CLOSED and ev.realized_pnl is not None and ev.realized_pnl < Decimal("0.00"):
                    for next_ev in sorted_s_evs[i+1:]:
                        if next_ev.event_type == EventType.ORDER_SUBMITTED:
                            sec = (ensure_utc(next_ev.timestamp) - ensure_utc(ev.timestamp)).total_seconds()
                            if sec > 0:
                                reentry_samples.append(sec)
                            break

            # 2. Position size samples
            for ev in s_evs:
                if ev.event_type == EventType.ORDER_SUBMITTED and ev.quantity is not None:
                    position_samples.append(float(ev.quantity))

            # 3. Trade frequency in 30 min buckets
            orders = [e for e in s_evs if e.event_type == EventType.ORDER_SUBMITTED]
            frequency_samples.append(float(len(orders)))

        # Robust statistics (Median)
        median_reentry = Decimal(str(round(statistics.median(reentry_samples), 1))) if reentry_samples else None
        median_position = Decimal(str(round(statistics.median(position_samples), 1))) if position_samples else None
        median_frequency = Decimal(str(round(statistics.median(frequency_samples), 1))) if frequency_samples else None

        return TraderBaseline(
            trader_id=trader_id,
            historical_sessions_count=count,
            confidence=confidence,
            data_sufficiency=data_sufficiency,
            is_cold_start=False,
            baseline_version=baseline_version,
            reentry_seconds=median_reentry,
            position_size=median_position,
            trade_frequency_per_30m=median_frequency,
            observations_reentry=len(reentry_samples),
            observations_position=len(position_samples),
            observations_frequency=len(frequency_samples)
        )

    @classmethod
    def to_schema_response(cls, baseline: TraderBaseline) -> BaselineInfoResponse:
        return BaselineInfoResponse(
            trader_id=baseline.trader_id,
            historical_sessions=baseline.historical_sessions_count,
            is_cold_start=baseline.is_cold_start,
            baseline_version=baseline.baseline_version,
            last_updated=datetime.now().isoformat(),
            features=BaselineFeatureStats(
                avg_reentry_seconds=float(baseline.reentry_seconds) if baseline.reentry_seconds else None,
                avg_position_size=float(baseline.position_size) if baseline.position_size else None,
                avg_trade_frequency=float(baseline.trade_frequency_per_30m) if baseline.trade_frequency_per_30m else None,
                observations_reentry=baseline.observations_reentry,
                observations_position=baseline.observations_position,
                observations_frequency=baseline.observations_frequency
            )
        )
