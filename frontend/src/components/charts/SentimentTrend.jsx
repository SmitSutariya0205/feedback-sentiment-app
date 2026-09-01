import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

/**
 * Line / Area chart visualization showing sentiment confidence trends over time.
 */
export function SentimentTrend({ records = [] }) {
  if (!records || records.length === 0) {
    return (
      <div className="chart-card">
        <h3 className="chart-title">Sentiment Trend Over Time</h3>
        <p className="chart-empty">No trend data available.</p>
      </div>
    );
  }

  // Sort chronologically ascending for line chart
  const sorted = [...records].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  const chartData = sorted.map((item) => ({
    id: item.id,
    date: new Date(item.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    product: item.product_name,
    sentiment: item.sentiment_label,
    confidence: Number((item.confidence_score * 100).toFixed(1)),
    rawScore: item.confidence_score,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3 className="chart-title">Confidence Trend Over Time</h3>
        <span className="chart-badge">Chronological Sequence</span>
      </div>

      <div className="chart-container" style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#94A3B8"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#94A3B8"
              fontSize={11}
              tickFormatter={(v) => `${v}%`}
              axisLine={false}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="custom-tooltip">
                      <p className="tooltip-date">{data.date}</p>
                      <p className="tooltip-product"><strong>Product:</strong> {data.product}</p>
                      <p className="tooltip-sentiment">
                        <strong>Sentiment:</strong>{' '}
                        <span className={`label-${data.sentiment}`}>{data.sentiment}</span>
                      </p>
                      <p className="tooltip-confidence">
                        <strong>Confidence:</strong> {data.confidence}%
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="confidence"
              stroke="#3B82F6"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#confidenceGradient)"
              dot={{ r: 4, fill: '#3B82F6', strokeWidth: 2, stroke: '#0F172A' }}
              activeDot={{ r: 6, fill: '#60A5FA' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
