// Match these to the backend Pydantic schemas

export type EventType =
  | 'order_submitted' | 'order_accepted' | 'order_partially_filled'
  | 'order_filled' | 'order_cancelled' | 'trade_closed'
  | 'pnl_updated' | 'exposure_updated' | 'session_started' | 'session_ended';

export type RiskBand = 'normal' | 'elevated' | 'high';
export type Confidence = 'high' | 'medium' | 'low' | 'insufficient_data';
export type SessionStatus = 'active' | 'completed' | 'abandoned';
export type ActionType = 'monitor' | 'warning' | 'cooldown_offer' | 'review_recommendation' | 'session_protection_simulation';

export interface TraderProfile {
  id: string;
  external_id: string;
  display_name: string;
  created_at: string;
  default_position_limit: number;
  daily_loss_limit: number;
  is_synthetic: boolean;
}

export interface TradingSession {
  id: string;
  trader_id: string;
  scenario_id: string | null;
  started_at: string;
  ended_at: string | null;
  status: SessionStatus;
  peak_pnl: number;
  current_pnl: number;
  total_trades: number;
  is_synthetic: boolean;
}

export interface TradeEvent {
  id: string;
  event_id: string;
  session_id: string;
  trader_id: string;
  event_type: EventType;
  instrument: string;
  timestamp: string;
  ingested_at: string;
  side: string | null;
  quantity: number | null;
  price: number | null;
  realized_pnl: number | null;
  source_id: string;
  schema_version: string;
  processing_status: string;
  rejection_reason: string | null;
}

export interface FeatureSnapshot {
  id: string;
  session_id: string;
  computed_at: string;
  post_loss_reentry_seconds: number | null;
  baseline_reentry_seconds: number | null;
  position_size_current: number | null;
  position_size_baseline: number | null;
  position_size_limit: number | null;
  trade_frequency_current: number | null;
  trade_frequency_baseline: number | null;
  trade_frequency_window_minutes: number;
  consecutive_losses: number;
  consecutive_loss_total: number;
  peak_session_pnl: number;
  current_session_pnl: number;
  profit_giveback_pct: number | null;
  combined_deviation_score: number | null;
  feature_version: string;
}

export interface RiskSignal {
  name: string;
  triggered: boolean;
  severity: string;
  value: number | null;
  threshold: number | null;
  description: string;
}

export interface RiskAssessment {
  id: string;
  session_id: string;
  assessed_at: string;
  risk_score: number;
  risk_band: RiskBand;
  triggered_signals: RiskSignal[];
  explanation: string;
  confidence: Confidence;
  data_sufficiency: number;
  engine_version: string;
  baseline_version: string | null;
}

export interface InterventionDecision {
  id: string;
  assessment_id: string;
  session_id: string;
  decided_at: string;
  action_type: ActionType;
  action_details: Record<string, unknown>;
  is_simulated: boolean;
  acknowledged: boolean;
  engine_version: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  trader_name: string;
  expected_outcome: string;
  event_count: number;
}

export interface BaselineInfo {
  trader_id: string;
  historical_sessions: number;
  is_cold_start: boolean;
  baseline_version: string | null;
  last_updated: string | null;
  features: {
    avg_reentry_seconds: number | null;
    avg_position_size: number | null;
    avg_trade_frequency: number | null;
    observations_reentry: number;
    observations_position: number;
    observations_frequency: number;
  };
}

export interface EvaluationScenario {
  scenario_id: string;
  name: string;
  events_processed: number;
  final_risk_band: RiskBand;
  max_risk_score: number;
  signals_triggered: number;
  expected_outcome_met: boolean | null;
  detection_latency_events: number | null;
}

export interface EvaluationSummary {
  total_scenarios: number;
  total_events: number;
  total_assessments: number;
  scenarios: EvaluationScenario[];
  data_integrity: {
    duplicates_detected: number;
    invalid_rejected: number;
    out_of_order_handled: number;
  };
  limitations: string[];
}

export interface SessionState {
  session: TradingSession;
  current_pnl: number;
  peak_pnl: number;
  total_trades: number;
  open_positions: number;
  events_processed: number;
  latest_risk: RiskAssessment | null;
  latest_features: FeatureSnapshot | null;
  latest_intervention: InterventionDecision | null;
}

export interface ReplayState {
  session_id: string;
  scenario_id: string;
  trader_id?: string;
  total_events: number;
  current_index: number;
  is_playing: boolean;
  is_complete: boolean;
  speed: number;
  events: TradeEvent[];
  risk_assessments: RiskAssessment[];
  feature_snapshots: FeatureSnapshot[];
  interventions: InterventionDecision[];
}
