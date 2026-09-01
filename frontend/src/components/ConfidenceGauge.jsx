import React from 'react';

/**
 * Meter & progress gauge for confidence score (0.0 to 1.0).
 */
export function ConfidenceGauge({ score = 0, sentiment = 'neutral' }) {
  const percentage = Math.min(Math.max(Math.round(score * 1000) / 10, 0), 100);

  const getMeterColor = () => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'var(--color-positive)';
      case 'negative':
        return 'var(--color-negative)';
      default:
        return 'var(--color-neutral)';
    }
  };

  return (
    <div className="confidence-gauge">
      <div className="gauge-header">
        <span className="gauge-label">Confidence Score</span>
        <span className="gauge-value">{(score * 100).toFixed(2)}%</span>
      </div>
      <div className="gauge-track">
        <div
          className="gauge-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: getMeterColor(),
          }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin="0"
          aria-valuemax="100"
        />
      </div>
      <div className="gauge-footer">
        <span>0% (Low)</span>
        <span>100% (High)</span>
      </div>
    </div>
  );
}
