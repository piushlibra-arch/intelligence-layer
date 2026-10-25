import React from 'react';
import type { RiskBand, ActionType } from '../types';
import './StatusBadge.css';

interface Props {
  band?: RiskBand;
  value?: string | RiskBand | ActionType;
  type?: string;
  size?: 'small' | 'medium';
}

export const StatusBadge: React.FC<Props> = ({ band, value, type, size = 'medium' }) => {
  const actualVal = (band || value || 'normal').toLowerCase();

  return (
    <span
      className={`status-badge status-badge--${actualVal} status-badge--${size} ${type ? `badge--${type}` : ''}`}
      aria-label={`Status: ${actualVal}`}
    >
      {actualVal.replace(/_/g, ' ').toUpperCase()}
    </span>
  );
};
