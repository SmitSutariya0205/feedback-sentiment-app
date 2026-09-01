import axios from 'axios';
import { config } from '../config';
import { handleApiError } from '../utils/errorHandler';
import { logger } from '../utils/logger';

/**
 * Dedicated Axios client instance for FastAPI backend communication.
 */
export const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: config.requestTimeoutMs,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request Interceptor: Automatically attach Bearer token to all protected requests
apiClient.interceptors.request.use(
  (reqConfig) => {
    // Attach static Bearer token
    if (config.apiBearerToken) {
      reqConfig.headers.Authorization = `Bearer ${config.apiBearerToken}`;
    }

    logger.debug(`[HTTP Outgoing] ${reqConfig.method?.toUpperCase()} ${reqConfig.url}`, {
      url: reqConfig.url,
      method: reqConfig.method,
      params: reqConfig.params,
    });

    return reqConfig;
  },
  (error) => {
    logger.error('[HTTP Request Setup Error]', { error });
    return Promise.reject(error);
  }
);

// Response Interceptor: Unwrap universal APIResponse envelope & transform HTTP errors
apiClient.interceptors.response.use(
  (response) => {
    const apiResponse = response.data;

    logger.debug(`[HTTP Response] ${response.status} ${response.config.url}`, {
      status: response.status,
      apiSuccess: apiResponse?.success,
    });

    // Check backend APIResponse envelope structure
    if (apiResponse && typeof apiResponse.success === 'boolean') {
      if (!apiResponse.success) {
        throw handleApiError(
          {
            response,
            statusCode: apiResponse.status_code || response.status,
            message: apiResponse.error_message || apiResponse.message,
          },
          `API Call: ${response.config.url}`
        );
      }
      // Return the inner payload data directly for callers
      return apiResponse.data;
    }

    // Direct payload fallback
    return apiResponse;
  },
  (error) => {
    const context = `API Call: ${error.config?.url || 'Unknown'}`;
    const formattedError = handleApiError(error, context);
    return Promise.reject(formattedError);
  }
);
