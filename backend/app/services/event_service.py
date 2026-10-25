from datetime import datetime, timezone
from decimal import Decimal
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.event import TradeEvent, EventType, ProcessingStatus
from app.models.session import TradingSession, SessionStatus
from app.models.trader import TraderProfile
from app.models.feature import BehaviouralFeatureSnapshot
from app.models.risk import RiskAssessment
from app.models.intervention import InterventionDecision
from app.schemas.events import EventIngestRequest, TradeEventResponse, EventIngestResponse
from app.engine.feature_engine import FeatureEngine
from app.engine.baseline_engine import BaselineEngine
from app.engine.risk_engine import RiskEngine
from app.engine.intervention_engine import InterventionEngine
from app.services.audit_service import AuditService

class EventService:
    @staticmethod
    async def ingest_event(
        db: AsyncSession,
        session_id: uuid.UUID,
        request: EventIngestRequest
    ) -> EventIngestResponse:
        # 1. Fetch Session and Trader
        session_query = select(TradingSession).where(TradingSession.id == session_id)
        session_res = await db.execute(session_query)
        trading_session = session_res.scalar_one_or_none()
        if not trading_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading session {session_id} not found"
            )

        trader_query = select(TraderProfile).where(TraderProfile.id == trading_session.trader_id)
        trader_res = await db.execute(trader_query)
        trader = trader_res.scalar_one_or_none()
        if not trader:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated trader profile not found"
            )

        # 2. Check for duplicate event
        dup_query = select(TradeEvent).where(
            TradeEvent.event_id == request.event_id,
            TradeEvent.source_id == request.source_id
        )
        dup_res = await db.execute(dup_query)
        existing_event = dup_res.scalar_one_or_none()

        if existing_event:
            # Idempotent response: return existing event without mutating session state
            return EventIngestResponse(
                event=TradeEventResponse.model_validate(existing_event),
                is_duplicate=True,
                risk_assessment=None,
                intervention=None
            )

        # 3. Create and persist TradeEvent
        new_event = TradeEvent(
            event_id=request.event_id,
            source_id=request.source_id,
            session_id=session_id,
            trader_id=trading_session.trader_id,
            event_type=request.event_type,
            instrument=request.instrument,
            timestamp=request.timestamp,
            ingested_at=datetime.now(timezone.utc),
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            realized_pnl=request.realized_pnl,
            unrealized_pnl=request.unrealized_pnl,
            schema_version=request.schema_version,
            payload=request.payload,
            is_duplicate=False,
            processing_status=ProcessingStatus.ACCEPTED
        )
        db.add(new_event)
        await db.flush()

        # 4. Update TradingSession financial metrics
        if request.event_type == EventType.TRADE_CLOSED and request.realized_pnl is not None:
            trading_session.current_pnl += request.realized_pnl
            if trading_session.current_pnl > trading_session.peak_pnl:
                trading_session.peak_pnl = trading_session.current_pnl
            trading_session.total_trades += 1
        elif request.event_type == EventType.SESSION_ENDED:
            trading_session.status = SessionStatus.COMPLETED
            trading_session.ended_at = request.timestamp

        await db.flush()

        # 5. Fetch all events for this session up to now to compute features
        all_events_q = select(TradeEvent).where(
            TradeEvent.session_id == session_id,
            TradeEvent.processing_status == ProcessingStatus.ACCEPTED
        ).order_by(TradeEvent.timestamp.asc())
        all_events_res = await db.execute(all_events_q)
        session_events = list(all_events_res.scalars().all())

        # 6. Retrieve trader baseline (strictly isolated before session started)
        baseline = await BaselineEngine.compute_baseline(
            db=db,
            trader_id=trading_session.trader_id,
            before_timestamp=trading_session.started_at
        )

        # 7. Compute Behavioural Features
        f_reentry = FeatureEngine.calculate_post_loss_reentry(
            events=session_events,
            baseline_seconds=baseline.reentry_seconds
        )
        f_size = FeatureEngine.calculate_position_size_escalation(
            current_quantity=request.quantity,
            baseline_quantity=baseline.position_size,
            configured_limit=trader.default_position_limit
        )
        f_freq = FeatureEngine.calculate_trade_frequency(
            events=session_events,
            window_minutes=30,
            baseline_frequency=baseline.trade_frequency_per_30m
        )
        f_losses = FeatureEngine.calculate_consecutive_losses(events=session_events)
        f_giveback = FeatureEngine.calculate_profit_giveback(
            peak_pnl=trading_session.peak_pnl,
            current_pnl=trading_session.current_pnl
        )

        signals_list = [
            f_reentry.signal,
            f_size.signal,
            f_freq.signal,
            f_losses.signal,
            f_giveback.signal
        ]
        f_comb = FeatureEngine.calculate_combined_deviation(signals_list)
        all_signals = signals_list + [f_comb.signal]

        # 8. Risk Assessment
        risk_res = RiskEngine.evaluate_risk(
            signals=all_signals,
            baseline=baseline,
            configured_loss_limit=trader.daily_loss_limit,
            current_pnl=trading_session.current_pnl
        )

        # 9. Intervention Recommendation
        intervention_res = InterventionEngine.recommend_intervention(
            risk_band=risk_res.risk_band,
            risk_score=risk_res.risk_score,
            confidence=risk_res.confidence,
            current_pnl=trading_session.current_pnl,
            daily_loss_limit=trader.daily_loss_limit
        )

        # 10. Persist Feature Snapshot
        feat_snap = BehaviouralFeatureSnapshot(
            session_id=session_id,
            trader_id=trading_session.trader_id,
            computed_at=datetime.now(timezone.utc),
            post_loss_reentry_seconds=f_reentry.reentry_seconds,
            baseline_reentry_seconds=f_reentry.baseline_seconds,
            position_size_current=f_size.current_quantity,
            position_size_baseline=f_size.baseline_quantity,
            position_size_limit=trader.default_position_limit,
            trade_frequency_current=f_freq.current_count,
            trade_frequency_baseline=f_freq.baseline_frequency,
            trade_frequency_window_minutes=f_freq.window_minutes,
            consecutive_losses=f_losses.consecutive_count,
            consecutive_loss_total=f_losses.cumulative_loss,
            peak_session_pnl=trading_session.peak_pnl,
            current_session_pnl=trading_session.current_pnl,
            profit_giveback_pct=f_giveback.giveback_pct,
            combined_deviation_score=f_comb.score,
            feature_version=FeatureEngine.FEATURE_VERSION
        )
        db.add(feat_snap)
        await db.flush()

        # 11. Persist Risk Assessment
        risk_assessment = RiskAssessment(
            session_id=session_id,
            trader_id=trading_session.trader_id,
            feature_snapshot_id=feat_snap.id,
            assessed_at=datetime.now(timezone.utc),
            risk_score=risk_res.risk_score,
            risk_band=risk_res.risk_band,
            triggered_signals=[sig.model_dump() for sig in risk_res.triggered_signals],
            explanation=risk_res.explanation,
            confidence=risk_res.confidence,
            data_sufficiency=risk_res.data_sufficiency,
            engine_version=risk_res.engine_version,
            baseline_version=risk_res.baseline_version,
            is_deterministic=True
        )
        db.add(risk_assessment)
        await db.flush()

        feat_snap.assessment_id = risk_assessment.id

        # 12. Persist Intervention Decision
        decision = InterventionDecision(
            assessment_id=risk_assessment.id,
            session_id=session_id,
            trader_id=trading_session.trader_id,
            decided_at=datetime.now(timezone.utc),
            action_type=intervention_res.action_type,
            action_details=intervention_res.action_details,
            is_simulated=intervention_res.is_simulated,
            acknowledged=False,
            engine_version=InterventionEngine.VERSION
        )
        db.add(decision)
        await db.flush()

        # 13. Audit Log
        await AuditService.log_record(
            db=db,
            entity_type="TradeEvent",
            entity_id=new_event.id,
            action="INGEST_EVENT",
            details={
                "event_type": new_event.event_type.value,
                "risk_score": float(risk_res.risk_score),
                "risk_band": risk_res.risk_band.value,
                "action_type": intervention_res.action_type.value
            }
        )
        await db.commit()

        return EventIngestResponse(
            event=TradeEventResponse.model_validate(new_event),
            is_duplicate=False,
            risk_assessment={
                "id": str(risk_assessment.id),
                "risk_score": float(risk_res.risk_score),
                "risk_band": risk_res.risk_band.value,
                "explanation": risk_res.explanation,
                "confidence": risk_res.confidence.value
            },
            intervention={
                "id": str(decision.id),
                "action_type": intervention_res.action_type.value,
                "details": intervention_res.action_details
            }
        )
