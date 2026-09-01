import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FeedbackForm } from '../../components/FeedbackForm';
import * as feedbackApi from '../../api/feedbackApi';

vi.mock('../../api/feedbackApi');

describe('<FeedbackForm /> Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all form input fields correctly', () => {
    render(<FeedbackForm />);

    expect(screen.getByLabelText(/User ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Request Tracing ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Product Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Feedback Text/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Sentiment/i })).toBeInTheDocument();
  });

  it('triggers client-side validation errors when invalid inputs are provided', async () => {
    render(<FeedbackForm />);

    const userIdInput = screen.getByLabelText(/User ID/i);
    const productNameInput = screen.getByLabelText(/Product Name/i);
    const feedbackTextInput = screen.getByLabelText(/Feedback Text/i);
    const submitBtn = screen.getByRole('button', { name: /Analyze Sentiment/i });

    // Set invalid inputs
    fireEvent.change(userIdInput, { target: { value: '-5' } });
    fireEvent.change(productNameInput, { target: { value: '' } });
    fireEvent.change(feedbackTextInput, { target: { value: 'Bad' } }); // < 5 chars

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/User ID must be a positive integer/i)).toBeInTheDocument();
      expect(screen.getByText(/Product name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Feedback text must be at least 5 characters/i)).toBeInTheDocument();
    });

    expect(feedbackApi.submitFeedback).not.toHaveBeenCalled();
  });

  it('submits valid data successfully and renders sentiment result', async () => {
    const mockResponse = {
      id: 101,
      request_id: '550e8400-e29b-41d4-a716-446655440000',
      user_id: 42,
      product_name: 'Super Gadget',
      feedback_text: 'This is an awesome gadget! I really enjoy using it.',
      sentiment_label: 'positive',
      confidence_score: 0.9421,
      created_at: '2026-08-19T12:00:00Z',
    };

    feedbackApi.submitFeedback.mockResolvedValueOnce(mockResponse);

    render(<FeedbackForm />);

    fireEvent.change(screen.getByLabelText(/User ID/i), { target: { value: '42' } });
    fireEvent.change(screen.getByLabelText(/Product Name/i), { target: { value: 'Super Gadget' } });
    fireEvent.change(screen.getByLabelText(/Feedback Text/i), {
      target: { value: 'This is an awesome gadget! I really enjoy using it.' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Analyze Sentiment/i }));

    await waitFor(() => {
      expect(feedbackApi.submitFeedback).toHaveBeenCalledTimes(1);
      expect(screen.getByText(/Analysis Result/i)).toBeInTheDocument();
      expect(screen.getByText(/Positive/i)).toBeInTheDocument();
      expect(screen.getByText(/94.21%/i)).toBeInTheDocument();
    });
  });

  it('displays ErrorAlert when API fails with 401 Unauthorized', async () => {
    feedbackApi.submitFeedback.mockRejectedValueOnce({
      statusCode: 401,
      message: 'Authentication failed. Please verify your static Bearer token configuration.',
      requestId: '550e8400-e29b-41d4-a716-446655440000',
    });

    render(<FeedbackForm />);

    fireEvent.change(screen.getByLabelText(/User ID/i), { target: { value: '42' } });
    fireEvent.change(screen.getByLabelText(/Product Name/i), { target: { value: 'Widget Pro' } });
    fireEvent.change(screen.getByLabelText(/Feedback Text/i), {
      target: { value: 'Valid feedback text here.' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Analyze Sentiment/i }));

    await waitFor(() => {
      expect(screen.getByText(/Submission Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Authentication failed/i)).toBeInTheDocument();
    });
  });

  it('displays ErrorAlert when connection to backend server fails', async () => {
    feedbackApi.submitFeedback.mockRejectedValueOnce({
      statusCode: 0,
      message: 'Unable to connect to the backend server. Please verify the backend is running.',
    });

    render(<FeedbackForm />);

    fireEvent.change(screen.getByLabelText(/User ID/i), { target: { value: '42' } });
    fireEvent.change(screen.getByLabelText(/Product Name/i), { target: { value: 'Widget Pro' } });
    fireEvent.change(screen.getByLabelText(/Feedback Text/i), {
      target: { value: 'Valid feedback text here.' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Analyze Sentiment/i }));

    await waitFor(() => {
      expect(screen.getByText(/Unable to connect to the backend server/i)).toBeInTheDocument();
    });
  });
});
