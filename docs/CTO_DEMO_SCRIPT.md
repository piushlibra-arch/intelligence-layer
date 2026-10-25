# CTO Demonstration Script — Adaptive Trader Risk Intelligence

**Duration**: 5 minutes
**Audience**: CTO of Raise Financial Services (Dhan)
**Format**: Live demo with running application

---

## Opening (30 seconds)

> "This prototype explores whether explainable, personalized risk detection can identify potentially harmful trading patterns earlier than fixed thresholds alone. It sits above your existing risk controls — it never overrides hard limits or executes trades. Everything you'll see runs on synthetic data in simulation mode."

---

## Demo 1: Normal Loss — No False Alert (60 seconds)

**Navigate to**: Session Replay → Select "Normal Trading" scenario

**Action**: Click Play, let events process

**Talk track**:
> "Watch Alex Chen — an experienced trader with 25 sessions of history. He takes a losing trade. The system records the loss, but notice the risk score stays in the green 'Normal' band. One loss isn't evidence of a problem. The explanation panel says 'Single loss within normal parameters — no behavioral deviation detected.' This is important: we don't want to cry wolf every time a trader has a bad trade."

**Key point**: The system doesn't assume one loss = risk.

---

## Demo 2: Escalating Risk — Real Detection (90 seconds)

**Navigate to**: Session Replay → Select "Escalating Risk After Losses"

**Action**: Click Play, point to key moments

**Talk track**:
> "Now watch Jordan Rivera. After a loss, they re-enter a position 3x faster than their personal baseline. The risk ticks up to 'Elevated.' Then they increase position size — 2x their usual. Another loss. Trading frequency spikes. Look at the feature panel — four signals are now active."

**Pause at high-risk point**:
> "The score hits 'High.' The explanation is specific: 'Re-entry latency 15 seconds vs baseline 48 seconds. Position size 200 shares vs baseline 100. 4 consecutive losses totaling -$2,400.' The system recommends a voluntary cooldown — not a forced lockout, not a vague warning. The trader sees exactly why."

**Key point**: Multiple converging signals, not a single magic number.

---

## Demo 3: The False Positive Challenge (45 seconds)

**Navigate to**: Session Replay → Select "Legitimate High-Frequency Trader"

**Action**: Click Play

**Talk track**:
> "Sam Nakamura trades rapidly — that's their style. They have 30 sessions of history at high frequency. Watch: despite rapid trading and mixed results, the score stays Normal. Because the baseline captures their natural pattern. If we only used absolute thresholds, Sam would trigger alerts every session. Personalization reduces false positives."

**Pause**:
> "I won't promise zero false positives — that's dishonest. But personalized baselines are measurably better than one-size-fits-all."

---

## Demo 4: Audit & Data Integrity (30 seconds)

**Navigate to**: Intervention History page, then mention Data Integrity

**Talk track**:
> "Every risk decision is recorded with full context — the score, the signals, the baseline version, the engine version. If regulators or compliance asks 'why did you show this warning?', every decision is traceable. We also handle duplicate events, out-of-order data, and invalid payloads — the data integrity tests verify this."

---

## Demo 5: Evaluation — Honest Metrics (30 seconds)

**Navigate to**: Evaluation page

**Talk track**:
> "These metrics come from our synthetic test scenarios — not production data. We show sample sizes. We separate what's measured from what's assumed. The business impact calculator is clearly labeled 'illustrative.' We won't claim improved retention until we have real data to prove it."

---

## Closing (30 seconds)

> "This is an engineering prototype built in [timeframe]. It demonstrates that personalized behavioral risk detection is technically feasible and explainable. Before production integration, we'd need: calibration against real anonymized trading data, A/B testing against current controls, regulatory review of intervention types, and integration with Dhan's event pipeline. I'm happy to discuss the technical architecture and next steps."

---

## Anticipated CTO Questions

### Q: "How does this differ from our existing risk controls?"
**A**: Your existing controls use fixed thresholds (max loss, max position size). This layer adds personalized behavioral analysis — it detects *changes* in a trader's pattern, not just absolute limits. It's additive, not replacement.

### Q: "What's the false positive rate?"
**A**: On synthetic data, we can characterize it, but that's not the same as real-world performance. The high-frequency trader scenario demonstrates that personalization reduces false positives vs. absolute thresholds. Real calibration requires real data.

### Q: "Can this block trades?"
**A**: Not in this prototype, and that's by design. The recommendations are graduated — from monitoring to warnings to voluntary cooldowns. The most severe intervention is a *simulated* session protection. Whether to actually restrict trading is a product and regulatory decision, not something we'd automate without extensive validation.

### Q: "How would this integrate with Dhan?"
**A**: Through an event stream. Dhan's order management system would publish trade events to a queue. Our service consumes them, calculates risk, and publishes recommendations back. The intervention display integrates into the existing trading interface. No changes to order execution.

### Q: "What's the tech stack?"
**A**: Python/FastAPI backend, React/TypeScript frontend, PostgreSQL, Docker. Designed for simplicity and auditability. No ML models — deterministic rules with transparent weights. This makes it easier to explain to regulators and to debug.

### Q: "How long to production?"
**A**: The prototype validates the approach. Production requires: (1) integration with Dhan's event pipeline, (2) calibration with anonymized historical data, (3) A/B testing framework, (4) compliance review, (5) gradual rollout. Estimate: 3-4 months for a shadow-mode pilot with real data, if prioritized.

### Q: "What about latency?"
**A**: Current prototype processes events synchronously — adequate for near-real-time shadow mode. For production latency requirements under 100ms, we'd use an event queue and async processing. The risk engine itself runs in single-digit milliseconds.

---

## Technical Decisions & Trade-offs

| Decision | Rationale | Trade-off |
|---|---|---|
| Deterministic rules over ML | Explainability, auditability, no training data needed | Less adaptive to novel patterns |
| Median baselines | Robust to outliers | Less sensitive to trend changes |
| Session-scoped assessment | Clear boundaries, simpler state | Misses cross-session patterns |
| Shadow mode only | Safety first, regulatory compliance | Can't demonstrate real intervention |
| PostgreSQL over event store | Familiar, reliable, good for prototype | May need event store at scale |
| API key auth | Simple for prototype | Need OAuth/OIDC for production |
