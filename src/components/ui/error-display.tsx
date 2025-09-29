"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertTriangle,
  RefreshCw,
  Home,
  HelpCircle,
  ExternalLink,
  Copy,
  Bug,
  Wifi,
  Server,
  Shield,
  FileX,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface ErrorAction {
  label: string;
  action: () => void;
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  icon?: React.ComponentType<{ className?: string }>;
}

export interface ErrorSolution {
  title: string;
  description: string;
  actions?: ErrorAction[];
}

interface ErrorDisplayProps {
  title?: string;
  message: string;
  errorCode?: string;
  type?:
    | "network"
    | "server"
    | "permission"
    | "validation"
    | "file"
    | "generic";
  solutions?: ErrorSolution[];
  onRetry?: () => void;
  onGoHome?: () => void;
  className?: string;
  showStackTrace?: boolean;
  stackTrace?: string;
}

const errorTypeConfig = {
  network: {
    icon: Wifi,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    defaultTitle: "Network Connection Error",
    defaultSolutions: [
      {
        title: "Check your internet connection",
        description:
          "Make sure you're connected to the internet and try again.",
        actions: [
          {
            label: "Retry",
            action: () => window.location.reload(),
            icon: RefreshCw,
          },
        ],
      },
      {
        title: "Server may be temporarily unavailable",
        description:
          "Our servers might be experiencing issues. Please try again in a few minutes.",
      },
    ],
  },
  server: {
    icon: Server,
    color: "text-red-600",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    defaultTitle: "Server Error",
    defaultSolutions: [
      {
        title: "Server is experiencing issues",
        description:
          "Our team has been notified and is working to resolve this issue.",
        actions: [
          {
            label: "Try Again",
            action: () => window.location.reload(),
            icon: RefreshCw,
          },
        ],
      },
    ],
  },
  permission: {
    icon: Shield,
    color: "text-yellow-600",
    bgColor: "bg-yellow-50",
    borderColor: "border-yellow-200",
    defaultTitle: "Permission Denied",
    defaultSolutions: [
      {
        title: "You don't have permission to access this resource",
        description:
          "Contact your administrator if you believe you should have access.",
        actions: [
          {
            label: "Go Home",
            action: () => (window.location.href = "/"),
            icon: Home,
          },
        ],
      },
    ],
  },
  validation: {
    icon: AlertTriangle,
    color: "text-amber-600",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    defaultTitle: "Validation Error",
    defaultSolutions: [
      {
        title: "Please check your input",
        description: "Make sure all required fields are filled out correctly.",
      },
    ],
  },
  file: {
    icon: FileX,
    color: "text-purple-600",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    defaultTitle: "File Error",
    defaultSolutions: [
      {
        title: "File could not be processed",
        description: "Please check the file format and try uploading again.",
        actions: [
          {
            label: "Try Again",
            action: () => window.location.reload(),
            icon: RefreshCw,
          },
        ],
      },
    ],
  },
  generic: {
    icon: Bug,
    color: "text-gray-600",
    bgColor: "bg-gray-50",
    borderColor: "border-gray-200",
    defaultTitle: "Something went wrong",
    defaultSolutions: [
      {
        title: "An unexpected error occurred",
        description:
          "Please try refreshing the page or contact support if the problem persists.",
        actions: [
          {
            label: "Refresh Page",
            action: () => window.location.reload(),
            icon: RefreshCw,
          },
        ],
      },
    ],
  },
};

export function ErrorDisplay({
  title,
  message,
  errorCode,
  type = "generic",
  solutions,
  onRetry,
  onGoHome,
  className,
  showStackTrace = false,
  stackTrace,
}: ErrorDisplayProps) {
  const config = errorTypeConfig[type];
  const Icon = config.icon;

  const displayTitle = title || config.defaultTitle;
  const displaySolutions = solutions || config.defaultSolutions;

  const copyErrorDetails = () => {
    const errorDetails = `
Error: ${displayTitle}
Message: ${message}
${errorCode ? `Code: ${errorCode}` : ""}
${stackTrace ? `Stack Trace: ${stackTrace}` : ""}
Time: ${new Date().toISOString()}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}
    `.trim();

    navigator.clipboard.writeText(errorDetails);
  };

  return (
    <div className={cn("max-w-2xl mx-auto p-6", className)}>
      <Card className={cn("border-2", config.borderColor)}>
        <CardHeader className={config.bgColor}>
          <CardTitle className="flex items-center gap-3">
            <Icon className={cn("h-6 w-6", config.color)} />
            <span className={config.color}>{displayTitle}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <Alert className="mb-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              {message}
              {errorCode && (
                <span className="block mt-1 text-xs text-muted-foreground">
                  Error Code: {errorCode}
                </span>
              )}
            </AlertDescription>
          </Alert>

          {displaySolutions && displaySolutions.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-sm">How to fix this:</h3>
              {displaySolutions.map(
                (solution: ErrorSolution, index: number) => (
                  <div key={index} className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-medium text-sm mb-2">
                      {solution.title}
                    </h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      {solution.description}
                    </p>
                    {solution.actions && solution.actions.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {solution.actions.map(
                          (action: ErrorAction, actionIndex: number) => {
                            const ActionIcon = action.icon;
                            return (
                              <Button
                                key={actionIndex}
                                variant={action.variant || "outline"}
                                size="sm"
                                onClick={action.action}
                                className="h-8"
                              >
                                {ActionIcon && (
                                  <ActionIcon className="h-3 w-3 mr-1" />
                                )}
                                {action.label}
                              </Button>
                            );
                          },
                        )}
                      </div>
                    )}
                  </div>
                ),
              )}
            </div>
          )}

          <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t">
            {onRetry && (
              <Button variant="default" size="sm" onClick={onRetry}>
                <RefreshCw className="h-3 w-3 mr-1" />
                Try Again
              </Button>
            )}
            {onGoHome && (
              <Button variant="outline" size="sm" onClick={onGoHome}>
                <Home className="h-3 w-3 mr-1" />
                Go Home
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={copyErrorDetails}>
              <Copy className="h-3 w-3 mr-1" />
              Copy Error Details
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href="mailto:support@example.com?subject=Error Report">
                <HelpCircle className="h-3 w-3 mr-1" />
                Contact Support
              </a>
            </Button>
          </div>

          {showStackTrace && stackTrace && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-muted-foreground">
                Technical Details
              </summary>
              <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto max-h-40">
                {stackTrace}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Hook for managing error state with automatic retry logic
export function useErrorHandler() {
  const [error, setError] = React.useState<{
    message: string;
    type?: ErrorDisplayProps["type"];
    code?: string;
    retryCount?: number;
  } | null>(null);

  const handleError = React.useCallback(
    (message: string, type?: ErrorDisplayProps["type"], code?: string) => {
      setError({ message, type, code, retryCount: 0 });
    },
    [],
  );

  const retry = React.useCallback(() => {
    if (error) {
      setError({ ...error, retryCount: (error.retryCount || 0) + 1 });
    }
  }, [error]);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    handleError,
    retry,
    clearError,
    hasError: !!error,
    retryCount: error?.retryCount || 0,
  };
}

export default ErrorDisplay;
