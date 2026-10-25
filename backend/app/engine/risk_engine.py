from decimal import Decimal
from typing import NamedTuple
from app.models.risk import RiskBand, ConfidenceLevel
from app.schemas.features import SignalResult
from app.engine.baseline_engine import TraderBaseline

class RiskAssessmentResult(NamedTuple):
    risk_score: Decimal
    risk_band: RiskBand
    triggered_signals: list[SignalResult]
    explanation: str
    confidence: ConfidenceLevel
    data_sufficiency: Decimal
    engine_version: str
    baseline_version: str | None

class RiskEngine:
    ENGINE_VERSION = "1.0.0"

    # Risk band thresholds
    NORMAL_MAX = Decimal("39.99")
    ELEVATED_MAX = Decimal("69.99")

    # Base weights for signals (summing to 100 on maximum severity)
    SIGNAL_WEIGHTS = {
        "post_loss_reentry": Decimal("25.0"),
        "position_size_escalation": Decimal("20.0"),
        "trade_frequency": Decimal("20.0"),
        "consecutive_losses": Decimal("15.0"),
        "profit_giveback": Decimal("15.0"),
        "combined_deviation": Decimal("5.0"),
    }

    SEVERITY_MULTIPLIER = {
        "low": Decimal("0.5"),
        "medium": Decimal("1.0"),
        "high": Decimal("1.4"),
    }

    @classmethod
    def evaluate_risk(
        cls,
        signals: list[SignalResult],
        baseline: TraderBaseline,
        configured_loss_limit: Decimal | None = None,
        current_pnl: Decimal | None = None
    ) -> RiskAssessmentResult:
        """
        Deterministic Risk Score Calculation:
        Score = clamp(sum(weight * severity_multiplier for active signals), 0, 100)
        """
        raw_score = Decimal("0.00")
        triggered_signals: list[SignalResult] = []
        explanation_lines: list[str] = []

        for sig in signals:
            if sig.triggered:
                triggered_signals.append(sig)
                weight = cls.SIGNAL_WEIGHTS.get(sig.name, Decimal("10.0"))
                multiplier = cls.SEVERITY_MULTIPLIER.get(sig.severity, Decimal("1.0"))
                contribution = (weight * multiplier).quantize(Decimal("0.01"))
                raw_score += contribution
                explanation_lines.append(f"• {sig.description} (+{contribution} pts)")

        # Factor in hard limits as distinct context in explanation
        if configured_loss_limit and current_pnl and current_pnl < Decimal("0.00"):
            loss_pct = (abs(current_pnl) / configured_loss_limit * Decimal("100.0")).quantize(Decimal("0.1"))
            if loss_pct >= Decimal("75.0"):
                raw_score += Decimal("10.00")
                explanation_lines.append(f"• Approaching daily loss limit: {loss_pct}% used of ₹{configured_loss_limit}")

        # Clamp between 0 and 100
        risk_score = min(max(raw_score, Decimal("0.00")), Decimal("100.00")).quantize(Decimal("0.01"))

        # Determine risk band
        if risk_score <= cls.NORMAL_MAX:
            risk_band = RiskBand.NORMAL
        elif risk_score <= cls.ELEVATED_MAX:
            risk_band = RiskBand.ELEVATED
        else:
            risk_band = RiskBand.HIGH

        # Construct explanation
        if not triggered_signals:
            explanation = "Normal trading activity. No behavioral risk escalation signals detected."
        else:
            header = f"Risk assessment: {risk_band.value.upper()} (score: {risk_score}/100)."
            body = "\n".join(explanation_lines)
            if baseline.is_cold_start:
                footer = "Note: Trader is in cold-start mode; assessment based on absolute rules without personalized baseline."
            else:
                footer = f"Evaluated against personal baseline v{baseline.baseline_version or '1'} from {baseline.historical_sessions_count} sessions."
            explanation = f"{header}\n{body}\n{footer}"

        return RiskAssessmentResult(
            risk_score=risk_score,
            risk_band=risk_band,
            triggered_signals=triggered_signals,
            explanation=explanation,
            confidence=baseline.confidence,
            data_sufficiency=baseline.data_sufficiency,
            engine_version=cls.ENGINE_VERSION,
            baseline_version=baseline.baseline_version
        )
