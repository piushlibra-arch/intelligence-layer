import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import ProcessingStatus, TradeEvent
from app.models.feature import BehaviouralFeatureSnapshot
from app.models.intervention import InterventionDecision
from app.models.risk import RiskAssessment
from app.models.session import SessionStatus, TradingSession
from app.models.trader import TraderProfile
from app.schemas.features import FeatureSnapshotResponse, SignalResult
from app.schemas.interventions import InterventionDecisionResponse
from app.schemas.risk import RiskAssessmentResponse
from app.schemas.sessions import SessionStateResponse, TradingSessionResponse


class SessionService:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        trader_id: uuid.UUID,
        scenario_id: str | None = None,
        is_synthetic: bool = True
    ) -> TradingSessionResponse:
        trader_q = select(TraderProfile).where(TraderProfile.id == trader_id)
        trader_res = await db.execute(trader_q)
        if not trader_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trader {trader_id} not found"
            )

        new_session = TradingSession(
            trader_id=trader_id,
            scenario_id=scenario_id,
            status=SessionStatus.ACTIVE,
            peak_pnl=Decimal("0.00"),
            current_pnl=Decimal("0.00"),
            total_trades=0,
            is_synthetic=is_synthetic
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return TradingSessionResponse.model_validate(new_session)

    @staticmethod
    async def get_session_state(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> SessionStateResponse:
        session_q = select(TradingSession).where(TradingSession.id == session_id)
        session_res = await db.execute(session_q)
        session = session_res.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        # Count events
        events_q = select(TradeEvent).where(
            TradeEvent.session_id == session_id,
            TradeEvent.processing_status == ProcessingStatus.ACCEPTED
        )
        events_res = await db.execute(events_q)
        events = list(events_res.scalars().all())

        # Latest feature snapshot
        feat_q = select(BehaviouralFeatureSnapshot).where(
            BehaviouralFeatureSnapshot.session_id == session_id
        ).order_by(BehaviouralFeatureSnapshot.computed_at.desc()).limit(1)
        feat_res = await db.execute(feat_q)
        latest_feat = feat_res.scalar_one_or_none()

        # Latest risk assessment
        risk_q = select(RiskAssessment).where(
            RiskAssessment.session_id == session_id
        ).order_by(RiskAssessment.assessed_at.desc()).limit(1)
        risk_res = await db.execute(risk_q)
        latest_risk = risk_res.scalar_one_or_none()

        # Latest intervention
        interv_q = select(InterventionDecision).where(
            InterventionDecision.session_id == session_id
        ).order_by(InterventionDecision.decided_at.desc()).limit(1)
        interv_res = await db.execute(interv_q)
        latest_interv = interv_res.scalar_one_or_none()

        latest_risk_resp = None
        if latest_risk:
            signals = [SignalResult(**s) for s in latest_risk.triggered_signals]
            latest_risk_resp = RiskAssessmentResponse(
                id=latest_risk.id,
                session_id=latest_risk.session_id,
                assessed_at=latest_risk.assessed_at,
                risk_score=float(latest_risk.risk_score),
                risk_band=latest_risk.risk_band,
                triggered_signals=signals,
                explanation=latest_risk.explanation,
                confidence=latest_risk.confidence,
                data_sufficiency=float(latest_risk.data_sufficiency),
                engine_version=latest_risk.engine_version,
                baseline_version=latest_risk.baseline_version
            )

        latest_feat_resp = None
        if latest_feat:
            latest_feat_resp = FeatureSnapshotResponse.model_validate(latest_feat)

        latest_interv_resp = None
        if latest_interv:
            latest_interv_resp = InterventionDecisionResponse.model_validate(latest_interv)

        return SessionStateResponse(
            session=TradingSessionResponse.model_validate(session),
            current_pnl=float(session.current_pnl),
            peak_pnl=float(session.peak_pnl),
            total_trades=session.total_trades,
            open_positions=0,
            events_processed=len(events),
            latest_risk=latest_risk_resp,
            latest_features=latest_feat_resp,
            latest_intervention=latest_interv_resp
        )
