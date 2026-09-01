import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { HistoricalFeedback } from '../../components/HistoricalFeedback';
import * as feedbackApi from '../../api/feedbackApi';

vi.mock('../../api/feedbackApi');
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  PieChart: ({ children }) => <div>{children}</div>,
  Pie: ({ children }) => <div>{children}</div>,
  Cell: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
  AreaChart: ({ children }) => <div>{children}</div>,
  Area: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
}));


describe('<HistoricalFeedback /> Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input and fetch button', () => {
    render(<HistoricalFeedback />);

    expect(screen.getByPlaceholderText(/Enter numeric User ID/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Fetch History/i })).toBeInTheDocument();
  });

  it('fetches historical records for user ID and renders table + charts', async () => {
    const mockListResult = {
      user_id: 42,
      total: 2,
      feedbacks: [
        {
          id: 1,
          request_id: '550e8400-e29b-41d4-a716-446655440000',
          user_id: 42,
          product_name: 'Widget A',
          feedback_text: 'Awesome product experience!',
          sentiment_label: 'positive',
          confidence_score: 0.95,
          created_at: '2026-08-19T10:00:00Z',
        },
        {
          id: 2,
          request_id: '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
          user_id: 42,
          product_name: 'Widget B',
          feedback_text: 'Terrible performance and broke down.',
          sentiment_label: 'negative',
          confidence_score: 0.88,
          created_at: '2026-08-19T11:00:00Z',
        },
      ],
    };

    feedbackApi.getHistoricalFeedback.mockResolvedValueOnce(mockListResult);

    render(<HistoricalFeedback />);

    const searchInput = screen.getByPlaceholderText(/Enter numeric User ID/i);
    fireEvent.change(searchInput, { target: { value: '42' } });

    fireEvent.click(screen.getByRole('button', { name: /Fetch History/i }));

    await waitFor(() => {
      expect(feedbackApi.getHistoricalFeedback).toHaveBeenCalledWith('42', expect.any(String));
      expect(screen.getByText(/History for User/i)).toBeInTheDocument();
      expect(screen.getByText(/2 Record\(s\) Found/i)).toBeInTheDocument();
      expect(screen.getByText('Widget A')).toBeInTheDocument();
      expect(screen.getByText('Widget B')).toBeInTheDocument();
    });
  });

  it('handles empty historical feedback list gracefully (200 OK with total 0)', async () => {
    const mockEmptyResult = {
      user_id: 99,
      total: 0,
      feedbacks: [],
    };

    feedbackApi.getHistoricalFeedback.mockResolvedValueOnce(mockEmptyResult);

    render(<HistoricalFeedback />);

    fireEvent.change(screen.getByPlaceholderText(/Enter numeric User ID/i), { target: { value: '99' } });
    fireEvent.click(screen.getByRole('button', { name: /Fetch History/i }));

    await waitFor(() => {
      expect(screen.getByText(/0 Record\(s\) Found/i)).toBeInTheDocument();
      expect(screen.getByText(/No Feedback Records Found/i)).toBeInTheDocument();
    });
  });

  it('renders ErrorAlert when retrieval fails with server error', async () => {
    feedbackApi.getHistoricalFeedback.mockRejectedValueOnce({
      statusCode: 500,
      message: 'Failed to retrieve feedback records from database.',
    });

    render(<HistoricalFeedback />);

    fireEvent.change(screen.getByPlaceholderText(/Enter numeric User ID/i), { target: { value: '42' } });
    fireEvent.click(screen.getByRole('button', { name: /Fetch History/i }));

    await waitFor(() => {
      expect(screen.getByText(/Retrieval Failed/i)).toBeInTheDocument();
      expect(screen.getByText(/Failed to retrieve feedback records/i)).toBeInTheDocument();
    });
  });
});
