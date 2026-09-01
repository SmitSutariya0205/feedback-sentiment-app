import React, { useState, useEffect } from 'react';
import { generateRequestId, isValidUuid } from '../utils/uuid';
import { submitFeedback } from '../api/feedbackApi';
import { useApiRequest } from '../hooks/useApiRequest';
import { FeedbackResult } from './FeedbackResult';
import { ErrorAlert } from './ErrorAlert';
import { LoadingSpinner } from './LoadingSpinner';

export function FeedbackForm() {
  const [formData, setFormData] = useState({
    userId: '1',
    requestId: '',
    productName: '',
    feedbackText: '',
  });

  const [validationErrors, setValidationErrors] = useState({});
  const [submittedResult, setSubmittedResult] = useState(null);

  const { execute, isLoading, error, reset: resetApiState } = useApiRequest(submitFeedback);

  // Initialize Request ID with a valid UUID v4
  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      requestId: generateRequestId(),
    }));
  }, []);

  const handleRegenerateUuid = () => {
    setFormData((prev) => ({
      ...prev,
      requestId: generateRequestId(),
    }));
    setValidationErrors((prev) => ({ ...prev, requestId: null }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear validation error when user edits field
    if (validationErrors[name]) {
      setValidationErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const errors = {};

    // 1. User ID validation (numeric, ge=1)
    const parsedUserId = Number(formData.userId);
    if (!formData.userId || isNaN(parsedUserId) || !Number.isInteger(parsedUserId) || parsedUserId < 1) {
      errors.userId = 'User ID must be a positive integer greater than or equal to 1.';
    }

    // 2. Request ID validation (valid UUID v4)
    if (!formData.requestId || !isValidUuid(formData.requestId.trim())) {
      errors.requestId = 'Request ID must be a valid UUID v4 (e.g. 550e8400-e29b-41d4-a716-446655440000).';
    }

    // 3. Product Name validation (1 to 200 chars)
    const trimmedProduct = formData.productName.trim();
    if (!trimmedProduct) {
      errors.productName = 'Product name is required.';
    } else if (trimmedProduct.length > 200) {
      errors.productName = 'Product name must not exceed 200 characters.';
    }

    // 4. Feedback Text validation (5 to 2000 chars)
    const trimmedFeedback = formData.feedbackText.trim();
    if (!trimmedFeedback) {
      errors.feedbackText = 'Feedback text is required.';
    } else if (trimmedFeedback.length < 5) {
      errors.feedbackText = 'Feedback text must be at least 5 characters long.';
    } else if (trimmedFeedback.length > 2000) {
      errors.feedbackText = 'Feedback text must not exceed 2000 characters.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmittedResult(null);
    resetApiState();

    if (!validate()) {
      return;
    }

    try {
      const result = await execute({
        requestId: formData.requestId.trim(),
        userId: Number(formData.userId),
        productName: formData.productName.trim(),
        feedbackText: formData.feedbackText.trim(),
      });

      setSubmittedResult(result);

      // Refresh request_id for next submission
      setFormData((prev) => ({
        ...prev,
        requestId: generateRequestId(),
      }));
    } catch (err) {
      // Error is caught and stored in useApiRequest state
    }
  };

  return (
    <div className="feedback-form-container">
      <form className="card form-card" onSubmit={handleSubmit} noValidate>
        <div className="card-header">
          <h2 className="card-title">Submit Product Feedback</h2>
          <p className="card-subtitle">
            Enter feedback details for VADER sentiment analysis processing.
          </p>
        </div>

        {error && (
          <ErrorAlert
            title="Submission Error"
            message={error.message}
            requestId={formData.requestId}
          />
        )}

        <div className="form-grid">
          {/* User ID field */}
          <div className="form-group">
            <label htmlFor="userId" className="form-label">
              User ID <span className="required">*</span>
            </label>
            <input
              type="number"
              id="userId"
              name="userId"
              min="1"
              step="1"
              value={formData.userId}
              onChange={handleChange}
              placeholder="e.g. 42"
              className={`form-input ${validationErrors.userId ? 'input-error' : ''}`}
              disabled={isLoading}
            />
            {validationErrors.userId && (
              <span className="field-error">{validationErrors.userId}</span>
            )}
          </div>

          {/* Request ID field with UUID regeneration */}
          <div className="form-group">
            <label htmlFor="requestId" className="form-label">
              Request Tracing ID (UUID v4) <span className="required">*</span>
            </label>
            <div className="input-group">
              <input
                type="text"
                id="requestId"
                name="requestId"
                value={formData.requestId}
                onChange={handleChange}
                placeholder="550e8400-e29b-41d4-a716-446655440000"
                className={`form-input code-font ${validationErrors.requestId ? 'input-error' : ''}`}
                disabled={isLoading}
              />
              <button
                type="button"
                className="btn-secondary btn-icon"
                onClick={handleRegenerateUuid}
                title="Generate new UUID"
                disabled={isLoading}
              >
                🔄
              </button>
            </div>
            {validationErrors.requestId && (
              <span className="field-error">{validationErrors.requestId}</span>
            )}
          </div>

          {/* Product Name field */}
          <div className="form-group full-width">
            <label htmlFor="productName" className="form-label">
              Product Name <span className="required">*</span>
            </label>
            <input
              type="text"
              id="productName"
              name="productName"
              maxLength={200}
              value={formData.productName}
              onChange={handleChange}
              placeholder="e.g. Wireless Noise-Canceling Headphones"
              className={`form-input ${validationErrors.productName ? 'input-error' : ''}`}
              disabled={isLoading}
            />
            <div className="field-hint-row">
              {validationErrors.productName ? (
                <span className="field-error">{validationErrors.productName}</span>
              ) : (
                <span className="field-hint">Between 1 and 200 characters</span>
              )}
              <span className="char-counter">{formData.productName.length}/200</span>
            </div>
          </div>

          {/* Feedback Text field */}
          <div className="form-group full-width">
            <label htmlFor="feedbackText" className="form-label">
              Feedback Text <span className="required">*</span>
            </label>
            <textarea
              id="feedbackText"
              name="feedbackText"
              rows={5}
              maxLength={2000}
              value={formData.feedbackText}
              onChange={handleChange}
              placeholder="Describe your experience with the product in detail (minimum 5 characters)..."
              className={`form-textarea ${validationErrors.feedbackText ? 'input-error' : ''}`}
              disabled={isLoading}
            />
            <div className="field-hint-row">
              {validationErrors.feedbackText ? (
                <span className="field-error">{validationErrors.feedbackText}</span>
              ) : (
                <span className="field-hint">Between 5 and 2000 characters</span>
              )}
              <span className="char-counter">{formData.feedbackText.length}/2000</span>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? <LoadingSpinner message="Analyzing Sentiment..." size="small" /> : 'Analyze Sentiment'}
          </button>
        </div>
      </form>

      {/* Render Sentiment Analysis Result when returned */}
      {submittedResult && <FeedbackResult result={submittedResult} />}
    </div>
  );
}
