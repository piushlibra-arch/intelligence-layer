import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import './MetricCard.css';

interface Props {
  label?: string;
  title?: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  accent?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<Props> = ({
  label,
  title,
  value,
  subtitle,
  trend,
  trendValue,
  accent = 'blue',
  icon,
}) => {
  const displayLabel = title || label || '';
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  return (
    <div className={`metric-card metric-card--${accent}`}>
      <div className="metric-card__header">
        <span className="metric-card__label">{displayLabel}</span>
        {icon && <span className="metric-card__icon">{icon}</span>}
      </div>
      <div className="metric-card__value">{value}</div>
      {subtitle && <div className="metric-card__subtitle">{subtitle}</div>}
      {trend && trendValue && (
        <div className={`metric-card__trend metric-card__trend--${trend}`}>
          <TrendIcon size={14} />
          <span>{trendValue}</span>
        </div>
      )}
    </div>
  );
};
