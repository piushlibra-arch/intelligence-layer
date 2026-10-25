import React from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Tooltip
} from 'recharts';
import type { FeatureSnapshot, BaselineInfo } from '../types';

interface Props {
  currentFeature: FeatureSnapshot | null;
  baseline: BaselineInfo | null;
}

export const FeatureRadar: React.FC<Props> = ({ currentFeature, baseline }) => {
  // Normalize each metric to 0-100 scale for visual comparison
  const normalizeReentry = (val: number | null) => {
    if (!val) return 20;
    // Faster re-entry = higher deviation risk (e.g. 10s = 90, 60s = 40, 120s = 10)
    return Math.min(100, Math.max(0, Math.round(100 - val * 0.8)));
  };

  const normalizePosition = (val: number | null, base: number | null) => {
    if (!val || !base) return 20;
    const ratio = val / base;
    return Math.min(100, Math.round(ratio * 35));
  };

  const normalizeFreq = (val: number | null, base: number | null) => {
    if (!val) return 10;
    const b = base || 4;
    return Math.min(100, Math.round((val / b) * 35));
  };

  const normalizeLosses = (val: number | null) => {
    if (!val) return 0;
    return Math.min(100, val * 25);
  };

  const normalizeGiveback = (val: number | null) => {
    if (!val) return 0;
    return Math.min(100, Math.round(val));
  };

  const data = [
    {
      subject: 'Re-entry Speed',
      current: normalizeReentry(currentFeature?.post_loss_reentry_seconds ?? null),
      baseline: normalizeReentry(baseline?.features.avg_reentry_seconds ?? null),
      fullMark: 100,
    },
    {
      subject: 'Position Size',
      current: normalizePosition(
        currentFeature?.position_size_current ?? null,
        baseline?.features.avg_position_size ?? null
      ),
      baseline: 35,
      fullMark: 100,
    },
    {
      subject: 'Trade Freq',
      current: normalizeFreq(
        currentFeature?.trade_frequency_current ?? null,
        baseline?.features.avg_trade_frequency ?? null
      ),
      baseline: 35,
      fullMark: 100,
    },
    {
      subject: 'Loss Streak',
      current: normalizeLosses(currentFeature?.consecutive_losses ?? null),
      baseline: 15,
      fullMark: 100,
    },
    {
      subject: 'Profit Giveback',
      current: normalizeGiveback(currentFeature?.profit_giveback_pct ?? null),
      baseline: 10,
      fullMark: 100,
    },
    {
      subject: 'Combined Score',
      current: Math.min(100, Number(currentFeature?.combined_deviation_score || 0)),
      baseline: 15,
      fullMark: 100,
    },
  ];

  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="var(--border)" />
          <PolarAngleAxis dataKey="subject" stroke="var(--text-secondary)" fontSize={11} />
          <PolarRadiusAxis domain={[0, 100]} stroke="var(--border)" tick={false} />
          <Radar
            name="Current Session"
            dataKey="current"
            stroke="var(--accent-blue)"
            fill="var(--accent-blue)"
            fillOpacity={0.4}
          />
          <Radar
            name="Trader Baseline"
            dataKey="baseline"
            stroke="var(--text-muted)"
            fill="var(--text-muted)"
            fillOpacity={0.15}
            strokeDasharray="3 3"
          />
          <Legend
            wrapperStyle={{ fontSize: '11px', color: 'var(--text-secondary)' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-secondary)',
              borderColor: 'var(--border)',
              borderRadius: '6px',
              fontSize: '12px',
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
