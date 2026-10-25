import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import type { RiskAssessment } from '../types';

interface Props {
  assessments: RiskAssessment[];
}

export const RiskScoreChart: React.FC<Props> = ({ assessments }) => {
  const data = assessments.map((a, index) => ({
    name: `Step ${index + 1}`,
    score: Number(a.risk_score),
    band: a.risk_band,
  }));

  if (data.length === 0) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
        No risk assessments recorded yet.
      </div>
    );
  }

  const latestScore = data[data.length - 1]?.score || 0;
  const strokeColor =
    latestScore >= 70
      ? 'var(--risk-high)'
      : latestScore >= 40
      ? 'var(--risk-elevated)'
      : 'var(--risk-normal)';

  return (
    <div style={{ width: '100%', height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={strokeColor} stopOpacity={0.4} />
              <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.6} />
          <XAxis
            dataKey="name"
            stroke="var(--text-muted)"
            fontSize={11}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            stroke="var(--text-muted)"
            fontSize={11}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-secondary)',
              borderColor: 'var(--border)',
              borderRadius: '6px',
              fontSize: '12px',
              color: 'var(--text-primary)'
            }}
            formatter={(val: any) => [`${val}/100`, 'Risk Score']}
          />
          {/* Risk Band Reference Lines */}
          <ReferenceLine y={40} stroke="var(--risk-elevated)" strokeDasharray="3 3" label={{ value: 'Elevated (40)', fill: 'var(--risk-elevated)', fontSize: 10 }} />
          <ReferenceLine y={70} stroke="var(--risk-high)" strokeDasharray="3 3" label={{ value: 'High (70)', fill: 'var(--risk-high)', fontSize: 10 }} />

          <Area
            type="monotone"
            dataKey="score"
            stroke={strokeColor}
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#riskGrad)"
            dot={{ r: 3, fill: strokeColor }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
