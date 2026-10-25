import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  ShieldCheck,
  Calculator,
  AlertTriangle,
  Info,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { getEvaluationSummary, startEvaluation } from '../api/client';
import type { EvaluationSummary } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { formatCurrency } from '../utils/format';
import './Evaluation.css';

export const Evaluation: React.FC = () => {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Business Impact Calculator State (Illustrative Only)
  const [tradersCount, setTradersCount] = useState<number>(10000);
  const [riskyPct, setRiskyPct] = useState<number>(8); // 8% of traders exhibit risk escalation
  const [interventionEfficacy, setInterventionEfficacy] = useState<number>(35); // 35% heed voluntary cooldown
  const [avgAnnualBrokerage, setAvgAnnualBrokerage] = useState<number>(15000); // ₹15,000 annual brokerage

  const loadEvaluation = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getEvaluationSummary();
      setSummary(res.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvaluation();
  }, []);

  const handleRunFreshEvaluation = async () => {
    try {
      setEvaluating(true);
      const res = await startEvaluation();
      setSummary(res.data);
    } catch (err: any) {
      setError(err.message || 'Failed to run evaluation suite');
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) return <LoadingSpinner message="Calculating evaluation metrics across benchmark scenarios..." />;
  if (error) return <ErrorDisplay message={error} onRetry={loadEvaluation} />;

  // Illustrative calculations
  const riskyTraders = Math.round((tradersCount * riskyPct) / 100);
  const retainedTraders = Math.round((riskyTraders * interventionEfficacy) / 100);
  const hypotheticalAnnualRevenueRetained = retainedTraders * avgAnnualBrokerage;

  return (
    <div className="evaluation-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Evaluation & Business Impact</h1>
          <p className="page-subtitle">
            Empirical evaluation against predefined test scenarios. Strictly separates observed engineering performance from speculative business projections.
          </p>
        </div>
        <button
          className="btn btn--primary"
          onClick={handleRunFreshEvaluation}
          disabled={evaluating}
        >
          <RefreshCw size={16} className={evaluating ? 'spin-icon' : ''} />
          <span>{evaluating ? 'Evaluating...' : 'Re-run Evaluation Suite'}</span>
        </button>
      </div>

      {/* Metrics Strip */}
      <div className="metrics-grid">
        <MetricCard
          title="Scenarios Tested"
          value={summary?.total_scenarios || 0}
          subtitle="Predefined behavioral test cases"
          icon={<BarChart3 size={20} />}
        />
        <MetricCard
          title="Events Ingested"
          value={summary?.total_events || 0}
          subtitle="Processed through pipeline"
          icon={<ShieldCheck size={20} />}
        />
        <MetricCard
          title="Duplicate Events Caught"
          value={summary?.data_integrity.duplicates_detected || 0}
          subtitle="Zero duplicate P&L impact"
          icon={<CheckCircle2 size={20} />}
        />
        <MetricCard
          title="Invalid Events Rejected"
          value={summary?.data_integrity.invalid_rejected || 0}
          subtitle="Schema validation guardrails"
          icon={<AlertTriangle size={20} />}
        />
      </div>

      {/* Scenarios Benchmark Results Table */}
      <div className="card">
        <div className="card-header">
          <h3>Scenario Benchmark Results</h3>
          <span className="card-tag">Ground Truth Verification</span>
        </div>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Scenario Name</th>
                <th>Events Processed</th>
                <th>Final Risk Band</th>
                <th>Peak Risk Score</th>
                <th>Detection Latency</th>
                <th>Outcome Status</th>
              </tr>
            </thead>
            <tbody>
              {summary?.scenarios.map((sc) => (
                <tr key={sc.scenario_id}>
                  <td>
                    <strong>{sc.name}</strong>
                    <div className="text-muted text-xs font-mono">{sc.scenario_id}</div>
                  </td>
                  <td>{sc.events_processed}</td>
                  <td>
                    <StatusBadge type="risk" value={sc.final_risk_band} />
                  </td>
                  <td>
                    <span className="font-mono font-bold">{sc.max_risk_score}</span>/100
                  </td>
                  <td>
                    {sc.detection_latency_events ? (
                      <span className="font-mono text-xs">Event #{sc.detection_latency_events}</span>
                    ) : (
                      <span className="text-muted text-xs">No alert (Normal)</span>
                    )}
                  </td>
                  <td>
                    <span className={`match-badge ${sc.expected_outcome_met ? 'match-yes' : 'match-no'}`}>
                      {sc.expected_outcome_met ? '✓ Expected Outcome Met' : 'Mismatch'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Illustrative Business Scenario Calculator */}
      <div className="card calculator-card">
        <div className="card-header">
          <div className="calc-title-box">
            <Calculator size={20} className="text-accent" />
            <div>
              <h3>Illustrative Business Scenario Calculator</h3>
              <p className="calc-disclaimer">
                ⚠️ All inputs and outputs below are illustrative hypothetical assumptions, NOT measured outcomes. Reduced risky trading does not automatically increase brokerage revenue.
              </p>
            </div>
          </div>
        </div>

        <div className="calculator-body">
          <div className="calculator-controls">
            <div className="calc-field">
              <label>Active Trader Base:</label>
              <input
                type="number"
                value={tradersCount}
                onChange={(e) => setTradersCount(Number(e.target.value))}
                className="calc-input"
                step="1000"
              />
            </div>

            <div className="calc-field">
              <label>Estimated Risk-Escalating Traders (%):</label>
              <input
                type="range"
                min="1"
                max="25"
                value={riskyPct}
                onChange={(e) => setRiskyPct(Number(e.target.value))}
                className="calc-slider"
              />
              <span className="slider-val">{riskyPct}% ({riskyTraders.toLocaleString()} traders)</span>
            </div>

            <div className="calc-field">
              <label>Assumed Intervention Efficacy (% Cooldown Adherence):</label>
              <input
                type="range"
                min="5"
                max="80"
                value={interventionEfficacy}
                onChange={(e) => setInterventionEfficacy(Number(e.target.value))}
                className="calc-slider"
              />
              <span className="slider-val">{interventionEfficacy}% ({retainedTraders.toLocaleString()} traders)</span>
            </div>

            <div className="calc-field">
              <label>Average Annual Brokerage Per Trader (₹):</label>
              <input
                type="number"
                value={avgAnnualBrokerage}
                onChange={(e) => setAvgAnnualBrokerage(Number(e.target.value))}
                className="calc-input"
                step="1000"
              />
            </div>
          </div>

          <div className="calculator-output-box">
            <div className="output-label">Hypothetical Annual Brokerage Preserved (Illustrative)</div>
            <div className="output-val">{formatCurrency(hypotheticalAnnualRevenueRetained)}</div>
            <p className="output-note">
              Based on {retainedTraders.toLocaleString()} traders avoiding catastrophic capital depletion and continuing active trading at ₹{avgAnnualBrokerage.toLocaleString()}/yr. Real-world validation on actual customer cohorts is required before relying on these figures.
            </p>
          </div>
        </div>
      </div>

      {/* Documented Limitations */}
      <div className="card">
        <div className="card-header">
          <h3>Methodological Limitations & Constraints</h3>
          <Info size={18} className="text-muted" />
        </div>
        <div className="limitations-list">
          {summary?.limitations.map((lim, i) => (
            <div key={i} className="limitation-item">
              <div className="lim-bullet" />
              <span>{lim}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
