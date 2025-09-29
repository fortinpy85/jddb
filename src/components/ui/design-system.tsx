/**
 * JDDB Design System
 * Standardized components and patterns for consistent UI
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/**
 * Standardized content sections with consistent styling
 */
interface ContentSectionProps {
  title?: string;
  subtitle?: string;
  icon?: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  className?: string;
  headerActions?: React.ReactNode;
  variant?: "default" | "highlighted" | "compact";
}

export function ContentSection({
  title,
  subtitle,
  icon: Icon,
  children,
  className,
  headerActions,
  variant = "default"
}: ContentSectionProps) {
  const isCompact = variant === "compact";
  const isHighlighted = variant === "highlighted";

  return (
    <Card
      className={cn(
        "bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-white/20 dark:border-slate-700/20 hover:bg-white/90 dark:hover:bg-slate-800/90 transition-all duration-300",
        isHighlighted && "hover:shadow-xl border-blue-200/50 dark:border-blue-400/50",
        className
      )}
    >
      {(title || subtitle || headerActions) && (
        <CardHeader className={cn("relative overflow-hidden", isCompact && "pb-3")}>
          {isHighlighted && (
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-50/30 to-indigo-50/20 rounded-full -mr-12 -mt-12"></div>
          )}
          <div className="flex items-center justify-between relative z-10">
            <div className="flex items-center space-x-3">
              {Icon && (
                <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-2 rounded-lg shadow-lg">
                  <Icon className="w-5 h-5 text-white" />
                </div>
              )}
              <div>
                {title && (
                  <CardTitle className="text-slate-800 dark:text-slate-200 font-bold tracking-wide">
                    {title}
                  </CardTitle>
                )}
                {subtitle && (
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
            {headerActions && (
              <div className="flex items-center space-x-2">
                {headerActions}
              </div>
            )}
          </div>
        </CardHeader>
      )}
      <CardContent className={cn(isCompact && "pt-3")}>
        {children}
      </CardContent>
    </Card>
  );
}

/**
 * Standardized stats card with consistent styling
 */
interface StatsCardProps {
  title: string;
  value: string | number | React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
  color?: "blue" | "emerald" | "amber" | "violet" | "red";
  trend?: string;
  tooltip?: string;
  onClick?: () => void;
  className?: string;
}

export function StatsCard({
  title,
  value,
  icon: Icon,
  color = "blue",
  trend,
  tooltip,
  onClick,
  className
}: StatsCardProps) {
  const colorConfig = {
    blue: {
      text: "text-blue-600",
      bg: "bg-gradient-to-br from-blue-50 to-indigo-50",
      hover: "hover:border-blue-200/50 dark:hover:border-blue-400/50"
    },
    emerald: {
      text: "text-emerald-600",
      bg: "bg-gradient-to-br from-emerald-50 to-green-50",
      hover: "hover:border-emerald-200/50 dark:hover:border-emerald-400/50"
    },
    amber: {
      text: "text-amber-600",
      bg: "bg-gradient-to-br from-amber-50 to-orange-50",
      hover: "hover:border-amber-200/50 dark:hover:border-amber-400/50"
    },
    violet: {
      text: "text-violet-600",
      bg: "bg-gradient-to-br from-violet-50 to-purple-50",
      hover: "hover:border-violet-200/50 dark:hover:border-violet-400/50"
    },
    red: {
      text: "text-red-600",
      bg: "bg-gradient-to-br from-red-50 to-pink-50",
      hover: "hover:border-red-200/50 dark:hover:border-red-400/50"
    }
  }[color];

  return (
    <Card
      className={cn(
        "group hover-lift cursor-pointer border border-white/20 dark:border-slate-700/20 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm hover:bg-white/90 dark:hover:bg-slate-800/90 transition-all duration-300",
        colorConfig.hover,
        onClick && "hover:scale-105",
        className
      )}
      title={tooltip}
      onClick={onClick}
    >
      <CardContent className="pt-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-50/40 to-indigo-50/20 rounded-full -mr-16 -mt-16 group-hover:scale-110 transition-transform duration-500"></div>
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-600 group-hover:text-blue-700 transition-colors duration-300 tracking-wide">
              {title}
            </p>
            <div className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-blue-900 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 transition-all duration-300">
              {value}
            </div>
            {trend && (
              <p className="text-xs text-green-600 flex items-center mt-1">
                {trend}
              </p>
            )}
          </div>
          <div className={cn("p-4 rounded-xl group-hover:scale-110 transition-all duration-300 shadow-lg group-hover:shadow-xl relative", colorConfig.bg)}>
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-xl"></div>
            <Icon className={cn("relative w-6 h-6 group-hover:rotate-12 transition-transform duration-500", colorConfig.text)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Standardized action button with consistent styling
 */
interface ActionButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  color?: "blue" | "emerald" | "amber" | "red" | "violet";
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
  disabled?: boolean;
}

export function ActionButton({
  children,
  onClick,
  variant = "outline",
  size = "md",
  color = "blue",
  icon: Icon,
  className,
  disabled
}: ActionButtonProps) {
  const colorConfig = {
    blue: {
      primary: "bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white",
      secondary: "bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200",
      outline: "border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300",
      ghost: "text-blue-700 hover:bg-blue-50"
    },
    emerald: {
      primary: "bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white",
      secondary: "bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200",
      outline: "border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:border-emerald-300",
      ghost: "text-emerald-700 hover:bg-emerald-50"
    },
    amber: {
      primary: "bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white",
      secondary: "bg-amber-50 hover:bg-amber-100 text-amber-700 border-amber-200",
      outline: "border-amber-200 text-amber-700 hover:bg-amber-50 hover:border-amber-300",
      ghost: "text-amber-700 hover:bg-amber-50"
    },
    red: {
      primary: "bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white",
      secondary: "bg-red-50 hover:bg-red-100 text-red-700 border-red-200",
      outline: "border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300",
      ghost: "text-red-700 hover:bg-red-50"
    },
    violet: {
      primary: "bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white",
      secondary: "bg-violet-50 hover:bg-violet-100 text-violet-700 border-violet-200",
      outline: "border-violet-200 text-violet-700 hover:bg-violet-50 hover:border-violet-300",
      ghost: "text-violet-700 hover:bg-violet-50"
    }
  }[color][variant];

  const sizeClass = {
    sm: "h-8 px-3 text-sm",
    md: "h-10 px-4",
    lg: "h-12 px-6 text-lg"
  }[size];

  return (
    <Button
      variant={variant as any}
      size={size as any}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "transition-all duration-200 hover:scale-105 hover:shadow-md group",
        colorConfig,
        sizeClass,
        className
      )}
    >
      {Icon && (
        <Icon className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform duration-200" />
      )}
      {children}
    </Button>
  );
}

/**
 * Standardized job card for consistent display
 */
interface JobCardProps {
  job: {
    id: number;
    job_number: string;
    title: string;
    classification: string;
    language: string;
    processed_date?: string;
    relevance_score?: number;
  };
  onView?: (job: any) => void;
  onExport?: (job: any) => void;
  onDelete?: (job: any) => void;
  showActions?: boolean;
  className?: string;
}

export function JobCard({
  job,
  onView,
  onExport,
  onDelete,
  showActions = true,
  className
}: JobCardProps) {
  const getLanguageName = (lang: string) => {
    return lang === "en" ? "English" : lang === "fr" ? "French" : lang;
  };

  const getClassificationLevel = (classification: string) => {
    const match = classification.match(/(\w+)-(\d+)/);
    if (match) {
      const [, group, level] = match;
      return `Level ${level} (${group})`;
    }
    return classification;
  };

  return (
    <Card
      className={cn(
        "group h-full flex flex-col transition-all duration-300 hover:shadow-xl hover:scale-[1.02] border border-white/20 dark:border-slate-700/20 hover:border-blue-200/50 dark:hover:border-blue-400/50 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm hover:bg-white/90 dark:hover:bg-slate-800/90",
        className
      )}
    >
      <CardContent className="p-6 flex-1 flex flex-col">
        {/* Header with badges */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition-colors">
              {job.job_number}
            </Badge>
            <Badge variant="outline" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 transition-colors">
              {job.classification}
            </Badge>
            <Badge variant="outline" className="border-blue-200 text-blue-700 hover:bg-blue-50 transition-colors">
              {getLanguageName(job.language)}
            </Badge>
            {job.relevance_score && (
              <Badge className="bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 border-0">
                {Math.round(job.relevance_score * 100)}% match
              </Badge>
            )}
          </div>
        </div>

        {/* Title and description */}
        <div className="flex-1 mb-4">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 group-hover:text-indigo-700 dark:group-hover:text-indigo-400 transition-colors duration-200 mb-2 line-clamp-2">
            {job.title}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
            {getClassificationLevel(job.classification)}
          </p>
          {job.processed_date && (
            <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
              Processed: {new Date(job.processed_date).toLocaleDateString()}
            </p>
          )}
        </div>

        {/* Action buttons */}
        {showActions && (
          <div className="flex items-center gap-2 pt-4 border-t border-slate-200/50 dark:border-slate-700/50">
            {onView && (
              <ActionButton
                variant="outline"
                size="sm"
                color="blue"
                onClick={() => onView(job)}
                className="flex-1"
              >
                View
              </ActionButton>
            )}
            {onExport && (
              <ActionButton
                variant="outline"
                size="sm"
                color="emerald"
                onClick={() => onExport(job)}
                className="flex-1"
              >
                Export
              </ActionButton>
            )}
            {onDelete && (
              <ActionButton
                variant="outline"
                size="sm"
                color="red"
                onClick={() => onDelete(job)}
                className="px-3"
              >
                Delete
              </ActionButton>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}