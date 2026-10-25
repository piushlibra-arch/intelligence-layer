import axios from 'axios';
import type {
  Scenario,
  TradingSession,
  SessionState,
  TradeEvent,
  FeatureSnapshot,
  RiskAssessment,
  InterventionDecision,
  BaselineInfo,
  TraderProfile,
  EvaluationSummary,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || '';
const API_KEY = import.meta.env.VITE_API_KEY || 'intel_secret_key_2026';

const api = axios.create({
  baseURL: API_URL ? `${API_URL}/api/v1` : '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Add API key for mutating requests
api.interceptors.request.use((config) => {
  if (['post', 'put', 'delete', 'patch'].includes(config.method || '')) {
    config.headers['X-API-Key'] = API_KEY;
  }
  return config;
});

// API functions
export const healthCheck = () => api.get('/health');
export const getScenarios = () => api.get<Scenario[]>('/scenarios');
export const getScenario = (id: string) => api.get<Scenario>(`/scenarios/${id}`);
export const startReplay = (scenarioId: string) =>
  api.post<{ session_id: string; scenario_id: string; trader_id: string; total_events: number; events: TradeEvent[] }>(
    `/scenarios/${scenarioId}/replay`
  );
export const getSessions = () => api.get<TradingSession[]>('/sessions');
export const getSession = (id: string) => api.get<TradingSession>(`/sessions/${id}`);
export const getSessionState = (id: string) => api.get<SessionState>(`/sessions/${id}/state`);
export const ingestEvent = (sessionId: string, event: Record<string, unknown>) =>
  api.post(`/sessions/${sessionId}/events`, event);
export const getEvents = (sessionId: string) =>
  api.get<TradeEvent[]>(`/sessions/${sessionId}/events`);
export const getFeatures = (sessionId: string) =>
  api.get<FeatureSnapshot[]>(`/sessions/${sessionId}/features`);
export const getLatestFeatures = (sessionId: string) =>
  api.get<FeatureSnapshot>(`/sessions/${sessionId}/features/latest`);
export const getRiskAssessments = (sessionId: string) =>
  api.get<RiskAssessment[]>(`/sessions/${sessionId}/risk`);
export const getLatestRisk = (sessionId: string) =>
  api.get<RiskAssessment>(`/sessions/${sessionId}/risk/latest`);
export const getInterventions = (sessionId: string) =>
  api.get<InterventionDecision[]>(`/sessions/${sessionId}/interventions`);
export const getBaseline = (traderId: string) =>
  api.get<BaselineInfo>(`/traders/${traderId}/baseline`);
export const getTraders = () => api.get<TraderProfile[]>('/traders');
export const getAuditRecords = (params?: Record<string, string>) =>
  api.get('/audit', { params });
export const getEvaluationSummary = () => api.get<EvaluationSummary>('/evaluation/summary');
export const startEvaluation = () => api.post('/evaluation/runs');

export default api;
