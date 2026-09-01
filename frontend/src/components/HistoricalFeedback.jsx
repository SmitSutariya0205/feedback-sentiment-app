import React, { useState } from 'react';
import { generateRequestId } from '../utils/uuid';
import { getHistoricalFeedback } from '../api/feedbackApi';
import { useApiRequest } from '../hooks/useApiRequest';
import { FeedbackTable } from './FeedbackTable';
import { ErrorAlert } from './ErrorAlert';
import { LoadingSpinner } from './LoadingSpinner';
import { SentimentDistribution } from './charts/SentimentDistribution';
import { SentimentTrend } from './charts/SentimentTrend';
import { ConfidenceAverage } from './charts/ConfidenceAverage';

export function HistoricalFeedback() {
  const [searchUserId, setSearchUserId] = useState('1');
  const [activeUserId, setActiveUserId] = useState(null);

  const { execute, data, isLoading, error, isSuccess } = useApiRequest(getHistoricalFeedback);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchUserId || Number(searchUserId) < 1) return;

    const reqId = generateRequestId();
    setActiveUserId(searchUserId);

    try {
      await execute(searchUserId, reqId);
    } catch (err) {
      // Error handled by useApiRequest
    }
  };

  const records = data?.feedbacks || [];
  const totalRecords = data?.total ?? 0;

  return (
    <div className="historical-feedback-container">
      <div className="card search-card">
        <div className="card-header">
          <h2 className="card-title">Retrieve Historical Feedback</h2>
          <p className="card-subtitle">
            Enter a User ID to fetch all previous product feedback records and sentiment analytics.
          </p>
        </div>

        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <label htmlFor="searchUserId" className="form-label sr-only">
              User ID
            </label>
            <div className="input-prefix-wrapper">
              <span className="input-prefix">👤 User ID:</span>
              <input
                type="number"
                id="searchUserId"
                min="1"
                step="1"
                value={searchUserId}
                onChange={(e) => setSearchUserId(e.target.value)}
                placeholder="Enter numeric User ID (e.g. 42)"
                className="form-input search-input"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              className="btn-primary btn-search"
              disabled={isLoading || !searchUserId}
            >
              {isLoading ? <LoadingSpinner message="" size="small" /> : 'Fetch History'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <ErrorAlert
          title="Retrieval Failed"
          message={error.message}
          onRetry={handleSearch}
        />
      )}

      {isLoading && <LoadingSpinner message="Querying FastAPI database..." size="large" />}

      {!isLoading && isSuccess && (
        <div className="history-results animate-fade-in">
          <div className="results-meta-bar">
            <h3 className="results-header-title">
              History for User <span className="highlight-user">#{activeUserId}</span>
            </h3>
            <span className="results-count-badge">{totalRecords} Record(s) Found</span>
          </div>

          {/* Render Visualizations if data exists */}
          {records.length > 0 && (
            <div className="analytics-section">
              <h3 className="section-subtitle">Sentiment Analytics & Visualizations</h3>
              <div className="charts-grid">
                <SentimentDistribution records={records} />
                <SentimentTrend records={records} />
                <ConfidenceAverage records={records} />
              </div>
            </div>
          )}

          {/* Render Table */}
          <div className="card table-card">
            <h3 className="section-subtitle">Feedback Records</h3>
            <FeedbackTable records={records} />
          </div>
        </div>
      )}
    </div>
  );
}
