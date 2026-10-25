# Adaptive Trader Risk Intelligence

**Explainable, Personalized Behavioral Risk Detection for Trading Platforms**

An engineering prototype developed for demonstration to quantitative systems architects and leadership at Raise Financial Services (Dhan).

---

## 1. Executive Summary

Traditional retail brokerage risk controls rely almost exclusively on predefined static thresholds:
- Daily max loss limit (e.g. stop trading at -₹5,000)
- Single-order quantity caps (e.g. max 500 shares)
- Trade count limits (e.g. max 20 orders per session)
- Manual or scheduled cool-off timeouts

While these protections are vital, they do not detect **changes in an individual trader's behaviour** until a catastrophic limit is already hit. 

**Adaptive Trader Risk Intelligence** analyses the sequence, timing, and sizing context of trading events to identify observable risk escalation patterns earlier than static limits alone.

### Crucial Safeguards & Shadow Mode
- **Shadow Mode Only**: The system operates completely in passive simulation. It does not execute, modify, cancel, or block live brokerage orders.
- **Additive, Not Replacement**: It sits above existing brokerage execution, P&L kill-switches, and margin checks without ever overriding them.
- **Explainable & Traceable**: Every risk decision provides plain-language contributing factors and exact metrics for regulatory and audit compliance.
- **Synthetic Data**: Powered by deterministic synthetic demonstration data. No live trader credentials or confidential Dhan customer records required.

---

## 2. Core Architecture & Event Flow

```
┌────────────────────────────────────────────────────────┐
│                   React 18 Dashboard                    │
│    Overview  │  Replay  │  Baselines  │  Audit  │ Eval │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────┴─────────────────────────────┐
│                 Nginx Reverse Proxy                    │
│           /api/* → backend   /* → SPA                  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│                   FastAPI Backend                      │
│                                                        │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ Event Ingest │──>│ Feature Eng  │──>│ Risk Score │  │
│  └──────────────┘   └──────┬───────┘   └─────┬──────┘  │
│                            │                 │         │
│                     ┌──────┴───────┐   ┌─────┴──────┐  │
│                     │ Baseline Eng │   │ Policy Eng │  │
│                     └──────────────┘   └─────┬──────┘  │
│                                              │         │
│                     ┌──────────────┐         │         │
│                     │ Audit Trail  │<────────┘         │
│                     └──────┬───────┘                   │
└────────────────────────────┼───────────────────────────┘
                             │
                      ┌──────┴──────┐
                      │  PostgreSQL │
                      │  (Internal) │
                      └─────────────┘
```

---

## 3. Behavioral Features Implemented

The engine calculates six distinct behavioral features from chronological event sequences:

| # | Feature | Formulation | Deviation & Trigger |
|---|---|---|---|
| **1** | **Post-Loss Re-entry Latency** | Elapsed seconds between a losing trade close and next order submission | $\text{Ratio} = \frac{\text{Baseline Latency}}{\text{Observed Latency}}$. Triggered if $\ge 2.0\times$ faster than normal (or $<30$s in cold-start). |
| **2** | **Position-Size Escalation** | Current order/position quantity vs. trader's baseline and limit | Triggered if quantity $\ge 1.5\times$ baseline or $\ge 80\%$ of configured position limit. |
| **3** | **Trade Frequency Spike** | Order submissions in a rolling 30-minute window | Triggered if count $\ge 2.0\times$ baseline frequency (or $\ge 6$ orders in cold-start). |
| **4** | **Consecutive Loss Pattern** | Sequential closed trades with negative realized P&L | Triggered if consecutive losses $\ge 3$. Computes cumulative loss ₹ drawdown. |
| **5** | **Profit Giveback** | Retracement from session peak realized P&L | $\text{Giveback \%} = \frac{\text{Peak PnL} - \text{Current PnL}}{\text{Peak PnL}} \times 100$. Triggered if $\ge 50\%$. |
| **6** | **Combined Deviation** | Weighted convergence across all 5 features | Weights: Re-entry (0.25), Size (0.20), Frequency (0.20), Losses (0.15), Giveback (0.15), Meta (0.05). Triggered if $\ge 3$ signals active. |

---

## 4. Personalized Baselines & Cold-Start Handling

To avoid false alarms on naturally high-frequency traders or scalpers, the system establishes a personal reference norm:
- **Sample Median**: Baselines use statistical medians across historical sessions, making them resilient against single-day outliers.
- **Data Isolation (No Leakage)**: Baselines strictly include sessions completed *prior* to current session start time.
- **Cold-Start Safeguard**: New traders with 0 historical sessions are flagged with `confidence: insufficient_data`. The engine explicitly avoids fabricating personal baselines and applies transparent absolute fallback guardrails.
- **Baseline Versioning**: Stored as a cryptographic hash of contributing session IDs for full audit reproducibility.

