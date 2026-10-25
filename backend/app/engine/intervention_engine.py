from decimal import Decimal
from typing import NamedTuple

from app.models.intervention import ActionType
from app.models.risk import ConfidenceLevel, RiskBand


class InterventionResult(NamedTuple):
    action_type: ActionType
    action_details: dict
    is_simulated: bool
    policy_name: str

class InterventionEngine:
    VERSION = "1.0.0"

    @classmethod
    def recommend_intervention(
        cls,
        risk_band: RiskBand,
        risk_score: Decimal,
        confidence: ConfidenceLevel,
        current_pnl: Decimal,
        daily_loss_limit: Decimal | None = None
    ) -> InterventionResult:
        """
        Graduated intervention recommendation:
        - Never overrides broker hard limits
        - Always marked is_simulated=True
        - Explainable reasons for recommendation
        """
        # 1. Check if hard limit is breached or almost breached (informational simulation)
        if daily_loss_limit and current_pnl < Decimal("0.00") and abs(current_pnl) >= daily_loss_limit:
            return InterventionResult(
                action_type=ActionType.SESSION_PROTECTION_SIMULATION,
                action_details={
                    "headline": "Configured Daily Loss Limit Reached (Simulated)",
                    "message": f"Session loss of ₹{abs(current_pnl)} has reached configured limit of ₹{daily_loss_limit}. In production, broker hard rules apply.",
                    "recommended_action": "Simulate session trading lockout",
                    "reason": "Hard daily loss limit reached",
                    "is_hard_limit_trigger": True
                },
                is_simulated=True,
                policy_name="hard_limit_protection_policy"
            )

        # 2. Risk band + confidence graduated mapping
        if risk_band == RiskBand.NORMAL:
            return InterventionResult(
                action_type=ActionType.MONITOR,
                action_details={
                    "headline": "Active Monitoring",
                    "message": "Trading metrics remain within normal parameters. Continuing background monitoring.",
                    "recommended_action": "None required",
                    "reason": "Risk score is in normal range"
                },
                is_simulated=True,
                policy_name="standard_monitoring_policy"
            )

        if risk_band == RiskBand.ELEVATED:
            if confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
                return InterventionResult(
                    action_type=ActionType.WARNING,
                    action_details={
                        "headline": "Behavioral Risk Warning",
                        "message": f"Elevated trading pace or sizing detected (score: {risk_score}/100). Consider reviewing current session plan.",
                        "recommended_action": "Display in-app notification prompt",
                        "reason": "Observed behavioral deviations exceed historical baseline threshold"
                    },
                    is_simulated=True,
                    policy_name="elevated_warning_policy"
                )
            else:
                return InterventionResult(
                    action_type=ActionType.MONITOR,
                    action_details={
                        "headline": "Monitoring with Insufficient Baseline Data",
                        "message": f"Elevated activity observed (score: {risk_score}/100), but trader baseline history is limited. Monitoring without intrusive prompts.",
                        "recommended_action": "Log behavioral signal for future baseline calibration",
                        "reason": "Low confidence prevents premature user intervention"
                    },
                    is_simulated=True,
                    policy_name="provisional_monitoring_policy"
                )

        # High Risk Band
        if confidence == ConfidenceLevel.HIGH:
            return InterventionResult(
                action_type=ActionType.COOLDOWN_OFFER,
                action_details={
                    "headline": "Voluntary Cooldown Offer",
                    "message": f"High risk pattern detected across multiple behavioral signals (score: {risk_score}/100). Would you like to take a 15-minute voluntary timeout?",
                    "recommended_action": "Offer voluntary 15-minute cooldown prompt with decline option",
                    "cooldown_duration_minutes": 15,
                    "reason": "High-confidence multi-signal escalation detected"
                },
                is_simulated=True,
                policy_name="high_risk_cooldown_policy"
            )
        elif confidence == ConfidenceLevel.MEDIUM:
            return InterventionResult(
                action_type=ActionType.REVIEW_RECOMMENDATION,
                action_details={
                    "headline": "Risk Plan Review Recommended",
                    "message": f"High risk indicators detected (score: {risk_score}/100). We recommend pausing to review session loss and sizing guidelines.",
                    "recommended_action": "Present risk checklist prompt",
                    "reason": "Multi-signal escalation observed with moderate baseline confidence"
                },
                is_simulated=True,
                policy_name="risk_plan_review_policy"
            )
        else:
            # Low or Insufficient Data
            return InterventionResult(
                action_type=ActionType.WARNING,
                action_details={
                    "headline": "Advisory Risk Warning (Cold-Start / Low-Data)",
                    "message": f"High trading frequency and losses observed in short window (score: {risk_score}/100).",
                    "recommended_action": "Display subtle session pacing warning",
                    "reason": "Absolute threshold escalation in cold-start mode"
                },
                is_simulated=True,
                policy_name="cold_start_warning_policy"
            )
