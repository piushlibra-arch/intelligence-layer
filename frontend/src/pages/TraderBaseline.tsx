import React, { useState, useEffect } from 'react';
import { UserCheck, Clock, Layers, Activity, AlertCircle } from 'lucide-react';
import { getTraders, getBaseline } from '../api/client';
import type { TraderProfile, BaselineInfo } from '../types';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { formatCurrency } from '../utils/format';
import './TraderBaseline.css';

export const TraderBaseline: React.FC = () => {
  const [traders, setTraders] = useState<TraderProfile[]>([]);
  const [selectedTraderId, setSelectedTraderId] = useState<string>('');
  const [baseline, setBaseline] = useState<BaselineInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTraders() {
      try {
        setLoading(true);
        const res = await getTraders();
        setTraders(res.data);
        if (res.data.length > 0) {
          setSelectedTraderId(res.data[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load trader profiles');
      } finally {
        setLoading(false);
      }
    }
    loadTraders();
  }, []);

  useEffect(() => {
    async function loadBaseline() {
      if (!selectedTraderId) return;
      try {
        const res = await getBaseline(selectedTraderId);
        setBaseline(res.data);
      } catch (err: any) {
        setBaseline(null);
      }
    }
    loadBaseline();
  }, [selectedTraderId]);

  if (loading) return <LoadingSpinner message="Loading trader baseline engine..." />;
  if (error) return <ErrorDisplay message={error} />;

  const currentTrader = traders.find((t) => t.id === selectedTraderId);

  return (
    <div className="baseline-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Trader Personal Baselines</h1>
          <p className="page-subtitle">
            Personalized behavioral reference norms derived from completed historical sessions. Robust to outliers and strictly isolated from future session data.
          </p>
        </div>
      </div>

      {/* Trader Selection Strip */}
      <div className="trader-tabs">
        {traders.map((trader) => (
          <button
            key={trader.id}
            className={`trader-tab ${trader.id === selectedTraderId ? 'trader-tab--active' : ''}`}
            onClick={() => setSelectedTraderId(trader.id)}
          >
            <div className="trader-tab__name">{trader.display_name}</div>
            <div className="trader-tab__id">{trader.external_id}</div>
          </button>
        ))}
      </div>

      {/* Selected Trader Baseline Summary */}
      {currentTrader && (
        <>
          {baseline?.is_cold_start ? (
            <div className="cold-start-banner">
              <AlertCircle size={22} className="cold-start-icon" />
              <div>
                <h4>Cold-Start Mode (Zero Historical Sessions)</h4>
                <p>
                  {currentTrader.display_name} has no historical completed trading sessions. The system strictly avoids fabricating personal norms. Risk assessments fall back to documented absolute guardrails with an 'insufficient_data' confidence flag.
                </p>
              </div>
            </div>
          ) : (
            <div className="baseline-stats-grid">
              <MetricCard
                title="Historical Sessions"
                value={baseline?.historical_sessions || 0}
                subtitle="Completed sessions analyzed"
                icon={<UserCheck size={20} />}
              />
              <MetricCard
                title="Baseline Re-entry Latency"
                value={
                  baseline?.features.avg_reentry_seconds
                    ? `${baseline.features.avg_reentry_seconds}s`
                    : 'N/A'
                }
                subtitle={`Median across ${baseline?.features.observations_reentry || 0} observations`}
                icon={<Clock size={20} />}
              />
              <MetricCard
                title="Baseline Position Size"
                value={
                  baseline?.features.avg_position_size
                    ? `${baseline.features.avg_position_size} shares`
                    : 'N/A'
                }
                subtitle={`Across ${baseline?.features.observations_position || 0} filled orders`}
                icon={<Layers size={20} />}
              />
              <MetricCard
                title="Typical Trade Frequency"
                value={
                  baseline?.features.avg_trade_frequency
                    ? `${baseline.features.avg_trade_frequency} / 30m`
                    : 'N/A'
                }
                subtitle={`Across ${baseline?.features.observations_frequency || 0} intervals`}
                icon={<Activity size={20} />}
              />
            </div>
          )}

          {/* Configuration & Integrity Details */}
          <div className="baseline-details-grid">
            <div className="card">
              <div className="card-header">
                <h3>Trader Profile & Configured Limits</h3>
              </div>
              <div className="details-list">
                <div className="detail-row">
                  <span className="detail-label">Trader ID</span>
                  <span className="detail-value font-mono">{currentTrader.id}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Configured Position Limit</span>
                  <span className="detail-value font-mono">
                    {currentTrader.default_position_limit} shares
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Configured Daily Loss Limit</span>
                  <span className="detail-value font-mono">
                    {formatCurrency(currentTrader.daily_loss_limit)}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Baseline Version</span>
                  <span className="detail-value font-mono">
                    {baseline?.baseline_version ? `v${baseline.baseline_version}` : 'None (Cold Start)'}
                  </span>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Baseline Update Rules & Guarantees</h3>
              </div>
              <div className="rules-content">
                <p>
                  <strong>1. Leak Prevention:</strong> Baseline metrics are strictly computed from completed sessions that ended prior to the current session start time. Current session events never leak into historical baselines.
                </p>
                <p>
                  <strong>2. Outlier Resistance:</strong> All baseline norms use sample medians rather than means, preventing temporary freak trades from distorting behavioral expectations.
                </p>
                <p>
                  <strong>3. Hard Limit Separation:</strong> The intelligence layer never modifies, widens, or bypasses trader-configured daily loss or position limits.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
