import { useState, useRef, useCallback, useEffect } from 'react';
import {
  startReplay,
  ingestEvent,
  getLatestRisk,
  getLatestFeatures,
  getInterventions,
  getScenario,
} from '../api/client';
import type {
  ReplayState,
  TradeEvent,
  RiskAssessment,
  FeatureSnapshot,
  InterventionDecision,
  Scenario,
} from '../types';

const INITIAL_STATE: ReplayState = {
  session_id: '',
  scenario_id: '',
  total_events: 0,
  current_index: 0,
  is_playing: false,
  is_complete: false,
  speed: 1,
  events: [],
  risk_assessments: [],
  feature_snapshots: [],
  interventions: [],
};

export function useReplay() {
  const [state, setState] = useState<ReplayState>(INITIAL_STATE);
  const [scenarioEvents, setScenarioEvents] = useState<TradeEvent[]>([]);
  const [scenarioInfo, setScenarioInfo] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stepping, setStepping] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearAutoPlay = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => clearAutoPlay();
  }, [clearAutoPlay]);

  /**
   * Start a new replay session for the given scenario
   */
  const start = useCallback(async (scenarioId: string) => {
    clearAutoPlay();
    setLoading(true);
    setError(null);
    try {
      // Get scenario info
      const scenarioRes = await getScenario(scenarioId);
      setScenarioInfo(scenarioRes.data);

      // Start replay - returns session_id and events
      const res = await startReplay(scenarioId);
      const sessionId = res.data.session_id;
      const events = (res.data as Record<string, unknown>).events as TradeEvent[] | undefined;

      setScenarioEvents(events || []);
      setState({
        ...INITIAL_STATE,
        session_id: sessionId,
        scenario_id: scenarioId,
        total_events: events?.length || scenarioRes.data.event_count,
        events: [],
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start replay';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [clearAutoPlay]);

  /**
   * Process the next event in the sequence
   */
  const processNextEvent = useCallback(async () => {
    if (!state.session_id || state.current_index >= scenarioEvents.length) {
      clearAutoPlay();
      setState(prev => ({ ...prev, is_playing: false, is_complete: true }));
      return;
    }

    setStepping(true);
    try {
      const event = scenarioEvents[state.current_index];
      // Ingest the event into the session
      await ingestEvent(state.session_id, event as unknown as Record<string, unknown>);

      // Fetch latest risk assessment and features after processing
      let latestRisk: RiskAssessment | null = null;
      let latestFeatures: FeatureSnapshot | null = null;
      let latestInterventions: InterventionDecision[] = [];

      try {
        const [riskRes, featRes, intRes] = await Promise.all([
          getLatestRisk(state.session_id).catch(() => null),
          getLatestFeatures(state.session_id).catch(() => null),
          getInterventions(state.session_id).catch(() => null),
        ]);
        latestRisk = riskRes?.data || null;
        latestFeatures = featRes?.data || null;
        latestInterventions = intRes?.data || [];
      } catch {
        // Non-critical: risk/features may not be ready yet
      }

      setState(prev => {
        const newEvents = [...prev.events, event];
        const newRisks = latestRisk
          ? [...prev.risk_assessments.filter(r => r.id !== latestRisk!.id), latestRisk]
          : prev.risk_assessments;
        const newFeatures = latestFeatures
          ? [...prev.feature_snapshots.filter(f => f.id !== latestFeatures!.id), latestFeatures]
          : prev.feature_snapshots;
        const newIndex = prev.current_index + 1;
        const isComplete = newIndex >= scenarioEvents.length;

        return {
          ...prev,
          events: newEvents,
          risk_assessments: newRisks,
          feature_snapshots: newFeatures,
          interventions: latestInterventions,
          current_index: newIndex,
          is_complete: isComplete,
          is_playing: isComplete ? false : prev.is_playing,
        };
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to process event';
      setError(msg);
      clearAutoPlay();
      setState(prev => ({ ...prev, is_playing: false }));
    } finally {
      setStepping(false);
    }
  }, [state.session_id, state.current_index, scenarioEvents, clearAutoPlay]);

  /**
   * Play / auto-step through events
   */
  const play = useCallback(() => {
    if (state.is_complete || !state.session_id) return;
    setState(prev => ({ ...prev, is_playing: true }));
  }, [state.is_complete, state.session_id]);

  // Effect to manage auto-play interval
  useEffect(() => {
    if (state.is_playing && !stepping) {
      clearAutoPlay();
      const interval = 1000 / state.speed;
      intervalRef.current = setInterval(() => {
        processNextEvent();
      }, interval);
    } else if (!state.is_playing) {
      clearAutoPlay();
    }
    return () => clearAutoPlay();
  }, [state.is_playing, state.speed, stepping, processNextEvent, clearAutoPlay]);

  /**
   * Pause auto-play
   */
  const pause = useCallback(() => {
    clearAutoPlay();
    setState(prev => ({ ...prev, is_playing: false }));
  }, [clearAutoPlay]);

  /**
   * Step forward one event
   */
  const stepForward = useCallback(() => {
    if (state.is_playing || stepping) return;
    processNextEvent();
  }, [state.is_playing, stepping, processNextEvent]);

  /**
   * Step backward - requires resetting and replaying up to current_index - 1
   */
  const stepBackward = useCallback(async () => {
    if (state.current_index <= 0 || !state.scenario_id || stepping) return;
    const targetIndex = state.current_index - 1;

    clearAutoPlay();
    setLoading(true);
    try {
      // Start a new replay session
      const res = await startReplay(state.scenario_id);
      const sessionId = res.data.session_id;
      const events = (res.data as Record<string, unknown>).events as TradeEvent[] | undefined;
      if (events) setScenarioEvents(events);

      const eventsToUse = events || scenarioEvents;

      // Reset state
      setState(prev => ({
        ...INITIAL_STATE,
        scenario_id: prev.scenario_id,
        session_id: sessionId,
        total_events: eventsToUse.length,
        speed: prev.speed,
      }));

      // Replay up to targetIndex
      const processedEvents: TradeEvent[] = [];
      let latestRisk: RiskAssessment | null = null;
      let latestFeatures: FeatureSnapshot | null = null;
      let latestInterventions: InterventionDecision[] = [];

      for (let i = 0; i < targetIndex; i++) {
        await ingestEvent(sessionId, eventsToUse[i] as unknown as Record<string, unknown>);
        processedEvents.push(eventsToUse[i]);
      }

      // Fetch latest state
      if (targetIndex > 0) {
        try {
          const [riskRes, featRes, intRes] = await Promise.all([
            getLatestRisk(sessionId).catch(() => null),
            getLatestFeatures(sessionId).catch(() => null),
            getInterventions(sessionId).catch(() => null),
          ]);
          latestRisk = riskRes?.data || null;
          latestFeatures = featRes?.data || null;
          latestInterventions = intRes?.data || [];
        } catch {
          // Non-critical
        }
      }

      setState({
        session_id: sessionId,
        scenario_id: state.scenario_id,
        total_events: eventsToUse.length,
        current_index: targetIndex,
        is_playing: false,
        is_complete: false,
        speed: state.speed,
        events: processedEvents,
        risk_assessments: latestRisk ? [latestRisk] : [],
        feature_snapshots: latestFeatures ? [latestFeatures] : [],
        interventions: latestInterventions,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to step backward';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [state.current_index, state.scenario_id, state.speed, scenarioEvents, stepping, clearAutoPlay]);

  /**
   * Reset replay - start fresh
   */
  const reset = useCallback(async () => {
    if (!state.scenario_id) return;
    clearAutoPlay();
    await start(state.scenario_id);
  }, [state.scenario_id, start, clearAutoPlay]);

  /**
   * Set playback speed
   */
  const setSpeed = useCallback((speed: number) => {
    setState(prev => ({ ...prev, speed }));
  }, []);

  return {
    state,
    scenarioInfo,
    loading,
    error,
    stepping,
    start,
    play,
    pause,
    stepForward,
    stepBackward,
    reset,
    setSpeed,
  };
}
