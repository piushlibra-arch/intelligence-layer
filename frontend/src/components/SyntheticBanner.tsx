import React from 'react';
import './SyntheticBanner.css';

export const SyntheticBanner: React.FC = () => (
  <div className="synthetic-banner" role="alert">
    <span className="synthetic-banner__icon">⚠️</span>
    <span className="synthetic-banner__text">
      <strong>SYNTHETIC DATA</strong> — This prototype uses simulated trading data for demonstration purposes only
    </span>
  </div>
);
