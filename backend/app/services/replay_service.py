from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import EventType, ProcessingStatus, TradeEvent
from app.models.session import SessionStatus, TradingSession
from app.models.trader import TraderProfile
from app.scenarios import get_scenario
from app.schemas.events import EventIngestRequest


class ReplayService:
    @classmethod
    async def prepare_scenario_session(
        cls,
        db: AsyncSession,
        scenario_id: str
    ) -> tuple[TradingSession, list[EventIngestRequest]]:
        scenario = get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario '{scenario_id}' not found"
            )

        t_config = scenario.trader_config

        # 1. Find or create trader profile
        trader_q = select(TraderProfile).where(TraderProfile.external_id == t_config.external_id)
        trader_res = await db.execute(trader_q)
        trader = trader_res.scalar_one_or_none()

        if not trader:
            trader = TraderProfile(
                external_id=t_config.external_id,
                display_name=t_config.display_name,
                default_position_limit=t_config.default_position_limit,
                daily_loss_limit=t_config.daily_loss_limit,
                is_synthetic=True
            )
            db.add(trader)
            await db.flush()

            # 2. Seed historical sessions if needed for baseline
            if t_config.historical_sessions_count > 0:
                await cls._seed_historical_sessions(db, trader, t_config)

        # 3. Create fresh new session for this replay
        now = datetime.now(UTC)
        new_session = TradingSession(
            trader_id=trader.id,
            scenario_id=scenario_id,
            started_at=now,
            status=SessionStatus.ACTIVE,
            peak_pnl=Decimal("0.00"),
            current_pnl=Decimal("0.00"),
            total_trades=0,
            is_synthetic=True
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        # 4. Generate events with timestamps relative to now
        events = scenario.generate_events(base_time=now)
        # Prefix event_id with session_id prefix to ensure uniqueness across replay sessions
        session_prefix = str(new_session.id)[:8]
        unique_events = [
            e.model_copy(update={"event_id": f"{e.event_id}_{session_prefix}"})
            for e in events
        ]
        return new_session, unique_events

    @classmethod
    async def _seed_historical_sessions(
        cls,
        db: AsyncSession,
        trader: TraderProfile,
        config
    ):
        """Seed realistic completed historical sessions to establish baseline"""
        base_time = datetime.now(UTC) - timedelta(days=config.historical_sessions_count + 2)

        for i in range(config.historical_sessions_count):
            session_start = base_time + timedelta(days=i, hours=9, minutes=30)
            hist_session = TradingSession(
                trader_id=trader.id,
                scenario_id="historical_seed",
                started_at=session_start,
                ended_at=session_start + timedelta(hours=3),
                status=SessionStatus.COMPLETED,
                peak_pnl=Decimal("1500.00"),
                current_pnl=Decimal("1200.00"),
                total_trades=4,
                is_synthetic=True
            )
            db.add(hist_session)
            await db.flush()

            # Add trades matching config baseline
            reentry = config.baseline_reentry or Decimal("60.0")
            pos_size = config.baseline_position or Decimal("100.0")

            t_cur = session_start + timedelta(minutes=10)
            for trade_idx in range(4):
                # Order
                db.add(TradeEvent(
                    event_id=f"hist_{trader.external_id}_{i}_{trade_idx}_order",
                    source_id="historical_seed",
                    session_id=hist_session.id,
                    trader_id=trader.id,
                    event_type=EventType.ORDER_SUBMITTED,
                    instrument="NIFTY",
                    timestamp=t_cur,
                    side="BUY",
                    quantity=pos_size,
                    price=Decimal("22000.00"),
                    processing_status=ProcessingStatus.ACCEPTED
                ))
                t_cur += timedelta(minutes=5)
                # Close trade (alternate wins and losses)
                is_loss = (trade_idx % 2 == 1)
                pnl = Decimal("-500.00") if is_loss else Decimal("700.00")
                db.add(TradeEvent(
                    event_id=f"hist_{trader.external_id}_{i}_{trade_idx}_close",
                    source_id="historical_seed",
                    session_id=hist_session.id,
                    trader_id=trader.id,
                    event_type=EventType.TRADE_CLOSED,
                    instrument="NIFTY",
                    timestamp=t_cur,
                    side="SELL",
                    quantity=pos_size,
                    price=Decimal("22007.00") if not is_loss else Decimal("21995.00"),
                    realized_pnl=pnl,
                    processing_status=ProcessingStatus.ACCEPTED
                ))
                # Re-entry elapsed
                t_cur += timedelta(seconds=float(reentry))

        await db.flush()
