/**
 * JDDB State Components
 * Consistent loading, error, and empty states with JDDB branding
 */

"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Database,
  AlertCircle,
  RefreshCw,
  Search,
  Upload,
  FileText,
  Wifi,
  WifiOff,
  CheckCircle,
  XCircle,
  Clock,
  Loader2
} from "lucide-react";

/**
 * Loading State Component
 */
interface LoadingStateProps {
  size?: "sm" | "md" | "lg";
  message?: string;
  showLogo?: boolean;
  className?: string;
  variant?: "spinner" | "pulse" | "skeleton";
}

export function LoadingState({
  size = "md",
  message = "Loading...",
  showLogo = true,
  className,
  variant = "spinner"
}: LoadingStateProps) {
  const sizes = {
    sm: { container: "py-8", spinner: "w-6 h-6", logo: "w-4 h-4", text: "text-sm" },
    md: { container: "py-16", spinner: "w-8 h-8", logo: "w-6 h-6", text: "text-base" },
    lg: { container: "py-24", spinner: "w-12 h-12", logo: "w-8 h-8", text: "text-lg" }
  };

  const sizeConfig = sizes[size];

  const renderSpinner = () => (
    <div className="relative">
      <div className={cn(
        "border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin",
        sizeConfig.spinner
      )}></div>
      {showLogo && (
        <Database className={cn(
          "absolute inset-0 m-auto text-blue-600",
          sizeConfig.logo
        )} />
      )}
    </div>
  );

  const renderPulse = () => (
    <div className="flex space-x-2">
      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: "0.1s" }}></div>
      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }}></div>
    </div>
  );

  const renderSkeleton = () => (
    <div className="space-y-3">
      <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4 animate-pulse"></div>
      <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2 animate-pulse"></div>
      <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3 animate-pulse"></div>
    </div>
  );

  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center space-y-4",
      sizeConfig.container,
      className
    )}>
      {variant === "spinner" && renderSpinner()}
      {variant === "pulse" && renderPulse()}
      {variant === "skeleton" && renderSkeleton()}

      <div className="space-y-2">
        <p className={cn(
          "font-medium text-slate-700 dark:text-slate-300",
          sizeConfig.text
        )}>
          {message}
        </p>
        {showLogo && variant !== "spinner" && (
          <div className="flex items-center justify-center space-x-2 text-blue-600">
            <Database className="w-4 h-4" />
            <span className="text-sm font-medium">JDDB</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Error State Component
 */
interface ErrorStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
  showRetry?: boolean;
  className?: string;
  variant?: "error" | "warning" | "network";
}

export function ErrorState({
  title = "Something went wrong",
  message = "We encountered an error while loading your data.",
  actionLabel = "Try Again",
  onAction,
  showRetry = true,
  className,
  variant = "error"
}: ErrorStateProps) {
  const variants = {
    error: {
      icon: XCircle,
      iconColor: "text-red-500",
      bgColor: "bg-red-50 dark:bg-red-900/20",
      borderColor: "border-red-200 dark:border-red-800"
    },
    warning: {
      icon: AlertCircle,
      iconColor: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-900/20",
      borderColor: "border-amber-200 dark:border-amber-800"
    },
    network: {
      icon: WifiOff,
      iconColor: "text-slate-500",
      bgColor: "bg-slate-50 dark:bg-slate-900/20",
      borderColor: "border-slate-200 dark:border-slate-800"
    }
  };

  const config = variants[variant];
  const Icon = config.icon;

  return (
    <div className={cn("py-16", className)}>
      <Card className={cn(
        "max-w-md mx-auto p-8 text-center",
        config.bgColor,
        config.borderColor
      )}>
        <div className="space-y-6">
          <div className="flex justify-center">
            <div className={cn(
              "p-4 rounded-full",
              config.bgColor
            )}>
              <Icon className={cn("w-8 h-8", config.iconColor)} />
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {title}
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              {message}
            </p>
          </div>

          {showRetry && (
            <div className="space-y-3">
              <Button
                onClick={onAction}
                className="w-full"
                variant="outline"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                {actionLabel}
              </Button>

              <div className="flex items-center justify-center space-x-2 text-blue-600">
                <Database className="w-4 h-4" />
                <span className="text-sm font-medium">JDDB</span>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}


/**
 * Status Indicator Component
 */
interface StatusIndicatorProps {
  status: "loading" | "success" | "error" | "warning" | "processing";
  message?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function StatusIndicator({
  status,
  message,
  size = "md",
  className
}: StatusIndicatorProps) {
  const variants = {
    loading: {
      icon: Loader2,
      color: "text-blue-500",
      bgColor: "bg-blue-100 dark:bg-blue-900/20",
      animate: "animate-spin"
    },
    success: {
      icon: CheckCircle,
      color: "text-green-500",
      bgColor: "bg-green-100 dark:bg-green-900/20",
      animate: ""
    },
    error: {
      icon: XCircle,
      color: "text-red-500",
      bgColor: "bg-red-100 dark:bg-red-900/20",
      animate: ""
    },
    warning: {
      icon: AlertCircle,
      color: "text-amber-500",
      bgColor: "bg-amber-100 dark:bg-amber-900/20",
      animate: ""
    },
    processing: {
      icon: Clock,
      color: "text-purple-500",
      bgColor: "bg-purple-100 dark:bg-purple-900/20",
      animate: "animate-pulse"
    }
  };

  const config = variants[status];
  const Icon = config.icon;

  const sizes = {
    sm: { container: "p-2", icon: "w-4 h-4", text: "text-xs" },
    md: { container: "p-3", icon: "w-5 h-5", text: "text-sm" },
    lg: { container: "p-4", icon: "w-6 h-6", text: "text-base" }
  };

  const sizeConfig = sizes[size];

  return (
    <div className={cn(
      "inline-flex items-center space-x-2 rounded-full",
      config.bgColor,
      sizeConfig.container,
      className
    )}>
      <Icon className={cn(
        sizeConfig.icon,
        config.color,
        config.animate
      )} />
      {message && (
        <span className={cn(
          "font-medium",
          config.color,
          sizeConfig.text
        )}>
          {message}
        </span>
      )}
    </div>
  );
}

/**
 * Page Skeleton Component
 */
interface PageSkeletonProps {
  showHeader?: boolean;
  showStats?: boolean;
  showContent?: boolean;
  className?: string;
}

export function PageSkeleton({
  showHeader = true,
  showStats = true,
  showContent = true,
  className
}: PageSkeletonProps) {
  return (
    <div className={cn("space-y-6 animate-pulse", className)}>
      {showHeader && (
        <div className="space-y-3">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
        </div>
      )}

      {showStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
                  <div className="h-8 w-8 bg-slate-200 dark:bg-slate-700 rounded"></div>
                </div>
                <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {showContent && (
        <div className="space-y-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="p-6">
              <div className="space-y-4">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-4/6"></div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}