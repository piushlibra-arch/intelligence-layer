import React from 'react';
import './LoadingSpinner.css';

interface Props {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

export const LoadingSpinner: React.FC<Props> = ({
  message = 'Loading…',
  size = 'medium',
}) => (
  <div className={`loading-spinner loading-spinner--${size}`} role="status" aria-live="polite">
    <div className="loading-spinner__ring" />
    {message && <p className="loading-spinner__message">{message}</p>}
  </div>
);
