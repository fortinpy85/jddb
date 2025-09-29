/**
 * PageHeader Component
 * Standardized header for consistent JDDB branding across all pages
 */

"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database, ArrowLeft, MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  onBack?: () => void;
  actions?: React.ReactNode;
  breadcrumb?: Array<{ label: string; href?: string }>;
  className?: string;
  variant?: "default" | "compact" | "minimal";
}

export function PageHeader({
  title,
  subtitle,
  showBack,
  onBack,
  actions,
  breadcrumb,
  className,
  variant = "default"
}: PageHeaderProps) {
  const isCompact = variant === "compact";
  const isMinimal = variant === "minimal";

  return (
    <div
      className={cn(
        "bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-b border-slate-200/50 dark:border-slate-700/50",
        isMinimal ? "py-2" : isCompact ? "py-3" : "py-4",
        className
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        {breadcrumb && breadcrumb.length > 0 && (
          <div className="mb-2">
            <nav className="flex items-center space-x-2 text-sm text-slate-500">
              {breadcrumb.map((item, index) => (
                <React.Fragment key={index}>
                  {index > 0 && <span>/</span>}
                  <span
                    className={cn(
                      index === breadcrumb.length - 1
                        ? "text-slate-900 dark:text-slate-100 font-medium"
                        : "hover:text-slate-700 dark:hover:text-slate-300 cursor-pointer"
                    )}
                  >
                    {item.label}
                  </span>
                </React.Fragment>
              ))}
            </nav>
          </div>
        )}

        <div className="flex items-center justify-between">
          {/* Left side - Logo, Title, Back button */}
          <div className="flex items-center space-x-4 min-w-0 flex-1">
            {showBack && onBack && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="flex-shrink-0"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
            )}

            {/* JDDB Logo - Always consistent */}
            {!isMinimal && (
              <div className="flex items-center group flex-shrink-0">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg blur opacity-20 group-hover:opacity-30 transition-opacity duration-300"></div>
                  <Database className="relative w-6 h-6 sm:w-8 sm:h-8 text-blue-600 mr-2 sm:mr-3 group-hover:scale-110 transition-transform duration-300" />
                </div>
                <div>
                  <h1 className="text-sm sm:text-lg lg:text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 transition-all duration-300">
                    <span className="hidden sm:inline">
                      Job Description Database
                    </span>
                    <span className="sm:hidden">JDDB</span>
                  </h1>
                  {subtitle && (
                    <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 font-medium">
                      {subtitle}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Page-specific title (if different from JDDB) */}
            {title && !isMinimal && (
              <div className="min-w-0 flex-1">
                <h2 className="text-lg sm:text-xl font-semibold text-slate-900 dark:text-slate-100 truncate">
                  {title}
                </h2>
              </div>
            )}
          </div>

          {/* Right side - Actions */}
          {actions && (
            <div className="flex items-center space-x-2 flex-shrink-0">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * PageContainer Component
 * Standardized container with consistent padding and layout
 */
interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
}

export function PageContainer({
  children,
  className,
  maxWidth = "full"
}: PageContainerProps) {
  const maxWidthClass = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "2xl": "max-w-2xl",
    full: "max-w-7xl"
  }[maxWidth];

  return (
    <div className={cn(
      "mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6",
      maxWidthClass,
      className
    )}>
      {children}
    </div>
  );
}

/**
 * PageLayout Component
 * Complete page layout with header and container
 */
interface PageLayoutProps extends PageHeaderProps {
  children: React.ReactNode;
  containerClassName?: string;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
}

export function PageLayout({
  children,
  containerClassName,
  maxWidth = "full",
  ...headerProps
}: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-900 dark:via-slate-800/30 dark:to-slate-900/20">
      <PageHeader {...headerProps} />
      <PageContainer className={containerClassName} maxWidth={maxWidth}>
        {children}
      </PageContainer>
    </div>
  );
}