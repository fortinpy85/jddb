/**
 * AlertBanner Component
 * Displays critical system messages below the top header
 * Supports dismissible alerts with actions
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import {
  AlertCircle,
  Info,
  CheckCircle,
  XCircle,
  X,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export type AlertVariant = "info" | "success" | "warning" | "error";

interface AlertAction {
  label: string;
  onClick: () => void;
  variant?: "default" | "outline" | "ghost";
}

export interface AlertBannerProps {
  variant?: AlertVariant;
  title?: string;
  message: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  actions?: AlertAction[];
  className?: string;
  icon?: React.ComponentType<{ className?: string }>;
  showIcon?: boolean;
  /** If true, uses relative positioning instead of fixed (for embedding in layouts) */
  relative?: boolean;
}

const variantConfig: Record<
  AlertVariant,
  {
    icon: React.ComponentType<{ className?: string }>;
    containerClass: string;
    iconClass: string;
    titleClass: string;
    messageClass: string;
  }
> = {
  info: {
    icon: Info,
    containerClass:
      "bg-blue-50/90 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800/50",
    iconClass: "text-blue-600 dark:text-blue-400",
    titleClass: "text-blue-900 dark:text-blue-200",
    messageClass: "text-blue-800 dark:text-blue-300",
  },
  success: {
    icon: CheckCircle,
    containerClass:
      "bg-green-50/90 dark:bg-green-950/30 border-green-200 dark:border-green-800/50",
    iconClass: "text-green-600 dark:text-green-400",
    titleClass: "text-green-900 dark:text-green-200",
    messageClass: "text-green-800 dark:text-green-300",
  },
  warning: {
    icon: AlertTriangle,
    containerClass:
      "bg-amber-50/90 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800/50",
    iconClass: "text-amber-600 dark:text-amber-400",
    titleClass: "text-amber-900 dark:text-amber-200",
    messageClass: "text-amber-800 dark:text-amber-300",
  },
  error: {
    icon: XCircle,
    containerClass:
      "bg-red-50/90 dark:bg-red-950/30 border-red-200 dark:border-red-800/50",
    iconClass: "text-red-600 dark:text-red-400",
    titleClass: "text-red-900 dark:text-red-200",
    messageClass: "text-red-800 dark:text-red-300",
  },
};

export function AlertBanner({
  variant = "info",
  title,
  message,
  dismissible = true,
  onDismiss,
  actions = [],
  className,
  icon: CustomIcon,
  showIcon = true,
  relative = false,
}: AlertBannerProps) {
  const [isVisible, setIsVisible] = useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  if (!isVisible) return null;

  const config = variantConfig[variant];
  const Icon = CustomIcon || config.icon;

  return (
    <div
      className={cn(
        // Base styles - conditional positioning
        relative ? "relative w-full" : "fixed top-16 left-0 right-0 z-40",
        "border-b",
        "backdrop-blur-sm",
        "shadow-card",
        "animate-in slide-in-from-top duration-300",
        config.containerClass,
        className,
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-start gap-3">
          {/* Icon */}
          {showIcon && (
            <Icon
              className={cn("w-5 h-5 mt-0.5 flex-shrink-0", config.iconClass)}
            />
          )}

          {/* Content */}
          <div className="flex-1 min-w-0">
            {title && (
              <h3
                className={cn("text-sm font-semibold mb-1", config.titleClass)}
              >
                {title}
              </h3>
            )}
            <p className={cn("text-sm", config.messageClass)}>{message}</p>

            {/* Actions */}
            {actions.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {actions.map((action, index) => (
                  <Button
                    key={index}
                    variant={action.variant || "outline"}
                    size="sm"
                    onClick={action.onClick}
                    className="h-8 shadow-button"
                  >
                    {action.label}
                  </Button>
                ))}
              </div>
            )}
          </div>

          {/* Dismiss Button */}
          {dismissible && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className={cn(
                "p-1 h-auto flex-shrink-0 hover:bg-black/5 dark:hover:bg-white/10",
                config.iconClass,
              )}
              aria-label="Dismiss alert"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * AlertBannerStack Component
 * Manages multiple alert banners with stacking
 */
export interface Alert {
  id: string;
  variant?: AlertVariant;
  title?: string;
  message: string;
  dismissible?: boolean;
  actions?: AlertAction[];
  icon?: React.ComponentType<{ className?: string }>;
  showIcon?: boolean;
}

interface AlertBannerStackProps {
  alerts: Alert[];
  onDismiss: (id: string) => void;
  maxVisible?: number;
  className?: string;
}

export function AlertBannerStack({
  alerts,
  onDismiss,
  maxVisible = 3,
  className,
}: AlertBannerStackProps) {
  const visibleAlerts = alerts.slice(0, maxVisible);

  if (visibleAlerts.length === 0) return null;

  return (
    <div
      className={cn("fixed top-16 left-0 right-0 z-40 space-y-0", className)}
    >
      {visibleAlerts.map((alert, index) => (
        <div
          key={alert.id}
          style={{
            transform: `translateY(${index * 4}px)`,
            opacity: 1 - index * 0.15,
          }}
          className="transition-all duration-300"
        >
          <AlertBanner
            variant={alert.variant}
            title={alert.title}
            message={alert.message}
            dismissible={alert.dismissible}
            onDismiss={() => onDismiss(alert.id)}
            actions={alert.actions}
            icon={alert.icon}
            showIcon={alert.showIcon}
          />
        </div>
      ))}
    </div>
  );
}

export default AlertBanner;
