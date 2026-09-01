import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook to manage asynchronous API operation state cleanly.
 * Guarantees proper loading, success, and error states so the UI never appears frozen.
 *
 * @param {Function} apiFunc - Async function to execute
 * @returns {Object} { data, error, isLoading, isSuccess, isError, execute, reset }
 */
export function useApiRequest(apiFunc) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
    setIsSuccess(false);
  }, []);

  const execute = useCallback(
    async (...args) => {
      setIsLoading(true);
      setError(null);
      setIsSuccess(false);

      try {
        const result = await apiFunc(...args);

        if (isMountedRef.current) {
          setData(result);
          setIsSuccess(true);
          setIsLoading(false);
        }
        return result;
      } catch (err) {
        if (isMountedRef.current) {
          setError(err);
          setIsSuccess(false);
          setIsLoading(false);
        }
        throw err;
      }
    },
    [apiFunc]
  );

  return {
    data,
    error,
    isLoading,
    isSuccess,
    isError: Boolean(error),
    execute,
    reset,
  };
}
