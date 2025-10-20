// Structured logger for critical paths
export type LogLevel = "info" | "warn" | "error" | "debug";

declare global {
  interface Window {
    ToastProvider?: {
      show: (message: string, options?: { type?: string }) => void;
    };
  }
}

export function log(
  level: LogLevel,
  message: string,
  context?: Record<string, any>,
) {
  const output = { level, message, ...context };
  if (level === "error") {
    // Optionally send to Sentry if DSN present
    // Sentry.captureException(message, context);
    // Show user-facing toast if available
    if (typeof window !== "undefined" && window.ToastProvider) {
      window.ToastProvider.show(message, { type: "error" });
    }
  }
  console[level === "error" ? "error" : "log"](output);
}
