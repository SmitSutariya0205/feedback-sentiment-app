import React from 'react';

/**
 * Reusable Error Alert component for presenting user-friendly error messages.
 */
export function ErrorAlert({ title = 'Operation Failed', message, onRetry, requestId }) {
  if (!message) return null;

  return (
    <div className="alert-card alert-error" role="alert">
      <div className="alert-icon">⚠️</div>
      <div className="alert-content">
        <h4 className="alert-title">{title}</h4>
        <p className="alert-message">{message}</p>
        {requestId && requestId !== 'N/A' && (
          <div className="alert-meta">
            <span className="meta-label">Request ID:</span> <code>{requestId}</code>
          </div>
        )}
      </div>
      {onRetry && (
        <button type="button" className="btn-retry" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
}
