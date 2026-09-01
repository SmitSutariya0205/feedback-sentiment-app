import { apiClient } from './client';

/**
 * Submit product feedback text for sentiment analysis.
 *
 * @param {Object} payload
 * @param {string} payload.requestId - Caller-supplied UUID v4
 * @param {number} payload.userId - Numeric user identifier (ge=1)
 * @param {string} payload.productName - Product name (1-200 chars)
 * @param {string} payload.feedbackText - Raw feedback text (5-2000 chars)
 * @returns {Promise<Object>} FeedbackResponse object { id, request_id, user_id, product_name, feedback_text, sentiment_label, confidence_score, created_at }
 */
export async function submitFeedback({ requestId, userId, productName, feedbackText }) {
  const body = {
    request_id: requestId,
    user_id: Number(userId),
    product_name: productName,
    feedback_text: feedbackText,
  };

  // POST /feedback returns APIResponse[FeedbackResponse]
  return await apiClient.post('/feedback', body);
}

/**
 * Retrieve historical feedback records for a given user.
 *
 * @param {number|string} userId - Target numeric user ID
 * @param {string} requestId - UUID v4 tracing ID query param
 * @returns {Promise<Object>} FeedbackListResponse { user_id, total, feedbacks: [...] }
 */
export async function getHistoricalFeedback(userId, requestId) {
  const parsedUserId = Number(userId);

  // GET /feedback/{user_id}?request_id=<uuid>
  return await apiClient.get(`/feedback/${parsedUserId}`, {
    params: { request_id: requestId },
  });
}

/**
 * Health check endpoint (public, unauthenticated).
 *
 * @returns {Promise<Object>} APIResponse
 */
export async function checkHealth() {
  return await apiClient.get('/health');
}
