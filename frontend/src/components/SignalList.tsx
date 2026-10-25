import React from 'react';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import type { RiskSignal } from '../types';
import './SignalList.css';

interface Props {
  signals: RiskSignal[];
}

export const SignalList: React.FC<Props> = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return (
      <div className="signal-list-empty">
        <Info size={18} className="signal-icon--info" />
        <span>No risk escalation signals active.</span>
      </div>
    );
  }

  const getSeverityIcon = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'high':
        return <AlertTriangle size={16} className="signal-icon signal-icon--high" />;
      case 'medium':
        return <AlertCircle size={16} className="signal-icon signal-icon--medium" />;
      default:
        return <Info size={16} className="signal-icon signal-icon--low" />;
    }
  };

  return (
    <div className="signal-list">
      {signals.map((sig, idx) => (
        <div key={`${sig.name}-${idx}`} className={`signal-item signal-item--${sig.severity.toLowerCase()}`}>
          <div className="signal-item__header">
            <div className="signal-item__title-row">
              {getSeverityIcon(sig.severity)}
              <span className="signal-name">{sig.name.replace(/_/g, ' ')}</span>
            </div>
            <span className={`signal-badge signal-badge--${sig.severity.toLowerCase()}`}>
              {sig.severity}
            </span>
          </div>
          <p className="signal-desc">{sig.description}</p>
        </div>
      ))}
    </div>
  );
};
