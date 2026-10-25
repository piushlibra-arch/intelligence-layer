from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import NamedTuple
from app.models.event import TradeEvent, EventType
from app.schemas.features import SignalResult

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class PostLossReentryResult(NamedTuple):
    reentry_seconds: Decimal | None
    baseline_seconds: Decimal | None
    deviation_ratio: Decimal | None
    signal: SignalResult

class PositionSizeResult(NamedTuple):
    current_quantity: Decimal | None
    baseline_quantity: Decimal | None
    escalation_ratio: Decimal | None
    limit_usage_pct: Decimal | None
    signal: SignalResult

class TradeFrequencyResult(NamedTuple):
    current_count: int
    baseline_frequency: Decimal | None
    frequency_ratio: Decimal | None
    window_minutes: int
    signal: SignalResult

class ConsecutiveLossResult(NamedTuple):
    consecutive_count: int
    cumulative_loss: Decimal
    signal: SignalResult

class ProfitGivebackResult(NamedTuple):
    peak_pnl: Decimal
    current_pnl: Decimal
    giveback_pct: Decimal | None
    signal: SignalResult

class CombinedDeviationResult(NamedTuple):
    score: Decimal
    active_signals_count: int
    signal: SignalResult

class FeatureEngine:
    FEATURE_VERSION = "1.0.0"

    @staticmethod
    def calculate_post_loss_reentry(
        events: list[TradeEvent],
        baseline_seconds: Decimal | None = None
    ) -> PostLossReentryResult:
        """
        Feature 1: Post-loss re-entry latency
        Measures elapsed time between the most recent losing closed trade and the subsequent order submitted.
        Ratio = baseline_seconds / reentry_seconds.
        Triggered if deviation_ratio >= 2.0 (re-entered 2x faster than baseline),
        or if no baseline exists and reentry_seconds < 30.0s after a loss.
        """
        sorted_events = sorted(events, key=lambda e: ensure_utc(e.timestamp))
        last_losing_close: TradeEvent | None = None
        next_entry: TradeEvent | None = None

        for idx, ev in enumerate(sorted_events):
            if ev.event_type == EventType.TRADE_CLOSED and ev.realized_pnl is not None and ev.realized_pnl < Decimal("0.00"):
                last_losing_close = ev
                next_entry = None
                # look for subsequent entry
                for sub_ev in sorted_events[idx + 1:]:
                    if sub_ev.event_type == EventType.ORDER_SUBMITTED and ensure_utc(sub_ev.timestamp) >= ensure_utc(ev.timestamp):
                        next_entry = sub_ev
                        break

        if not last_losing_close or not next_entry:
            return PostLossReentryResult(
                reentry_seconds=None,
                baseline_seconds=baseline_seconds,
                deviation_ratio=None,
                signal=SignalResult(
                    name="post_loss_reentry",
                    triggered=False,
                    severity="low",
                    value=None,
                    threshold=float(baseline_seconds / Decimal("2.0")) if baseline_seconds else 30.0,
                    description="No post-loss re-entry observed"
                )
            )

        elapsed = Decimal(str((ensure_utc(next_entry.timestamp) - ensure_utc(last_losing_close.timestamp)).total_seconds()))
        reentry_seconds = max(elapsed, Decimal("0.1"))

        deviation_ratio = None
        triggered = False
        severity = "low"
        threshold = 2.0

        if baseline_seconds and baseline_seconds > Decimal("0.0"):
            deviation_ratio = (baseline_seconds / reentry_seconds).quantize(Decimal("0.01"))
            if deviation_ratio >= Decimal("2.0"):
                triggered = True
                severity = "high" if deviation_ratio >= Decimal("3.0") else "medium"
            desc = f"Re-entered in {reentry_seconds}s vs baseline {baseline_seconds}s (ratio {deviation_ratio}x)"
        else:
            # Cold-start / fallback rule: re-entry in under 30 seconds after loss
            threshold = 30.0
            triggered = reentry_seconds < Decimal("30.0")
            severity = "medium" if triggered else "low"
            desc = f"Re-entered in {reentry_seconds}s after loss (absolute threshold: 30s)"

        return PostLossReentryResult(
            reentry_seconds=reentry_seconds,
            baseline_seconds=baseline_seconds,
            deviation_ratio=deviation_ratio,
            signal=SignalResult(
                name="post_loss_reentry",
                triggered=triggered,
                severity=severity,
                value=float(reentry_seconds),
                threshold=threshold,
                description=desc
            )
        )

    @staticmethod
    def calculate_position_size_escalation(
        current_quantity: Decimal | None,
        baseline_quantity: Decimal | None = None,
        configured_limit: Decimal | None = None
    ) -> PositionSizeResult:
        """
        Feature 2: Position-size escalation
        Compares latest position or order quantity with historical baseline and configured limits.
        Triggered if escalation_ratio >= 1.5 or limit_usage >= 80%.
        """
        if current_quantity is None or current_quantity <= Decimal("0.0"):
            return PositionSizeResult(
                current_quantity=None,
                baseline_quantity=baseline_quantity,
                escalation_ratio=None,
                limit_usage_pct=None,
                signal=SignalResult(
                    name="position_size_escalation",
                    triggered=False,
                    severity="low",
                    value=None,
                    threshold=float(baseline_quantity * Decimal("1.5")) if baseline_quantity else None,
                    description="No active position size recorded"
                )
            )

        escalation_ratio = None
        limit_usage_pct = None
        triggered = False
        severity = "low"
        desc_parts = []

        if baseline_quantity and baseline_quantity > Decimal("0.0"):
            escalation_ratio = (current_quantity / baseline_quantity).quantize(Decimal("0.01"))
            if escalation_ratio >= Decimal("1.5"):
                triggered = True
                severity = "high" if escalation_ratio >= Decimal("2.0") else "medium"
                desc_parts.append(f"Size {current_quantity} is {escalation_ratio}x baseline {baseline_quantity}")

        if configured_limit and configured_limit > Decimal("0.0"):
            limit_usage_pct = ((current_quantity / configured_limit) * Decimal("100.0")).quantize(Decimal("0.1"))
            if limit_usage_pct >= Decimal("80.0"):
                triggered = True
                severity = "high" if limit_usage_pct >= Decimal("100.0") else max(severity, "medium")
                desc_parts.append(f"Limit usage at {limit_usage_pct}% of {configured_limit}")

        if not desc_parts:
            desc = f"Position size {current_quantity} within normal range"
        else:
            desc = "; ".join(desc_parts)

        return PositionSizeResult(
            current_quantity=current_quantity,
            baseline_quantity=baseline_quantity,
            escalation_ratio=escalation_ratio,
            limit_usage_pct=limit_usage_pct,
            signal=SignalResult(
                name="position_size_escalation",
                triggered=triggered,
                severity=severity,
                value=float(current_quantity),
                threshold=float(baseline_quantity * Decimal("1.5")) if baseline_quantity else (float(configured_limit * Decimal("0.8")) if configured_limit else None),
                description=desc
            )
        )

    @staticmethod
    def calculate_trade_frequency(
        events: list[TradeEvent],
        window_minutes: int = 30,
        baseline_frequency: Decimal | None = None
    ) -> TradeFrequencyResult:
        """
        Feature 3: Trade-frequency escalation
        Calculates qualifying entries over rolling 30-minute time window.
        Triggered if frequency_ratio >= 2.0 (or current >= 6 trades in 30 mins for cold start).
        """
        if not events:
            return TradeFrequencyResult(
                current_count=0,
                baseline_frequency=baseline_frequency,
                frequency_ratio=None,
                window_minutes=window_minutes,
                signal=SignalResult(
                    name="trade_frequency",
                    triggered=False,
                    severity="low",
                    value=0.0,
                    threshold=float(baseline_frequency * Decimal("2.0")) if baseline_frequency else 6.0,
                    description="No trades in window"
                )
            )

        latest_time = max(ensure_utc(e.timestamp) for e in events)
        window_start = latest_time - timedelta(minutes=window_minutes)

        entries_in_window = [
            e for e in events
            if e.event_type == EventType.ORDER_SUBMITTED and ensure_utc(e.timestamp) >= window_start
        ]
        count = len(entries_in_window)

        frequency_ratio = None
        triggered = False
        severity = "low"
        threshold = 6.0

        if baseline_frequency and baseline_frequency > Decimal("0.0"):
            frequency_ratio = (Decimal(str(count)) / baseline_frequency).quantize(Decimal("0.01"))
            threshold = float(baseline_frequency * Decimal("2.0"))
            if frequency_ratio >= Decimal("2.0"):
                triggered = True
                severity = "high" if frequency_ratio >= Decimal("3.0") else "medium"
            desc = f"{count} trades in {window_minutes}m vs baseline {baseline_frequency} ({frequency_ratio}x)"
        else:
            triggered = count >= 6
            severity = "medium" if triggered else "low"
            desc = f"{count} trades in {window_minutes}m (fallback threshold: 6)"

        return TradeFrequencyResult(
            current_count=count,
            baseline_frequency=baseline_frequency,
            frequency_ratio=frequency_ratio,
            window_minutes=window_minutes,
            signal=SignalResult(
                name="trade_frequency",
                triggered=triggered,
                severity=severity,
                value=float(count),
                threshold=threshold,
                description=desc
            )
        )

    @staticmethod
    def calculate_consecutive_losses(events: list[TradeEvent]) -> ConsecutiveLossResult:
        """
        Feature 4: Consecutive-loss pattern
        Counts consecutive losing trades closed up to the latest trade.
        Triggered if consecutive losses >= 3.
        """
        closed_trades = [
            e for e in sorted(events, key=lambda e: ensure_utc(e.timestamp))
            if e.event_type == EventType.TRADE_CLOSED and e.realized_pnl is not None
        ]

        consecutive = 0
        cumulative = Decimal("0.00")

        # Walk backward from the latest closed trade
        for trade in reversed(closed_trades):
            if trade.realized_pnl is not None and trade.realized_pnl < Decimal("0.00"):
                consecutive += 1
                cumulative += trade.realized_pnl
            else:
                break

        triggered = consecutive >= 3
        severity = "high" if consecutive >= 4 else ("medium" if triggered else "low")
        desc = f"{consecutive} consecutive losing trades (total P&L: ₹{cumulative})"

        return ConsecutiveLossResult(
            consecutive_count=consecutive,
            cumulative_loss=cumulative,
            signal=SignalResult(
                name="consecutive_losses",
                triggered=triggered,
                severity=severity,
                value=float(consecutive),
                threshold=3.0,
                description=desc
            )
        )

    @staticmethod
    def calculate_profit_giveback(
        peak_pnl: Decimal,
        current_pnl: Decimal
    ) -> ProfitGivebackResult:
        """
        Feature 5: Profit giveback
        Measures decline from peak realized session P&L.
        Only calculated when peak_pnl > 0.
        giveback_pct = (peak_pnl - current_pnl) / peak_pnl * 100
        Triggered if giveback_pct >= 50.0%.
        """
        if peak_pnl <= Decimal("0.00"):
            return ProfitGivebackResult(
                peak_pnl=peak_pnl,
                current_pnl=current_pnl,
                giveback_pct=None,
                signal=SignalResult(
                    name="profit_giveback",
                    triggered=False,
                    severity="low",
                    value=None,
                    threshold=50.0,
                    description="Session peak P&L is not positive; giveback not applicable"
                )
            )

        drawdown = peak_pnl - current_pnl
        if drawdown <= Decimal("0.00"):
            giveback_pct = Decimal("0.00")
        else:
            giveback_pct = ((drawdown / peak_pnl) * Decimal("100.0")).quantize(Decimal("0.01"))

        triggered = giveback_pct >= Decimal("50.00")
        severity = "high" if giveback_pct >= Decimal("75.00") else ("medium" if triggered else "low")
        desc = f"Gave back {giveback_pct}% of peak profit ₹{peak_pnl} (current: ₹{current_pnl})"

        return ProfitGivebackResult(
            peak_pnl=peak_pnl,
            current_pnl=current_pnl,
            giveback_pct=giveback_pct,
            signal=SignalResult(
                name="profit_giveback",
                triggered=triggered,
                severity=severity,
                value=float(giveback_pct),
                threshold=50.0,
                description=desc
            )
        )

    @staticmethod
    def calculate_combined_deviation(signals: list[SignalResult]) -> CombinedDeviationResult:
        """
        Feature 6: Combined behavioural deviation
        Weights:
        - post_loss_reentry: 0.25
        - position_size_escalation: 0.20
        - trade_frequency: 0.20
        - consecutive_losses: 0.15
        - profit_giveback: 0.15
        - meta/overlap: 0.05
        Triggered if 3+ individual signals are active simultaneously.
        """
        weights = {
            "post_loss_reentry": Decimal("0.25"),
            "position_size_escalation": Decimal("0.20"),
            "trade_frequency": Decimal("0.20"),
            "consecutive_losses": Decimal("0.15"),
            "profit_giveback": Decimal("0.15"),
        }

        severity_multiplier = {
            "low": Decimal("0.5"),
            "medium": Decimal("1.0"),
            "high": Decimal("1.5"),
        }

        active_count = 0
        weighted_score = Decimal("0.00")

        for sig in signals:
            if sig.name in weights and sig.triggered:
                active_count += 1
                base_w = weights[sig.name]
                mult = severity_multiplier.get(sig.severity, Decimal("1.0"))
                weighted_score += (base_w * mult * Decimal("100.0"))

        # Add multi-signal amplification if 3 or more signals are active
        if active_count >= 3:
            weighted_score += Decimal("10.0")

        clamped_score = min(max(weighted_score, Decimal("0.0")), Decimal("100.0")).quantize(Decimal("0.01"))
        triggered = active_count >= 3
        severity = "high" if active_count >= 4 else ("medium" if triggered else "low")
        desc = f"{active_count} concurrent risk signals active (combined score: {clamped_score})"

        return CombinedDeviationResult(
            score=clamped_score,
            active_signals_count=active_count,
            signal=SignalResult(
                name="combined_deviation",
                triggered=triggered,
                severity=severity,
                value=float(clamped_score),
                threshold=3.0,
                description=desc
            )
        )
