import { describe, it, expect, vi, beforeEach } from 'vitest';
import { submitFeedback, getHistoricalFeedback } from '../../api/feedbackApi';
import { apiClient } from '../../api/client';

vi.mock('../../api/client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('Feedback API endpoints', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('submitFeedback', () => {
    it('should format payload correctly and invoke POST /feedback', async () => {
      const mockResult = {
        id: 1,
        request_id: '550e8400-e29b-41d4-a716-446655440000',
        user_id: 42,
        product_name: 'Widget Pro',
        feedback_text: 'Great product!',
        sentiment_label: 'positive',
        confidence_score: 0.95,
        created_at: '2026-08-19T10:00:00Z',
      };

      apiClient.post.mockResolvedValueOnce(mockResult);

      const payload = {
        requestId: '550e8400-e29b-41d4-a716-446655440000',
        userId: '42',
        productName: 'Widget Pro',
        feedbackText: 'Great product!',
      };

      const result = await submitFeedback(payload);

      expect(apiClient.post).toHaveBeenCalledWith('/feedback', {
        request_id: '550e8400-e29b-41d4-a716-446655440000',
        user_id: 42,
        product_name: 'Widget Pro',
        feedback_text: 'Great product!',
      });
      expect(result).toEqual(mockResult);
    });
  });

  describe('getHistoricalFeedback', () => {
    it('should invoke GET /feedback/{user_id} with request_id query parameter', async () => {
      const mockListResult = {
        user_id: 42,
        total: 1,
        feedbacks: [
          {
            id: 1,
            request_id: '550e8400-e29b-41d4-a716-446655440000',
            user_id: 42,
            product_name: 'Widget Pro',
            feedback_text: 'Great product!',
            sentiment_label: 'positive',
            confidence_score: 0.95,
            created_at: '2026-08-19T10:00:00Z',
          },
        ],
      };

      apiClient.get.mockResolvedValueOnce(mockListResult);

      const result = await getHistoricalFeedback(42, '550e8400-e29b-41d4-a716-446655440000');

      expect(apiClient.get).toHaveBeenCalledWith('/feedback/42', {
        params: { request_id: '550e8400-e29b-41d4-a716-446655440000' },
      });
      expect(result).toEqual(mockListResult);
    });
  });
});
