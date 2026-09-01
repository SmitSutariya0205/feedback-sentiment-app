import { logger } from './logger';

/**
 * Custom Error class for API response errors.
 */
export class ApiError extends Error {
  constructor(message, statusCode, originalError = null, technicalDetail = null, requestId = null) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.originalError = originalError;
    this.technicalDetail = technicalDetail;
    this.requestId = requestId;
  }
}

/**
 * Process any caught exception and extract a clean, user-friendly error message
 * while logging the raw technical traceback to console.
 */
export function handleApiError(error, contextInfo = 'API Operation') {
  let userMessage = 'An unexpected error occurred. Please try again.';
  let statusCode = error.response?.status || error.statusCode || 500;
  let technicalDetail = '';
  let requestId = error.requestId || error.config?.headers?.['X-Request-ID'] || 'N/A';

  // 1. Connection Failure / Network Error (backend offline, CORS blocked, etc.)
  if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
    statusCode = 0;
    userMessage = 'Unable to connect to the backend server. Please verify the backend is running.';
    technicalDetail = `Network Error (code: ${error.code}) during ${contextInfo}`;
  }
  // 2. Request Timeout
  else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    statusCode = 408;
    userMessage = 'The request timed out. The server took too long to respond.';
    technicalDetail = `Request timeout after ${error.config?.timeout || 'configured'} ms during ${contextInfo}`;
  }
  // 3. Server Responded with APIResponse envelope containing status code & error_message
  else if (error.response?.data) {
    const apiResp = error.response.data;
    statusCode = error.response.status || apiResp.status_code || statusCode;
    technicalDetail = apiResp.error_message || apiResp.message || JSON.stringify(apiResp);

    switch (statusCode) {
      case 401:
        userMessage = 'Authentication failed. Please verify your static Bearer token configuration.';
        break;
      case 422:
        // FastAPI validation error — display specific field errors provided by backend
        userMessage = apiResp.error_message || 'Validation failed. Please check the input fields.';
        break;
      case 404:
        userMessage = apiResp.error_message || 'The requested resource was not found.';
        break;
      case 500:
        userMessage = apiResp.error_message || 'Internal server error. Please try again later.';
        break;
      default:
        userMessage = apiResp.error_message || apiResp.message || userMessage;
    }
  }
  // 4. Custom ApiError instance
  else if (error instanceof ApiError) {
    userMessage = error.message;
    statusCode = error.statusCode;
    technicalDetail = error.technicalDetail || error.message;
  }
  // 5. Native JS error
  else if (error.message) {
    technicalDetail = error.message;
    userMessage = error.message;
  }

  // Structured logging of technical details (never hidden from developer/logs)
  logger.error(`[${contextInfo}] Error (${statusCode}): ${technicalDetail}`, {
    statusCode,
    technicalDetail,
    requestId,
    stack: error.stack,
    config: error.config ? { url: error.config.url, method: error.config.method } : null,
  });

  return new ApiError(userMessage, statusCode, error, technicalDetail, requestId);
}
