/**
 * Centralized Logging Utility
 *
 * Provides structured logging with log levels and environment-aware output.
 * Replaces console.log statements throughout the application.
 *
 * Usage:
 * ```ts
 * import { logger } from '@/utils/logger';
 *
 * logger.debug('User action', { userId, action: 'click' });
 * logger.info('Data loaded successfully', { count: items.length });
 * logger.warn('Deprecated feature used', { feature: 'oldAPI' });
 * logger.error('API request failed', error, { endpoint: '/api/jobs' });
 * ```
 */

type LogLevel = "debug" | "info" | "warn" | "error";

interface LogContext {
  [key: string]: any;
}

class Logger {
  private level: LogLevel;
  private isDevelopment: boolean;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV !== "production";
    // In production, only log warnings and errors
    // In development, log everything
    this.level = this.isDevelopment ? "debug" : "warn";
  }

  /**
   * Log debug information (development only)
   */
  debug(message: string, context?: LogContext): void {
    if (this.shouldLog("debug")) {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] [DEBUG] ${message}`, context || "");
    }
  }

  /**
   * Log informational messages
   */
  info(message: string, context?: LogContext): void {
    if (this.shouldLog("info")) {
      const timestamp = new Date().toISOString();
      console.info(`[${timestamp}] [INFO] ${message}`, context || "");
    }
  }

  /**
   * Log warning messages
   */
  warn(message: string, context?: LogContext): void {
    if (this.shouldLog("warn")) {
      const timestamp = new Date().toISOString();
      console.warn(`[${timestamp}] [WARN] ${message}`, context || "");
    }
  }

  /**
   * Log error messages
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    if (this.shouldLog("error")) {
      const timestamp = new Date().toISOString();
      if (error instanceof Error) {
        console.error(`[${timestamp}] [ERROR] ${message}`, {
          message: error.message,
          stack: error.stack,
          ...context,
        });
      } else {
        console.error(
          `[${timestamp}] [ERROR] ${message}`,
          error,
          context || "",
        );
      }
    }
  }

  /**
   * Set log level programmatically
   */
  setLevel(level: LogLevel): void {
    this.level = level;
  }

  /**
   * Get current log level
   */
  getLevel(): LogLevel {
    return this.level;
  }

  /**
   * Determine if a message should be logged based on current level
   */
  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ["debug", "info", "warn", "error"];
    const currentLevelIndex = levels.indexOf(this.level);
    const messageLevelIndex = levels.indexOf(level);
    return messageLevelIndex >= currentLevelIndex;
  }

  /**
   * Create a child logger with a specific context
   */
  child(defaultContext: LogContext): ChildLogger {
    return new ChildLogger(this, defaultContext);
  }
}

/**
 * Child logger that includes default context in all log messages
 */
class ChildLogger {
  constructor(
    private parent: Logger,
    private defaultContext: LogContext,
  ) {}

  debug(message: string, context?: LogContext): void {
    this.parent.debug(message, { ...this.defaultContext, ...context });
  }

  info(message: string, context?: LogContext): void {
    this.parent.info(message, { ...this.defaultContext, ...context });
  }

  warn(message: string, context?: LogContext): void {
    this.parent.warn(message, { ...this.defaultContext, ...context });
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    this.parent.error(message, error, { ...this.defaultContext, ...context });
  }
}

// Export singleton instance
export const logger = new Logger();

// Export types for use in other files
export type { LogLevel, LogContext };
