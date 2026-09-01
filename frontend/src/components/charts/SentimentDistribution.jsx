import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

/**
 * Donut chart visualization for sentiment distribution (positive, negative, neutral).
 */
export function SentimentDistribution({ records = [] }) {
  const counts = records.reduce(
    (acc, item) => {
      const label = (item.sentiment_label || 'neutral').toLowerCase();
      if (acc[label] !== undefined) {
        acc[label] += 1;
      }
      return acc;
    },
    { positive: 0, negative: 0, neutral: 0 }
  );

  const data = [
    { name: 'Positive', value: counts.positive, color: '#10b981' },
    { name: 'Negative', value: counts.negative, color: '#ef4444' },
    { name: 'Neutral', value: counts.neutral, color: '#f59e0b' },
  ].filter((item) => item.value > 0);

  if (records.length === 0 || data.length === 0) {
    return (
      <div className="chart-card">
        <h3 className="chart-title">Sentiment Breakdown</h3>
        <p className="chart-empty">No sentiment data available for visualization.</p>
      </div>
    );
  }

  const total = records.length;

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3 className="chart-title">Sentiment Distribution</h3>
        <span className="chart-badge">{total} Total Feedback</span>
      </div>

      <div className="chart-container" style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="var(--color-bg-card)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [
                `${value} record(s) (${((value / total) * 100).toFixed(1)}%)`,
                name,
              ]}
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#F8FAFC',
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              formatter={(value) => <span style={{ color: '#94A3B8', fontSize: '0.85rem' }}>{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-stats-grid">
        <div className="stat-pill stat-pos">
          <span className="stat-label">Positive</span>
          <span className="stat-value">{counts.positive} ({((counts.positive / total) * 100).toFixed(0)}%)</span>
        </div>
        <div className="stat-pill stat-neu">
          <span className="stat-label">Neutral</span>
          <span className="stat-value">{counts.neutral} ({((counts.neutral / total) * 100).toFixed(0)}%)</span>
        </div>
        <div className="stat-pill stat-neg">
          <span className="stat-label">Negative</span>
          <span className="stat-value">{counts.negative} ({((counts.negative / total) * 100).toFixed(0)}%)</span>
        </div>
      </div>
    </div>
  );
}
