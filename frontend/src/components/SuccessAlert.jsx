import React from 'react';

/**
 * Reusable Success Alert component.
 */
export function SuccessAlert({ title = 'Success', message, onClose }) {
  if (!message) return null;

  return (
    <div className="alert-card alert-success" role="status">
      <div className="alert-icon">✅</div>
      <div className="alert-content">
        <h4 className="alert-title">{title}</h4>
        <p className="alert-message">{message}</p>
      </div>
      {onClose && (
        <button type="button" className="btn-close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      )}
    </div>
  );
}
