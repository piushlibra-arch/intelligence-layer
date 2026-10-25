# Architecture Document — Adaptive Trader Risk Intelligence

## 1. System Overview

Adaptive Trader Risk Intelligence is an engineering prototype that analyses trading event sequences to identify potential risk escalation patterns. It operates entirely in simulation mode using synthetic data.

### Design Principles
- **Transparency**: Every risk assessment is explainable and auditable
- **Determinism**: Same events + same engine version = same assessment
- **Safety**: Shadow mode only — no live order execution
- **Honesty**: No fabricated baselines, metrics, or outcomes

## 2. Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                     │
│  Overview │ Session Replay │ Baseline │ Interventions │ Eval  │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────┴────────────────────────────────────┐
│                    Nginx Reverse Proxy                         │
│              /api/* → backend   /* → frontend                 │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────┐
│                    FastAPI Backend                             │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Event    │  │ Feature  │  │ Risk     │  │ Interven │     │
│  │ Ingest   │→ │ Engine   │→ │ Scoring  │→ │ Policy   │     │
│  │ Service  │  │          │  │ Engine   │  │ Engine   │     │
│  └────┬─────┘  └──────────┘  └────┬─────┘  └────┬─────┘     │
│       │         ┌──────────┐      │              │           │
│       │         │ Baseline │      │              │           │
│       │         │ Engine   │──────┘              │           │
│       │         └──────────┘                     │           │
│       │         ┌──────────┐                     │           │
│       └────────→│ Audit    │←────────────────────┘           │
│                 │ Service  │                                  │
│                 └────┬─────┘                                  │
└──────────────────────┼───────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              │  PostgreSQL 16  │
              │  (Internal)     │
              └─────────────────┘
```

## 3. Event Flow

### Ingestion Pipeline

1. **Event arrives** via POST `/api/v1/sessions/{id}/events`
2. **Schema validation**: Pydantic validates required fields, types, and ranges
3. **Duplicate detection**: Check `event_id` uniqueness within source scope
4. **Ordering validation**: Verify timestamp is consistent with session timeline
5. **Persistence**: Store event with `processing_status` (accepted/rejected/quarantined)
6. **Feature calculation**: Compute all 6 behavioral features from ordered event sequence
7. **Baseline lookup**: Retrieve trader's personal baseline (or cold-start defaults)
8. **Risk scoring**: Generate deterministic score 0-100 with explanations
9. **Intervention policy**: Map score + signals + confidence to graduated response
10. **Audit recording**: Log the complete decision chain

### Event Types

| Event Type | Key Fields | Triggers Assessment |
|---|---|---|
| `session_started` | trader_id | Initializes session |
| `order_submitted` | instrument, side, quantity, price | Updates frequency |
| `order_filled` | quantity, price, fill details | Updates position |
| `trade_closed` | realized_pnl | Full re-assessment |
| `pnl_updated` | realized_pnl | Giveback check |
| `session_ended` | — | Final assessment |

## 4. Feature Calculations

### Feature 1: Post-Loss Re-entry Latency

**Formula**: `reentry_seconds = next_entry_timestamp - losing_close_timestamp`

**Deviation**: `deviation_ratio = baseline_median_seconds / reentry_seconds`

A ratio > 2.0 means the trader re-entered more than twice as fast as their usual pattern.

**Signal threshold**: `deviation_ratio > 2.0` (or absolute < 30 seconds if no baseline)

### Feature 2: Position Size Escalation

**Formula**: `escalation_ratio = current_quantity / baseline_median_quantity`

**Signal threshold**: `escalation_ratio > 1.5` or `limit_usage > 80%`

### Feature 3: Trade Frequency Escalation

**Formula**: Count of `order_submitted` events in rolling 30-minute window

**Deviation**: `frequency_ratio = current_count / baseline_median_count`

**Signal threshold**: `frequency_ratio > 2.0`

### Feature 4: Consecutive Loss Pattern

**Formula**: Count sequential `trade_closed` events with `realized_pnl < 0`

**Signal threshold**: `consecutive_losses >= 3`

### Feature 5: Profit Giveback

**Formula**: `giveback_pct = (peak_pnl - current_pnl) / peak_pnl * 100`

Only calculated when `peak_pnl > 0`. Uses realized P&L only.

**Signal threshold**: `giveback_pct > 50%`

### Feature 6: Combined Behavioral Deviation

**Formula**: Weighted sum of active signal strengths

| Signal | Weight |
|---|---|
| Post-loss re-entry | 0.25 |
| Position size | 0.20 |
| Trade frequency | 0.20 |
| Consecutive losses | 0.15 |
| Profit giveback | 0.15 |
| Combined (meta) | 0.05 |

**Signal threshold**: 3+ individual signals active simultaneously

**Limitation**: Correlated indicators (e.g., high frequency and fast re-entry) may overlap. The combined score does not attempt to decorrelate them — this is documented as a known limitation.

## 5. Baseline Mechanism

### Construction
- Uses **median** of historical observations (robust to outliers)
- Minimum 5 completed sessions for "reliable" status
- Only uses sessions completed **before** current session started (prevents future leak)

### Cold Start
- 0 sessions: `confidence = insufficient_data`, uses absolute thresholds only
- 1-4 sessions: `confidence = low`, uses available data with wider margins
- 5-19 sessions: `confidence = medium`
- 20+ sessions: `confidence = high`

### Update Rule
- Recalculated from all historical completed sessions (excluding current)
- `baseline_version` = hash of contributing session IDs
- Never silently changes trader-configured hard limits

## 6. Risk Score Methodology

### Score Range
0-100, deterministic, heuristic assessment of observable patterns.

**This is NOT**:
- A probability of financial loss
- A clinical or psychological score
- A prediction of trader behavior

### Risk Bands

| Band | Score Range | Meaning |
|---|---|---|
| Normal | 0-39 | No significant behavioral deviation detected |
| Elevated | 40-69 | One or more signals warrant monitoring |
| High | 70-100 | Multiple signals suggest potential risk escalation |

### Scoring Formula

```
base_score = 0
for each signal:
    if signal.triggered:
        contribution = signal.weight * signal.severity_multiplier * 100
        base_score += contribution
risk_score = clamp(base_score, 0, 100)
```

Severity multipliers range from 1.0 (at threshold) to 2.0 (far beyond threshold).

### Determinism Guarantee
Given identical:
- Ordered event sequence
- Engine version
- Baseline version

The same risk score and explanation are produced.

## 7. Intervention Policy

### Graduated Responses

| Risk Band | Confidence | Intervention |
|---|---|---|
| Normal | Any | Continue monitoring |
| Elevated | High/Medium | Display explanatory warning |
| Elevated | Low/Insufficient | Continue monitoring (insufficient evidence) |
| High | High | Offer voluntary cooldown |
| High | Medium | Display warning, recommend review |
| High | Low/Insufficient | Display warning with confidence caveat |

### Hard Limits
- Daily loss limits and position limits are **separate** from behavioral scoring
- The intelligence layer **never** overrides, disables, or changes hard limits
- All interventions are **simulated** in this prototype

## 8. Database Consistency

### Idempotent Ingestion
- `event_id` uniqueness enforced per source scope
- Duplicate events return 409 Conflict, not re-processed
- No double-counting of positions or P&L

### Event Ordering
- Events processed in timestamp order within a session
- Out-of-order events documented and handled per policy
- Late events flagged but processed if valid

### Traceability
Every `RiskAssessment` links to:
- `TradingSession`
- `BehaviouralFeatureSnapshot`
- `TradeEvent` (triggering event)

Every `InterventionDecision` links to:
- `RiskAssessment`
- `InterventionPolicy`

### Audit Trail
Complete `AuditRecord` for every state-changing operation with:
- Entity type and ID
- Action performed
- Timestamp
- Engine version
- Details payload

## 9. Security Boundaries

### Data Security
- All data is synthetic by default
- No real customer data required
- No brokerage credentials needed
- No live trading capability

### API Security
- State-changing endpoints require API key authentication
- Read endpoints open for dashboard access
- Input validation at API boundary via Pydantic
- Safe error responses (no stack traces in production)
- CORS restricted to configured origins
- Request size limits enforced

### Infrastructure Security
- PostgreSQL accessible only from internal Docker network
- Non-root containers where practical
- No secrets in source code or Docker images
- Environment variables for all configuration

## 10. Scaling Limitations

This prototype is designed for single-instance demonstration:
- Single PostgreSQL instance (no replication)
- Single backend process
- In-memory replay state (session-scoped)
- No horizontal scaling
- No message queue for event processing

### Production Considerations
For real-world deployment, consider:
- Event queue (Kafka/SQS) for reliable ingestion
- Read replicas for dashboard queries
- Horizontal backend scaling with shared state
- Real-time WebSocket for live updates
- Proper authentication (OAuth 2.0 / OIDC)
- Rate limiting per trader/session
- Encrypted data at rest
- Compliance with financial data regulations

## 11. Failure Handling

| Failure | Behavior |
|---|---|
| Database unavailable | API returns 503, health check fails |
| Invalid event | Returns 422 with validation details |
| Duplicate event | Returns 409, no state change |
| Feature calculation error | Assessment created with reduced confidence |
| Baseline unavailable | Falls back to absolute thresholds |
| Assessment engine error | Logged, audit recorded, error returned |

## 12. Disclaimer

This prototype demonstrates engineering capabilities. It has not been validated against real trading data. Synthetic evaluation results do not establish operational effectiveness. The risk-scoring methodology uses uncalibrated initial parameters. This system should not be used for actual trading decisions without extensive validation, regulatory review, and calibration against real-world data.
