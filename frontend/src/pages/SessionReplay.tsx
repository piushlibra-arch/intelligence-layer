import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Info
} from 'lucide-react';
import { useScenarios } from '../hooks/useScenarios';
import { useReplay } from '../hooks/useReplay';
import { ReplayControls } from '../components/ReplayControls';
import { EventTimeline } from '../components/EventTimeline';
import { RiskGauge } from '../components/RiskGauge';
import { PnLChart } from '../components/PnLChart';
import { RiskScoreChart } from '../components/RiskScoreChart';
import { FeatureRadar } from '../components/FeatureRadar';
import { SignalList } from '../components/SignalList';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { formatCurrency } from '../utils/format';
import { getBaseline } from '../api/client';
import type { BaselineInfo } from '../types';
import './SessionReplay.css';

export const SessionReplay: React.FC = () => {
  const { scenarios, loading: scenariosLoading, error: scenariosError } = useScenarios();
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_b');
  const [baselineInfo, setBaselineInfo] = useState<BaselineInfo | null>(null);

  const {
    state,
    scenarioInfo,
    loading: replayLoading,
    error: replayError,
    start,
    play,
    pause,
    stepForward,
    stepBackward,
    reset,
    setSpeed,
  } = useReplay();

  // Initialize scenario
  useEffect(() => {
    if (scenarios.length > 0 && !state.session_id) {
      start(selectedScenarioId);
    }
  }, [scenarios, selectedScenarioId, start, state.session_id]);

  // Fetch baseline for current trader
  useEffect(() => {
    async function fetchTraderBaseline() {
      const traderId = state.trader_id || (state.events.length > 0 ? state.events[0].trader_id : null);
      if (traderId) {
        try {
          const res = await getBaseline(traderId);
          setBaselineInfo(res.data);
        } catch {
          setBaselineInfo(null);
        }
      }
    }
    fetchTraderBaseline();
  }, [state.trader_id, state.events]);

  const handleScenarioChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setSelectedScenarioId(newId);
    start(newId);
  };

  if (scenariosLoading) return <LoadingSpinner message="Loading trading scenarios..." />;
  if (scenariosError) return <ErrorDisplay message={scenariosError} />;

  const latestAssessment = state.risk_assessments[state.risk_assessments.length - 1] || null;
  const latestFeature = state.feature_snapshots[state.feature_snapshots.length - 1] || null;
  const latestIntervention = state.interventions[state.interventions.length - 1] || null;

  // Session P&L from latest feature snapshot or events
  const currentPnL = latestFeature ? Number(latestFeature.current_session_pnl) : 0;

  return (
    <div className="replay-page">
      {/* Scenario Selection Header */}
      <div className="replay-header">
        <div className="scenario-selector-box">
          <label htmlFor="scenario-select" className="selector-label">
            Active Scenario:
          </label>
          <select
            id="scenario-select"
            className="scenario-dropdown"
            value={selectedScenarioId}
            onChange={handleScenarioChange}
          >
            {scenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name} ({sc.trader_name})
              </option>
            ))}
          </select>
        </div>

        {scenarioInfo && (
          <div className="scenario-meta">
            <span className="scenario-desc">{scenarioInfo.description}</span>
            <span className="scenario-expected">
              <strong>Expected:</strong> {scenarioInfo.expected_outcome}
            </span>
          </div>
        )}
      </div>

      {/* Interactive Controls Bar */}
      <ReplayControls
        isPlaying={state.is_playing}
        isComplete={state.is_complete}
        currentIndex={state.current_index}
        totalEvents={state.total_events}
        speed={state.speed}
        loading={replayLoading}
        onPlay={play}
        onPause={pause}
        onStepForward={stepForward}
        onStepBackward={stepBackward}
        onReset={reset}
        onSpeedChange={setSpeed}
      />

      {replayError && <ErrorDisplay message={replayError} />}

      {/* Main Grid */}
      <div className="replay-main-grid">
        {/* Left Column: Event Stream */}
        <div className="replay-left-col">
          <EventTimeline
            events={state.events}
            currentIndex={state.current_index}
          />
        </div>

        {/* Center / Right Column: Live Decision Intelligence */}
        <div className="replay-right-col">
          {/* Top Row: Risk Score Gauge + Intervention Recommendation */}
          <div className="decision-row">
            {/* Risk Gauge Card */}
            <div className="replay-card gauge-card">
              <div className="card-title">Behavioral Risk Score</div>
              <RiskGauge
                score={latestAssessment ? Number(latestAssessment.risk_score) : 0}
                band={latestAssessment ? latestAssessment.risk_band : 'normal'}
              />
              <div className="gauge-footer">
                <span className="confidence-pill">
                  Confidence: {latestAssessment?.confidence.replace(/_/g, ' ') || 'initializing'}
                </span>
                <span className="engine-ver">Engine v{latestAssessment?.engine_version || '1.0'}</span>
              </div>
            </div>

            {/* Simulated Intervention Card */}
            <div className="replay-card intervention-card">
              <div className="card-title-row">
                <div className="card-title">Recommended Intervention</div>
                <span className="sim-badge">Simulated Only</span>
              </div>

              {latestIntervention ? (
                <div className={`intervention-box action--${latestIntervention.action_type}`}>
                  <div className="interv-header">
                    <ShieldAlert size={20} />
                    <span className="interv-type">
                      {latestIntervention.action_type.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  </div>
                  <h4 className="interv-headline">
                    {latestIntervention.action_details?.headline as string || 'Action Recommended'}
                  </h4>
                  <p className="interv-msg">
                    {latestIntervention.action_details?.message as string || ''}
                  </p>
                  <div className="interv-reason">
                    <strong>Reason:</strong> {latestIntervention.action_details?.reason as string || ''}
                  </div>
                </div>
              ) : (
                <div className="interv-empty">
                  <Info size={24} />
                  <span>Monitoring event stream. Interventions will appear here when triggered.</span>
                </div>
              )}
            </div>
          </div>

          {/* Middle Row: Active Signals & Explanation */}
          <div className="signals-explanation-row">
            <div className="replay-card signals-card">
              <div className="card-title">Triggered Risk Signals</div>
              <SignalList signals={latestAssessment?.triggered_signals || []} />
            </div>

            <div className="replay-card explanation-card">
              <div className="card-title">Traceable Audit Explanation</div>
              <div className="explanation-text">
                {latestAssessment?.explanation ? (
                  latestAssessment.explanation.split('\n').map((line, i) => (
                    <p key={i} className="explanation-line">
                      {line}
                    </p>
                  ))
                ) : (
                  <p className="text-muted">Awaiting initial events...</p>
                )}
              </div>
            </div>
          </div>

          {/* Charts Row: PnL & Risk Score Progression */}
          <div className="charts-row">
            <div className="replay-card chart-card">
              <div className="card-title-row">
                <div className="card-title">Realized Session P&L</div>
                <span className={`pnl-total ${currentPnL >= 0 ? 'pos' : 'neg'}`}>
                  {formatCurrency(currentPnL)}
                </span>
              </div>
              <PnLChart events={state.events} />
            </div>

            <div className="replay-card chart-card">
              <div className="card-title">Risk Score Progression</div>
              <RiskScoreChart assessments={state.risk_assessments} />
            </div>
          </div>

          {/* Behavioral Radar Comparison */}
          <div className="replay-card radar-card">
            <div className="card-title-row">
              <div className="card-title">Behavioral Feature Deviation vs Personal Baseline</div>
              <span className="baseline-tag">
                Baseline v{latestAssessment?.baseline_version || '1.0'}
              </span>
            </div>
            <FeatureRadar
              currentFeature={latestFeature}
              baseline={baselineInfo}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
