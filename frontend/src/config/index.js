/**
 * Centralized application configuration.
 * Reads environment variables defined with VITE_ prefix.
 */
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'https://feedback-backend-smit0205.azurewebsites.net',
  apiBearerToken: import.meta.env.VITE_API_BEARER_TOKEN || 'dev-secret-token',
  requestTimeoutMs: 15000, // 15 seconds request timeout
  logLevel: import.meta.env.VITE_LOG_LEVEL || 'info', // debug | info | warn | error
};
