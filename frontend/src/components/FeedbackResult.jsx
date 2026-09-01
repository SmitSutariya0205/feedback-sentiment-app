import React from 'react';
import { SentimentBadge } from './SentimentBadge';
import { ConfidenceGauge } from './ConfidenceGauge';

/**
 * Display returned sentiment analysis results clearly after feedback submission.
 */
export function FeedbackResult({ result }) {
  if (!result) return null;

  const {
    id,
    request_id,
    user_id,
    product_name,
    feedback_text,
    sentiment_label,
    confidence_score,
    created_at,
  } = result;

  const formattedDate = created_at
    ? new Date(created_at).toLocaleString('en-US', {
        dateStyle: 'medium',
        timeStyle: 'medium',
      })
    : new Date().toLocaleString();

  return (
    <div className="feedback-result-card animate-fade-in">
      <div className="result-header">
        <h3 className="result-title">Analysis Result</h3>
        <SentimentBadge label={sentiment_label} size="large" />
      </div>

      <div className="result-gauge-section">
        <ConfidenceGauge score={confidence_score} sentiment={sentiment_label} />
      </div>

      <div className="result-details-grid">
        <div className="detail-item">
          <span className="detail-label">Record ID</span>
          <span className="detail-value">#{id}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">User ID</span>
          <span className="detail-value">{user_id}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Product Name</span>
          <span className="detail-value">{product_name}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Processed At</span>
          <span className="detail-value">{formattedDate}</span>
        </div>
        <div className="detail-item detail-full">
          <span className="detail-label">Request Tracing ID</span>
          <code className="detail-value code-block">{request_id}</code>
        </div>
        <div className="detail-item detail-full">
          <span className="detail-label">Feedback Analyzed</span>
          <blockquote className="detail-feedback-quote">{feedback_text}</blockquote>
        </div>
      </div>
    </div>
  );
}
