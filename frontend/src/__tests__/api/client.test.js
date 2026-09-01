import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import { apiClient } from '../../api/client';
import { handleApiError, ApiError } from '../../utils/errorHandler';

vi.mock('../../config', () => ({
  config: {
    apiBaseUrl: 'http://localhost:8000',
    apiBearerToken: 'test-secret-token',
    requestTimeoutMs: 5000,
  },
}));

describe('API Client & Error Handler', () => {
  it('should automatically attach Bearer token to request headers', async () => {
    // Interceptor test
    const mockConfig = { headers: {} };
    const requestInterceptor = apiClient.interceptors.request.handlers[0].fulfilled;
    const modifiedConfig = requestInterceptor(mockConfig);

    expect(modifiedConfig.headers.Authorization).toBe('Bearer test-secret-token');
  });

  describe('handleApiError status code & error mapping', () => {
    it('should handle 401 Unauthorized errors properly', () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            success: false,
            status_code: 401,
            message: 'Unauthorized',
            error_message: 'Invalid or missing Bearer token',
            data: null,
          },
        },
      };

      const err = handleApiError(mockError, 'Test 401');
      expect(err).toBeInstanceOf(ApiError);
      expect(err.statusCode).toBe(401);
      expect(err.message).toContain('Authentication failed');
    });

    it('should handle 422 Validation errors properly', () => {
      const mockError = {
        response: {
          status: 422,
          data: {
            success: false,
            status_code: 422,
            message: 'Validation Error',
            error_message: 'feedback_text: String should have at least 5 characters',
            data: null,
          },
        },
      };

      const err = handleApiError(mockError, 'Test 422');
      expect(err.statusCode).toBe(422);
      expect(err.message).toBe('feedback_text: String should have at least 5 characters');
    });

    it('should handle 404 Not Found errors properly', () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            success: false,
            status_code: 404,
            message: 'Not Found',
            error_message: 'Resource not found',
            data: null,
          },
        },
      };

      const err = handleApiError(mockError, 'Test 404');
      expect(err.statusCode).toBe(404);
      expect(err.message).toContain('Resource not found');
    });

    it('should handle 500 Internal Server errors properly', () => {
      const mockError = {
        response: {
          status: 500,
          data: {
            success: false,
            status_code: 500,
            message: 'Internal Server Error',
            error_message: 'Sentiment analysis failed: VADER model crashed',
            data: null,
          },
        },
      };

      const err = handleApiError(mockError, 'Test 500');
      expect(err.statusCode).toBe(500);
      expect(err.message).toBe('Sentiment analysis failed: VADER model crashed');
    });

    it('should handle connection failure (ERR_NETWORK)', () => {
      const mockError = {
        code: 'ERR_NETWORK',
        message: 'Network Error',
      };

      const err = handleApiError(mockError, 'Test Connection Failure');
      expect(err.statusCode).toBe(0);
      expect(err.message).toContain('Unable to connect to the backend server');
    });

    it('should handle request timeout (ECONNABORTED)', () => {
      const mockError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded',
        config: { timeout: 5000 },
      };

      const err = handleApiError(mockError, 'Test Timeout');
      expect(err.statusCode).toBe(408);
      expect(err.message).toContain('request timed out');
    });
  });
});
