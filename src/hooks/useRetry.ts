"use client";

import { useState, useCallback, useRef } from "react";

interface RetryOptions {
  maxAttempts?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryCondition?: (error: any) => boolean;
  onRetry?: (attempt: number, error: any) => void;
  onMaxRetriesReached?: (error: any) => void;
}

interface RetryState {
  isRetrying: boolean;
  attempt: number;
  lastError: any;
  nextRetryAt: Date | null;
}

export function useRetry(options: RetryOptions = {}) {
  const {
    maxAttempts = 3,
    baseDelay = 1000,
    maxDelay = 30000,
    backoffMultiplier = 2,
    retryCondition = () => true,
    onRetry,
    onMaxRetriesReached,
  } = options;

  const [retryState, setRetryState] = useState<RetryState>({
    isRetrying: false,
    attempt: 0,
    lastError: null,
    nextRetryAt: null,
  });

  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const calculateDelay = useCallback(
    (attempt: number) => {
      const delay = Math.min(
        baseDelay * Math.pow(backoffMultiplier, attempt - 1),
        maxDelay,
      );
      // Add jitter to prevent thundering herd
      return delay + Math.random() * 1000;
    },
    [baseDelay, backoffMultiplier, maxDelay],
  );

  const executeWithRetry = useCallback(
    async <T>(operation: () => Promise<T>): Promise<T> => {
      let lastError: any;

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          setRetryState((prev) => ({
            ...prev,
            attempt,
            isRetrying: attempt > 1,
          }));

          const result = await operation();

          // Success - reset state
          setRetryState({
            isRetrying: false,
            attempt: 0,
            lastError: null,
            nextRetryAt: null,
          });

          return result;
        } catch (error) {
          lastError = error;

          // Check if we should retry this error
          if (!retryCondition(error)) {
            setRetryState((prev) => ({
              ...prev,
              isRetrying: false,
              lastError: error,
            }));
            throw error;
          }

          // If this was the last attempt, don't delay
          if (attempt === maxAttempts) {
            setRetryState((prev) => ({
              ...prev,
              isRetrying: false,
              lastError: error,
            }));
            onMaxRetriesReached?.(error);
            throw error;
          }

          // Calculate delay and wait before next attempt
          const delay = calculateDelay(attempt);
          const nextRetryAt = new Date(Date.now() + delay);

          setRetryState((prev) => ({
            ...prev,
            lastError: error,
            nextRetryAt,
          }));

          onRetry?.(attempt, error);

          await new Promise((resolve) => {
            timeoutRef.current = setTimeout(resolve, delay);
          });
        }
      }

      throw lastError;
    },
    [maxAttempts, retryCondition, calculateDelay, onRetry, onMaxRetriesReached],
  );

  const manualRetry = useCallback(
    async <T>(operation: () => Promise<T>): Promise<T> => {
      // Reset attempt counter for manual retry
      setRetryState((prev) => ({
        ...prev,
        attempt: 0,
        isRetrying: false,
        lastError: null,
        nextRetryAt: null,
      }));

      return executeWithRetry(operation);
    },
    [executeWithRetry],
  );

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = undefined;
    }
    setRetryState((prev) => ({
      ...prev,
      isRetrying: false,
      nextRetryAt: null,
    }));
  }, []);

  return {
    executeWithRetry,
    manualRetry,
    cancel,
    ...retryState,
    canRetry: retryState.attempt < maxAttempts && !retryState.isRetrying,
  };
}

// Predefined retry configurations for common scenarios
export const RETRY_CONFIGS = {
  // Quick retries for transient errors
  quick: {
    maxAttempts: 3,
    baseDelay: 500,
    maxDelay: 2000,
    backoffMultiplier: 1.5,
  },

  // Standard retries for API calls
  standard: {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 5000,
    backoffMultiplier: 2,
  },

  // Persistent retries for important operations
  persistent: {
    maxAttempts: 5,
    baseDelay: 2000,
    maxDelay: 30000,
    backoffMultiplier: 2,
  },

  // Network-specific retries
  network: {
    maxAttempts: 4,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
    retryCondition: (error: any) => {
      // Retry on network errors, 5xx server errors, and timeouts
      return (
        error.name === "NetworkError" ||
        error.code === "NETWORK_ERROR" ||
        error.code === "TIMEOUT" ||
        (error.response?.status >= 500 && error.response?.status < 600) ||
        error.response?.status === 429 // Rate limited
      );
    },
  },

  // File upload retries
  upload: {
    maxAttempts: 3,
    baseDelay: 2000,
    maxDelay: 15000,
    backoffMultiplier: 2,
    retryCondition: (error: any) => {
      // Don't retry client errors except for rate limiting
      if (error.response?.status >= 400 && error.response?.status < 500) {
        return error.response?.status === 429; // Rate limited
      }
      return true;
    },
  },
} as const;

export default useRetry;
