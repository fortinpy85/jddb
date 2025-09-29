/**
 * Progress Toast Utilities
 * Provides easy-to-use functions for showing progress feedback during long operations
 */

import { useToast } from "@/components/ui/toast";
import { useCallback } from "react";

export interface ProgressOptions {
  title: string;
  description?: string;
  estimatedDuration?: number; // in milliseconds
  showPercentage?: boolean;
  type?: "success" | "error" | "warning" | "info";
}

export interface ProgressController {
  updateProgress: (value: number, description?: string, estimatedTimeRemaining?: string) => void;
  complete: (message?: string) => void;
  error: (message: string) => void;
  cancel: () => void;
}

/**
 * Hook for creating and managing progress toasts
 */
export function useProgressToast() {
  const { addToast, updateToast, removeToast } = useToast();

  const createProgressToast = useCallback((options: ProgressOptions): ProgressController => {
    const toastId = Math.random().toString(36).substr(2, 9);

    // Add initial toast
    addToast({
      title: options.title,
      description: options.description,
      type: options.type || "info",
      duration: 0, // Don't auto-remove
      progress: {
        value: 0,
        showPercentage: options.showPercentage !== false,
        estimatedTimeRemaining: options.estimatedDuration ? formatDuration(options.estimatedDuration) : undefined
      }
    });

    let startTime = Date.now();
    let lastUpdateTime = startTime;

    const updateProgress = (value: number, description?: string, estimatedTimeRemaining?: string) => {
      const now = Date.now();
      const elapsed = now - startTime;
      const progressRate = value / elapsed; // progress per ms

      let timeRemaining: string | undefined = estimatedTimeRemaining;

      // Auto-calculate estimated time if not provided and we have meaningful progress
      if (!estimatedTimeRemaining && value > 5 && value < 95) {
        const remainingProgress = 100 - value;
        const estimatedRemainingMs = remainingProgress / progressRate;
        timeRemaining = formatDuration(estimatedRemainingMs);
      }

      updateToast(toastId, {
        description,
        progress: {
          value: Math.min(100, Math.max(0, value)),
          showPercentage: options.showPercentage !== false,
          estimatedTimeRemaining: timeRemaining
        }
      });

      lastUpdateTime = now;
    };

    const complete = (message?: string) => {
      updateToast(toastId, {
        title: `${options.title} - Complete`,
        description: message || "Operation completed successfully",
        type: "success",
        duration: 5000, // Auto-remove after 5 seconds
        progress: {
          value: 100,
          showPercentage: false
        }
      });
    };

    const error = (message: string) => {
      updateToast(toastId, {
        title: `${options.title} - Error`,
        description: message,
        type: "error",
        duration: 0, // Don't auto-remove errors
        progress: undefined // Remove progress bar on error
      });
    };

    const cancel = () => {
      removeToast(toastId);
    };

    return {
      updateProgress,
      complete,
      error,
      cancel
    };
  }, [addToast, updateToast, removeToast]);

  return {
    createProgressToast
  };
}

/**
 * Utility functions for common progress patterns
 */
export function useProgressUtils() {
  const { createProgressToast } = useProgressToast();

  // File upload progress
  const createUploadProgress = useCallback((fileName: string) => {
    return createProgressToast({
      title: "Uploading File",
      description: `Uploading ${fileName}...`,
      showPercentage: true,
      type: "info"
    });
  }, [createProgressToast]);

  // Batch operation progress
  const createBatchProgress = useCallback((operationName: string, totalItems: number) => {
    return createProgressToast({
      title: operationName,
      description: `Processing ${totalItems} items...`,
      showPercentage: true,
      type: "info"
    });
  }, [createProgressToast]);

  // Search/analysis progress
  const createAnalysisProgress = useCallback((analysisType: string) => {
    return createProgressToast({
      title: `${analysisType} Analysis`,
      description: "Analyzing job descriptions...",
      showPercentage: false, // Analysis might not have clear percentage progress
      type: "info"
    });
  }, [createProgressToast]);

  // Comparison progress
  const createComparisonProgress = useCallback((jobCount: number) => {
    return createProgressToast({
      title: "Job Comparison",
      description: `Comparing ${jobCount} job descriptions...`,
      showPercentage: true,
      type: "info"
    });
  }, [createProgressToast]);

  return {
    createUploadProgress,
    createBatchProgress,
    createAnalysisProgress,
    createComparisonProgress
  };
}

/**
 * Format duration in milliseconds to human-readable string
 */
function formatDuration(ms: number): string {
  if (ms < 1000) return "< 1s";
  if (ms < 60000) return `${Math.round(ms / 1000)}s`;
  if (ms < 3600000) return `${Math.round(ms / 60000)}m`;
  return `${Math.round(ms / 3600000)}h`;
}

/**
 * Create a progress tracker for operations with known steps
 */
export function createStepProgress(steps: string[]): (currentStep: number, customMessage?: string) => number {
  return (currentStep: number, customMessage?: string) => {
    const progress = (currentStep / steps.length) * 100;
    const stepMessage = customMessage || `Step ${currentStep + 1} of ${steps.length}: ${steps[currentStep]}`;
    return progress;
  };
}