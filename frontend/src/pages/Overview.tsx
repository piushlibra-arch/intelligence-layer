import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ShieldCheck,
  Zap,
  FileCheck,
  Server
} from 'lucide-react';
import { getSessions, getEvaluationSummary, healthCheck } from '../api/client';
import type { TradingSession, EvaluationSummary } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorDisplay } from '../components/ErrorDisplay';
import './Overview.css';

export const Overview: React.FC = () => {
  const [sessions, setSessions] = useState<TradingSession[]>([]);
  const [evalSummary, setEvalSummary] = useState<EvaluationSummary | null>(null);
  const [backendHealth, setBackendHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [sessRes, evalRes, healthRes] = await Promise.all([
          getSessions().catch(() => ({ data: [] })),
          getEvaluationSummary().catch(() => ({ data: null })),
          healthCheck().catch(() => ({ data: { status: 'offline' } })),
        ]);
        setSessions(sessRes.data);
        setEvalSummary(evalRes.data);
        setBackendHealth(healthRes.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch overview data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <LoadingSpinner message="Loading risk intelligence overview..." />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  const elevatedCount = evalSummary?.scenarios.filter(s => s.final_risk_band === 'elevated').length || 0;
  const highRiskCount = evalSummary?.scenarios.filter(s => s.final_risk_band === 'high').length || 0;

  return (
    <div className="overview-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Trader Risk Intelligence</h1>
          <p className="page-subtitle">
            Explainable, personalized behavioral risk detection operating in shadow simulation mode.
          </p>
        </div>
        <div className="engine-status-badge">
          <Server size={14} />
          <span>Engine v1.0.0 ({backendHealth?.status || 'Active'})</span>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="metrics-grid">
        <MetricCard
          title="Simulated Sessions"
          value={evalSummary?.total_scenarios || sessions.length}
          subtitle="Pre-calibrated test scenarios"
          icon={<Activity size={20} />}
        />
        <MetricCard
          title="Elevated Risk Events"
          value={elevatedCount}
          subtitle="Warranting advisory monitoring"
          icon={<AlertTriangle size={20} />}
        />
        <MetricCard
          title="High Risk Escalations"
          value={highRiskCount}
          subtitle="Triggering voluntary cooldown"
          icon={<Zap size={20} />}
        />
        <MetricCard
          title="Events Ingested"
          value={evalSummary?.total_events || 0}
          subtitle="Synthetic trading events"
          icon={<FileCheck size={20} />}
        />
      </div>

      <div className="overview-grid">
        {/* Scenario Benchmark Summary */}
        <div className="card">
          <div className="card-header">
            <h3>Demonstration Scenarios Evaluation</h3>
            <span className="card-tag">Benchmark Suite</span>
          </div>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Scenario</th>
                  <th>Events</th>
                  <th>Max Score</th>
                  <th>Risk Band</th>
                  <th>Outcome Match</th>
                </tr>
              </thead>
              <tbody>
                {evalSummary?.scenarios.map((sc) => (
                  <tr key={sc.scenario_id}>
                    <td>
                      <div className="font-semibold">{sc.name}</div>
                      <span className="text-muted text-xs font-mono">{sc.scenario_id}</span>
                    </td>
                    <td>{sc.events_processed}</td>
                    <td>
                      <span className="font-mono font-bold">{sc.max_risk_score}</span>/100
                    </td>
                    <td>
                      <StatusBadge type="risk" value={sc.final_risk_band} />
                    </td>
                    <td>
                      <span className={`match-badge ${sc.expected_outcome_met ? 'match-yes' : 'match-no'}`}>
                        {sc.expected_outcome_met ? '✓ Verified' : 'Pending'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Integrity & Safeguards */}
        <div className="card">
          <div className="card-header">
            <h3>Safeguards & Shadow Mode</h3>
            <ShieldCheck size={18} className="text-green" />
          </div>
          <div className="safeguards-content">
            <div className="safeguard-item">
              <div className="safeguard-bullet" />
              <div>
                <strong>Zero Live Order Impact</strong>
                <p>Engine operates strictly in shadow mode. No orders modified, blocked, or executed.</p>
              </div>
            </div>
            <div className="safeguard-item">
              <div className="safeguard-bullet" />
              <div>
                <strong>Deterministic Behavioral Scoring</strong>
                <p>Identical event sequence under same engine produces 100% repeatable audit score.</p>
              </div>
            </div>
            <div className="safeguard-item">
              <div className="safeguard-bullet" />
              <div>
                <strong>Idempotent Event Ingestion</strong>
                <p>Duplicate event IDs are quarantined and rejected without double-counting session P&L.</p>
              </div>
            </div>
            <div className="safeguard-item">
              <div className="safeguard-bullet" />
              <div>
                <strong>Personalized Baseline Isolation</strong>
                <p>Uses historical completed sessions strictly before current session started to prevent future leak.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
