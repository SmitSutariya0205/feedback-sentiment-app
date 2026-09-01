import React from 'react';

/**
 * Reusable Loading Spinner component.
 */
export function LoadingSpinner({ message = 'Loading...', size = 'medium' }) {
  return (
    <div className={`loading-container size-${size}`}>
      <div className="spinner-ring" aria-label="Loading indicator">
        <div></div>
        <div></div>
        <div></div>
        <div></div>
      </div>
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
}