---

## 5. Demonstration Scenarios

| Scenario | Trader Profile | Historical Sessions | Expected Outcome |
|---|---|---|---|
| **Scenario A: Normal Trading** | Alex Chen | 25 sessions | Normal loss followed by ordinary re-entry. Score stays in **Normal (0–39)**. Proves the system does not cry wolf on standard losses. |
| **Scenario B: Escalating Risk** | Jordan Rivera | 20 sessions | Initial win (+₹2500) followed by 3x faster re-entry, 2x position size, 4 consecutive losses, and profit giveback. Transitions **Normal → Elevated → High (70–100)**. Recommends voluntary cooldown. |
| **Scenario C: High-Frequency Trader** | Sam Nakamura | 30 sessions | Rapid trading and quick re-entries matching trader's established style. Baseline suppresses false alerts; stays **Normal**. |
| **Scenario D: Cold-Start Trader** | Taylor Kim | 0 sessions | Reports `insufficient_data` confidence. Null personal baseline with documented absolute rules. |
| **Scenario E: Data Integrity Stress Test** | System Audit | 10 sessions | Injects duplicate event IDs, out-of-order timestamps, and partial fills. Verifies idempotent processing with zero double-counting. |

---

## 6. Local Installation & Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 16 (or SQLite in memory for automated tests)

### Quick Start with Docker Compose
```bash
# 1. Clone repository and navigate to root
cd /path/to/intelligence-layer

# 2. Copy and configure environment variables
cp .env.example .env

# 3. Start PostgreSQL, Backend, and Frontend containers
docker compose up -d

# 4. Open dashboard in browser
open http://localhost
```

### Local Manual Development Setup

#### Backend (FastAPI)
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

#### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be live at `http://localhost:5173`.

---

## 7. Running Automated Tests

The prototype includes unit tests, integration tests, and Hypothesis property-based invariant verification:

```bash
cd backend
source .venv/bin/activate

# Run full test suite with verbose output
pytest tests/ -v

# Run property-based invariant tests
pytest tests/test_property_based.py -v
```

### Invariants Verified by Hypothesis
1. **Bounded Risk Score**: Scores strictly remain between `0.00` and `100.00` across all arbitrary signal combinations.
2. **Determinism**: Exact same ordered event sequence under identical engine version always outputs identical risk scores and explanations.
3. **Hard Limit Integrity**: Risk evaluation never mutates, disables, or overrides user-configured loss limits.
4. **Idempotent Ingestion**: Duplicate event IDs return an idempotent acknowledgement without double-counting position sizes or realized P&L.

---

## 8. AWS EC2 Deployment Guide

The prototype is containerized and configured for deployment on an AWS EC2 instance running Ubuntu 22.04 / 24.04 LTS.

### Architecture on AWS
`User Browser → Port 80/443 (Nginx) → Internal Docker Network (FastAPI Backend :8000) → Private PostgreSQL (:5432)`
*PostgreSQL is private and never exposed to the public internet.*

### Step 1: Launch EC2 Instance
- **Instance Type**: `t3.medium` or `t3.small` (cost: ~$0.02 - $0.04/hr, ~$15 - $30/month)
- **AMI**: Ubuntu 24.04 LTS
- **Security Group**: Allow TCP `22` (restricted to your IP), `80` (HTTP), `443` (HTTPS).

### Step 2: One-Click Deployment Script
From your local machine:
```bash
export EC2_HOST="your-ec2-public-ip-or-dns"
export SSH_KEY="~/.ssh/your-key.pem"

# 1. Setup Docker, Nginx, and security on remote instance
ssh -i "${SSH_KEY}" ubuntu@${EC2_HOST} "bash -s" < deploy/setup-ec2.sh

# 2. Deploy application and run migrations
./deploy/deploy-ec2.sh
```

### Step 3: Cleanup / Teardown
To avoid unwanted cloud charges when the demo concludes:
```bash
export EC2_HOST="your-ec2-public-ip-or-dns"
export SSH_KEY="~/.ssh/your-key.pem"

./deploy/cleanup.sh
```
Then terminate the EC2 instance via the AWS Console or AWS CLI.

---

## 9. Methodological Limitations & Disclaimer

> [!CAUTION]
> **Engineering Prototype Demonstration**:
> 1. All evaluations and metrics presented are derived from constructed synthetic scenarios. They do **not** represent verified operational accuracy on live retail trader populations.
> 2. Feature thresholds (e.g. 2x baseline re-entry) are heuristic and require calibration against anonymized historical brokerage logs before production pilot.
> 3. Business calculator outputs are illustrative models and do not constitute financial forecasts or proof of increased retention or revenue.
