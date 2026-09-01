import React, { useState } from 'react';
import { SentimentBadge } from './SentimentBadge';

/**
 * Reusable table for displaying historical feedback records.
 */
export function FeedbackTable({ records = [] }) {
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');

  if (!records || records.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📭</div>
        <h4 className="empty-title">No Feedback Records Found</h4>
        <p className="empty-subtitle">
          This user has not submitted any product feedback yet.
        </p>
      </div>
    );
  }

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedRecords = [...records].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];

    if (sortField === 'created_at') {
      valA = new Date(valA).getTime();
      valB = new Date(valB).getTime();
    }

    if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
    if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div className="table-responsive">
      <table className="feedback-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('id')} className="sortable">
              ID {sortField === 'id' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
            </th>
            <th onClick={() => handleSort('product_name')} className="sortable">
              Product {sortField === 'product_name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
            </th>
            <th>Feedback Text</th>
            <th onClick={() => handleSort('sentiment_label')} className="sortable">
              Sentiment {sortField === 'sentiment_label' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
            </th>
            <th onClick={() => handleSort('confidence_score')} className="sortable">
              Confidence {sortField === 'confidence_score' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
            </th>
            <th onClick={() => handleSort('created_at')} className="sortable">
              Date & Time {sortField === 'created_at' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedRecords.map((item) => (
            <tr key={item.id}>
              <td className="cell-id">#{item.id}</td>
              <td className="cell-product">{item.product_name}</td>
              <td className="cell-feedback">
                <span className="feedback-text-snippet" title={item.feedback_text}>
                  {item.feedback_text}
                </span>
              </td>
              <td className="cell-sentiment">
                <SentimentBadge label={item.sentiment_label} size="small" />
              </td>
              <td className="cell-confidence">
                <div className="table-confidence-bar">
                  <span className="confidence-num">{(item.confidence_score * 100).toFixed(1)}%</span>
                  <div className="mini-track">
                    <div
                      className={`mini-fill fill-${item.sentiment_label}`}
                      style={{ width: `${Math.min(item.confidence_score * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </td>
              <td className="cell-date">
                {new Date(item.created_at).toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
