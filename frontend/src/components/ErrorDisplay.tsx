import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import './ErrorDisplay.css';

interface Props {
  message: string;
  onRetry?: () => void;
}

export const ErrorDisplay: React.FC<Props> = ({ message, onRetry }) => (
  <div className="error-display" role="alert">
    <AlertTriangle className="error-display__icon" size={32} />
    <h3 className="error-display__title">Something went wrong</h3>
    <p className="error-display__message">{message}</p>
    {onRetry && (
      <button className="error-display__retry" onClick={onRetry} aria-label="Retry">
        <RefreshCw size={16} />
        Retry
      </button>
    )}
  </div>
);
