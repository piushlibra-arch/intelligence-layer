import React from 'react';
import type { RiskBand } from '../types';
import './RiskGauge.css';

interface Props {
  score: number;
  band: RiskBand;
  size?: number;
}

export const RiskGauge: React.FC<Props> = ({ score, band, size = 180 }) => {
  const center = size / 2;
  const radius = (size - 20) / 2;
  const strokeWidth = 12;
  // Semicircle: from 180° to 360° (or π to 2π)
  const circumference = Math.PI * radius;
  const normalizedScore = Math.min(100, Math.max(0, score));
  const offset = circumference - (normalizedScore / 100) * circumference;

  const bandColor =
    band === 'high'
      ? 'var(--risk-high)'
      : band === 'elevated'
      ? 'var(--risk-elevated)'
      : 'var(--risk-normal)';

  // The arc path for a semicircle (180° sweep from left to right, bottom side)
  const pathD = `M ${center - radius} ${center} A ${radius} ${radius} 0 0 1 ${center + radius} ${center}`;

  return (
    <div className="risk-gauge" style={{ width: size, height: size / 2 + 30 }}>
      <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`}>
        {/* Background track */}
        <path
          d={pathD}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Score arc */}
        <path
          d={pathD}
          fill="none"
          stroke={bandColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.5s ease, stroke 0.3s ease' }}
        />
        {/* Score text */}
        <text
          x={center}
          y={center - 10}
          textAnchor="middle"
          className="risk-gauge__score"
          fill={bandColor}
        >
          {Math.round(normalizedScore)}
        </text>
      </svg>
      <div className="risk-gauge__label" style={{ color: bandColor }}>
        {band.charAt(0).toUpperCase() + band.slice(1)} Risk
      </div>
    </div>
  );
};
