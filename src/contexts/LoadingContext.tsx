/**
 * Loading Context for Context-Aware Loading Messages
 * Provides centralized loading state management with context-specific messaging
 */

import React, { createContext, useContext, useState, useCallback } from "react";

export type LoadingContext =
  | "dashboard"
  | "jobs"
  | "search"
  | "comparison"
  | "upload"
  | "job-details"
  | "stats"
  | "processing"
  | "generic";

interface LoadingMessage {
  title: string;
  description: string;
}

const LOADING_MESSAGES: Record<LoadingContext, LoadingMessage> = {
  dashboard: {
    title: "Loading Dashboard",
    description: "Preparing your job description overview...",
  },
  jobs: {
    title: "Loading Jobs",
    description: "Fetching job descriptions from database...",
  },
  search: {
    title: "Searching",
    description: "Finding matching job descriptions...",
  },
  comparison: {
    title: "Analyzing Jobs",
    description: "Comparing job descriptions and requirements...",
  },
  upload: {
    title: "Processing Upload",
    description: "Analyzing and extracting job description content...",
  },
  "job-details": {
    title: "Loading Details",
    description: "Retrieving job description and sections...",
  },
  stats: {
    title: "Loading Statistics",
    description: "Calculating database metrics and insights...",
  },
  processing: {
    title: "Processing",
    description: "Analyzing content and extracting information...",
  },
  generic: {
    title: "Loading JDDB",
    description: "Preparing your job description database...",
  },
};

interface LoadingContextType {
  context: LoadingContext;
  getMessage: () => LoadingMessage;
  setContext: (context: LoadingContext) => void;
  setCustomMessage: (title: string, description?: string) => void;
  clearCustomMessage: () => void;
}

const LoadingStateContext = createContext<LoadingContextType | undefined>(
  undefined,
);

interface LoadingProviderProps {
  children: React.ReactNode;
  initialContext?: LoadingContext;
}

export function LoadingProvider({
  children,
  initialContext = "generic",
}: LoadingProviderProps) {
  const [context, setContext] = useState<LoadingContext>(initialContext);
  const [customMessage, setCustomMessage] = useState<LoadingMessage | null>(
    null,
  );

  const getMessage = useCallback((): LoadingMessage => {
    if (customMessage) {
      return customMessage;
    }
    return LOADING_MESSAGES[context];
  }, [context, customMessage]);

  const setCustomMessageHandler = useCallback(
    (title: string, description?: string) => {
      setCustomMessage({
        title,
        description:
          description || "Please wait while we complete this operation...",
      });
    },
    [],
  );

  const clearCustomMessage = useCallback(() => {
    setCustomMessage(null);
  }, []);

  const value: LoadingContextType = {
    context,
    getMessage,
    setContext,
    setCustomMessage: setCustomMessageHandler,
    clearCustomMessage,
  };

  return (
    <LoadingStateContext.Provider value={value}>
      {children}
    </LoadingStateContext.Provider>
  );
}

export function useLoadingContext(): LoadingContextType {
  const context = useContext(LoadingStateContext);
  if (!context) {
    throw new Error("useLoadingContext must be used within a LoadingProvider");
  }
  return context;
}

/**
 * Hook for easy loading message management in components
 */
export function useLoadingMessage() {
  const { setContext, setCustomMessage, clearCustomMessage, getMessage } =
    useLoadingContext();

  const setJobsLoading = useCallback(() => setContext("jobs"), [setContext]);
  const setSearchLoading = useCallback(
    () => setContext("search"),
    [setContext],
  );
  const setComparisonLoading = useCallback(
    () => setContext("comparison"),
    [setContext],
  );
  const setUploadLoading = useCallback(
    () => setContext("upload"),
    [setContext],
  );
  const setJobDetailsLoading = useCallback(
    () => setContext("job-details"),
    [setContext],
  );
  const setStatsLoading = useCallback(() => setContext("stats"), [setContext]);
  const setProcessingLoading = useCallback(
    () => setContext("processing"),
    [setContext],
  );
  const setDashboardLoading = useCallback(
    () => setContext("dashboard"),
    [setContext],
  );

  return {
    getMessage,
    setJobsLoading,
    setSearchLoading,
    setComparisonLoading,
    setUploadLoading,
    setJobDetailsLoading,
    setStatsLoading,
    setProcessingLoading,
    setDashboardLoading,
    setCustomMessage,
    clearCustomMessage,
  };
}
