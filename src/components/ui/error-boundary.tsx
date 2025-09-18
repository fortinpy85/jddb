"use client";

import React, { Component, type ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home, Bug } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
  isolate?: boolean;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };

    this.resetErrorBoundary = this.resetErrorBoundary.bind(this);
    this.handleRetry = this.handleRetry.bind(this);
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorId = Math.random().toString(36).substr(2, 9);

    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    const { onError } = this.props;

    this.setState({
      errorInfo,
    });

    // Log error details
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }

    // Report to error tracking service (e.g., Sentry) if needed
    if (typeof window !== "undefined" && (window as any).__SENTRY__) {
      (window as any).__SENTRY__.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
      });
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    const { resetOnPropsChange, resetKeys } = this.props;
    const { hasError } = this.state;

    if (hasError && prevProps !== this.props) {
      // Error just occurred
      return;
    }

    if (hasError && resetOnPropsChange) {
      // Check if any reset keys changed
      const hasResetKeyChanged = resetKeys?.some(
        (resetKey, idx) => prevProps.resetKeys?.[idx] !== resetKey,
      );

      if (hasResetKeyChanged) {
        this.resetErrorBoundary();
      }
    }
  }

  resetErrorBoundary(): void {
    if (this.resetTimeoutId) {
      window.clearTimeout(this.resetTimeoutId);
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  }

  handleRetry(): void {
    // Add a small delay to prevent immediate re-error
    this.resetTimeoutId = window.setTimeout(() => {
      this.resetErrorBoundary();
    }, 250);
  }

  handleReload(): void {
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  }

  handleGoHome(): void {
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  }

  render(): ReactNode {
    const { hasError, error, errorInfo, errorId } = this.state;
    const {
      children,
      fallback,
      showDetails = false,
      isolate = false,
    } = this.props;

    if (hasError) {
      // Custom fallback UI provided
      if (fallback) {
        return fallback;
      }

      // Default error UI
      return (
        <div
          className={cn(
            "flex items-center justify-center p-6",
            isolate ? "min-h-[200px]" : "min-h-screen",
            "bg-gray-50",
          )}
        >
          <Card className="w-full max-w-2xl">
            <CardContent className="p-8 text-center">
              <div className="mb-6">
                <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Oops! Something went wrong
                </h2>
                <p className="text-gray-600 mb-4">
                  We encountered an unexpected error. Don't worry, it's not your
                  fault.
                </p>
                {errorId && (
                  <p className="text-sm text-gray-500 font-mono mb-6">
                    Error ID: {errorId}
                  </p>
                )}
              </div>

              <div className="flex flex-wrap gap-3 justify-center mb-6">
                <Button onClick={this.handleRetry} variant="default" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>

                <Button onClick={this.handleReload} variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reload Page
                </Button>

                <Button onClick={this.handleGoHome} variant="outline" size="sm">
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </Button>
              </div>

              {showDetails && error && (
                <details className="text-left bg-gray-100 rounded-lg p-4 mt-6">
                  <summary className="cursor-pointer text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <Bug className="h-4 w-4 mr-2" />
                    Technical Details
                  </summary>

                  <div className="mt-3 space-y-3 text-sm">
                    <div>
                      <strong className="text-red-600">Error:</strong>
                      <pre className="mt-1 p-2 bg-red-50 rounded text-xs font-mono overflow-x-auto text-red-800">
                        {error.name}: {error.message}
                      </pre>
                    </div>

                    {error.stack && (
                      <div>
                        <strong className="text-red-600">Stack Trace:</strong>
                        <pre className="mt-1 p-2 bg-red-50 rounded text-xs font-mono overflow-x-auto text-red-800">
                          {error.stack}
                        </pre>
                      </div>
                    )}

                    {errorInfo?.componentStack && (
                      <div>
                        <strong className="text-red-600">
                          Component Stack:
                        </strong>
                        <pre className="mt-1 p-2 bg-red-50 rounded text-xs font-mono overflow-x-auto text-red-800">
                          {errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              <div className="mt-6 text-xs text-gray-500">
                If this problem persists, please contact support with the error
                ID above.
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return children;
  }
}

// Hook-based error boundary for functional components
export function useErrorHandler() {
  return React.useCallback((error: Error, errorInfo?: React.ErrorInfo) => {
    console.error("Unhandled error:", error, errorInfo);

    // You can integrate with error reporting services here
    if (typeof window !== "undefined" && (window as any).__SENTRY__) {
      (window as any).__SENTRY__.captureException(error, {
        contexts: errorInfo
          ? {
              react: {
                componentStack: errorInfo.componentStack,
              },
            }
          : undefined,
      });
    }
  }, []);
}

// Wrapper component for easy use
interface ErrorBoundaryWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
  showDetails?: boolean;
  isolate?: boolean;
}

export function ErrorBoundaryWrapper({
  children,
  fallback,
  showDetails = process.env.NODE_ENV === "development",
  isolate = true,
}: ErrorBoundaryWrapperProps) {
  const errorHandler = useErrorHandler();

  return (
    <ErrorBoundary
      onError={errorHandler}
      fallback={fallback}
      showDetails={showDetails}
      isolate={isolate}
    >
      {children}
    </ErrorBoundary>
  );
}

export default ErrorBoundary;
