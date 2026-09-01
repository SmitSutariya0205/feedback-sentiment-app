import React from 'react';

/**
 * Colored badge component for sentiment label (positive, negative, neutral).
 */
export function SentimentBadge({ label, size = 'medium' }) {
  const normalizedLabel = (label || 'neutral').toLowerCase();

  const config = {
    positive: {
      text: 'Positive',
      icon: '😊',
      className: 'badge-positive',
    },
    negative: {
      text: 'Negative',
      icon: '😞',
      className: 'badge-negative',
    },
    neutral: {
      text: 'Neutral',
      icon: '😐',
      className: 'badge-neutral',
    },
  };

  const current = config[normalizedLabel] || config.neutral;

  return (
    <span className={`sentiment-badge ${current.className} badge-${size}`}>
      <span className="badge-icon">{current.icon}</span>
      <span className="badge-text">{current.text}</span>
    </span>
  );
}
