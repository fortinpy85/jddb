/**
 * Enhanced Card Components
 * Modern card designs with improved visual hierarchy and interactions
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ChevronRight, ExternalLink, MoreVertical } from "lucide-react";

interface EnhancedCardProps {
  title?: string;
  subtitle?: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  image?: string;
  children?: React.ReactNode;
  className?: string;
  variant?: "default" | "elevated" | "outlined" | "gradient";
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  actions?: React.ReactNode;
  badges?: Array<{
    label: string;
    variant?: "default" | "secondary" | "destructive" | "outline";
  }>;
  onClick?: () => void;
  href?: string;
}

export function EnhancedCard({
  title,
  subtitle,
  description,
  icon: Icon,
  image,
  children,
  className,
  variant = "default",
  size = "md",
  interactive = false,
  actions,
  badges,
  onClick,
  href,
}: EnhancedCardProps) {
  const variants = {
    default:
      "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-card",
    elevated: "bg-white dark:bg-slate-800 border-0 elevation-2 shadow-hover",
    outlined: "bg-transparent border-2 border-slate-200 dark:border-slate-700 shadow-outline",
    gradient:
      "bg-gradient-to-br from-white via-blue-50/30 to-indigo-50/20 dark:from-slate-800 dark:via-slate-700/30 dark:to-slate-800/20 border border-white/20 dark:border-slate-700/20 shadow-card",
  };

  const sizes = {
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  };

  const CardWrapper = href ? "a" : "div";
  const cardProps = href
    ? { href, target: "_blank", rel: "noopener noreferrer" }
    : {};

  return (
    <CardWrapper
      {...cardProps}
      className={cn(
        "group relative overflow-hidden rounded-xl transition-all duration-300",
        variants[variant],
        interactive && "hover:scale-[1.02] cursor-pointer shadow-transition",
        interactive && "hover:border-blue-200 dark:hover:border-blue-400",
        className,
      )}
      onClick={onClick}
    >
      {/* Background Effects */}
      {variant === "gradient" && (
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500/10 to-indigo-500/5 rounded-full -mr-16 -mt-16 group-hover:scale-110 transition-transform duration-500"></div>
      )}

      {/* Image Header */}
      {image && (
        <div className="relative h-48 bg-gradient-to-br from-blue-500 to-indigo-600 overflow-hidden">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
        </div>
      )}

      <div className={cn(sizes[size], "relative z-10")}>
        {/* Header Section */}
        {(title || subtitle || Icon || actions) && (
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start space-x-3 flex-1 min-w-0">
              {Icon && (
                <div className="flex-shrink-0 p-2 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg elevation-2 shadow-glow-blue transition-shadow duration-300">
                  <Icon className="w-5 h-5 text-white" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                {title && (
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-200 truncate">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 truncate">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
            {actions && (
              <div className="flex items-center space-x-2 flex-shrink-0">
                {actions}
              </div>
            )}
          </div>
        )}

        {/* Badges */}
        {badges && badges.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {badges.map((badge, index) => (
              <Badge key={index} variant={badge.variant || "secondary"}>
                {badge.label}
              </Badge>
            ))}
          </div>
        )}

        {/* Description */}
        {description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-3">
            {description}
          </p>
        )}

        {/* Content */}
        {children && <div className="space-y-4">{children}</div>}

        {/* Interactive Indicator */}
        {(interactive || href) && (
          <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            {href ? (
              <ExternalLink className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </div>
        )}
      </div>
    </CardWrapper>
  );
}

/**
 * Feature Card Component
 * Specialized card for highlighting features or capabilities
 */
interface FeatureCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  features?: string[];
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function FeatureCard({
  title,
  description,
  icon: Icon,
  features,
  action,
  className,
}: FeatureCardProps) {
  return (
    <EnhancedCard
      variant="gradient"
      size="lg"
      interactive={!!action}
      className={className}
      onClick={action?.onClick}
    >
      <div className="text-center space-y-6">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="p-4 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl elevation-3 shadow-glow-blue transition-shadow duration-300">
            <Icon className="w-8 h-8 text-white" />
          </div>
        </div>

        {/* Content */}
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3">
            {title}
          </h3>
          <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Features List */}
        {features && features.length > 0 && (
          <div className="space-y-2">
            {features.map((feature, index) => (
              <div
                key={index}
                className="flex items-center justify-center text-sm text-slate-600 dark:text-slate-400"
              >
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-2"></div>
                {feature}
              </div>
            ))}
          </div>
        )}

        {/* Action Button */}
        {action && (
          <Button
            variant="outline"
            className="border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300 shadow-button transition-colors duration-200"
          >
            {action.label}
          </Button>
        )}
      </div>
    </EnhancedCard>
  );
}

/**
 * Metric Card Component
 * For displaying statistics and metrics with visual emphasis
 */
interface MetricCardProps {
  title: string;
  value: string | number | React.ReactNode;
  change?: {
    value: number;
    period: string;
  };
  icon: React.ComponentType<{ className?: string }>;
  color?: "blue" | "emerald" | "amber" | "red" | "violet";
  className?: string;
}

export function MetricCard({
  title,
  value,
  change,
  icon: Icon,
  color = "blue",
  className,
}: MetricCardProps) {
  const colors = {
    blue: {
      text: "text-blue-600",
      bg: "bg-blue-50",
      border: "border-blue-200",
    },
    emerald: {
      text: "text-emerald-600",
      bg: "bg-emerald-50",
      border: "border-emerald-200",
    },
    amber: {
      text: "text-amber-600",
      bg: "bg-amber-50",
      border: "border-amber-200",
    },
    red: {
      text: "text-red-600",
      bg: "bg-red-50",
      border: "border-red-200",
    },
    violet: {
      text: "text-violet-600",
      bg: "bg-violet-50",
      border: "border-violet-200",
    },
  };

  const colorConfig = colors[color];

  return (
    <EnhancedCard
      variant="elevated"
      size="md"
      className={cn("group hover:scale-105", className)}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
            {title}
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {value}
          </p>
          {change && (
            <p
              className={cn(
                "text-xs font-medium mt-2",
                change.value >= 0 ? "text-emerald-600" : "text-red-600",
              )}
            >
              {change.value >= 0 ? "+" : ""}
              {change.value}% from {change.period}
            </p>
          )}
        </div>
        <div
          className={cn(
            "p-3 rounded-xl group-hover:scale-110 transition-transform duration-300",
            colorConfig.bg,
            "border",
            colorConfig.border,
          )}
        >
          <Icon className={cn("w-6 h-6", colorConfig.text)} />
        </div>
      </div>
    </EnhancedCard>
  );
}
