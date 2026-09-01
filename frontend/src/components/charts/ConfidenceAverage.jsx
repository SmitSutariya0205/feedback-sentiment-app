import React from 'react';

/**
 * KPI card summary displaying average confidence score and sentiment metrics.
 */
export function ConfidenceAverage({ records = [] }) {
  if (!records || records.length === 0) {
    return (
      <div className="chart-card kpi-card">
        <h3 className="chart-title">Confidence Summary</h3>
        <p className="chart-empty">No historical metrics.</p>
      </div>
    );
  }

  const scores = records.map((r) => r.confidence_score);
  const avg = scores.reduce((sum, val) => sum + val, 0) / scores.length;
  const max = Math.max(...scores);
  const min = Math.min(...scores);

  const avgPercentage = (avg * 100).toFixed(2);
  const maxPercentage = (max * 100).toFixed(1);
  const minPercentage = (min * 100).toFixed(1);

  return (
    <div className="chart-card kpi-card">
      <div className="chart-header">
        <h3 className="chart-title">Average Confidence</h3>
        <span className="kpi-icon">🎯</span>
      </div>

      <div className="kpi-main-display">
        <div className="kpi-score">{avgPercentage}%</div>
        <div className="kpi-subtext">Overall VADER Model Certainty</div>
      </div>

      <div className="kpi-metrics-grid">
        <div className="kpi-metric-item">
          <span className="kpi-metric-label">Total Analysed</span>
          <span className="kpi-metric-value">{records.length}</span>
        </div>
        <div className="kpi-metric-item">
          <span className="kpi-metric-label">Max Certainty</span>
          <span className="kpi-metric-value text-positive">{maxPercentage}%</span>
        </div>
        <div className="kpi-metric-item">
          <span className="kpi-metric-label">Min Certainty</span>
          <span className="kpi-metric-value text-neutral">{minPercentage}%</span>
        </div>
      </div>
    </div>
  );
}
