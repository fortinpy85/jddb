/**
 * Enhanced Navigation Components
 * Modern navigation patterns with improved accessibility and UX
 */

"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  ChevronRight,
  ChevronDown,
  Home,
  Star,
  Bell,
  User,
  Settings,
  HelpCircle,
  Menu,
  X
} from "lucide-react";

interface NavigationItem {
  id: string;
  label: string;
  shortLabel?: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  badge?: {
    label: string;
    variant?: "default" | "secondary" | "destructive";
  };
  children?: NavigationItem[];
  href?: string;
  onClick?: () => void;
  isActive?: boolean;
  isDisabled?: boolean;
}

interface EnhancedNavigationProps {
  items: NavigationItem[];
  orientation?: "horizontal" | "vertical";
  variant?: "default" | "pills" | "minimal" | "sidebar";
  size?: "sm" | "md" | "lg";
  activeId?: string;
  onItemClick?: (item: NavigationItem) => void;
  className?: string;
  allowCollapse?: boolean;
}

export function EnhancedNavigation({
  items,
  orientation = "horizontal",
  variant = "default",
  size = "md",
  activeId,
  onItemClick,
  className,
  allowCollapse = false
}: EnhancedNavigationProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const handleItemClick = (item: NavigationItem) => {
    if (item.isDisabled) return;

    if (item.children && item.children.length > 0) {
      toggleExpanded(item.id);
    } else {
      onItemClick?.(item);
    }
  };

  const renderNavItem = (item: NavigationItem, level: number = 0) => {
    const isActive = activeId === item.id || item.isActive;
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;
    const Icon = item.icon;

    const baseClasses = cn(
      "group relative flex items-center justify-between transition-all duration-200",
      "hover:bg-slate-100 dark:hover:bg-slate-800",
      "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
      "dark:focus:ring-blue-400 dark:focus:ring-offset-slate-800",
      {
        "w-full text-left": orientation === "vertical" || variant === "sidebar",
        "cursor-pointer": !item.isDisabled,
        "opacity-50 cursor-not-allowed": item.isDisabled,
      }
    );

    const variantClasses = {
      default: cn(
        "border border-transparent hover:border-slate-200 dark:hover:border-slate-700",
        isActive && "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-400 text-blue-700 dark:text-blue-400"
      ),
      pills: cn(
        "rounded-full px-4 py-2",
        isActive && "bg-blue-600 text-white shadow-lg"
      ),
      minimal: cn(
        "border-b-2 border-transparent hover:border-slate-300 dark:hover:border-slate-600",
        isActive && "border-blue-500"
      ),
      sidebar: cn(
        "rounded-lg px-3 py-2 mx-2",
        isActive && "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
      )
    };

    const sizeClasses = {
      sm: "text-sm gap-2 min-h-[2rem]",
      md: "text-sm gap-3 min-h-[2.5rem]",
      lg: "text-base gap-3 min-h-[3rem]"
    };

    const indentClass = level > 0 ? `ml-${level * 4}` : "";

    return (
      <div key={item.id} className={indentClass}>
        <button
          className={cn(
            baseClasses,
            variantClasses[variant],
            sizeClasses[size],
            "w-full px-3 py-2"
          )}
          onClick={() => handleItemClick(item)}
          disabled={item.isDisabled}
          title={item.description}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {/* Icon */}
            <Icon className={cn(
              "flex-shrink-0",
              size === "sm" ? "w-4 h-4" : size === "lg" ? "w-6 h-6" : "w-5 h-5",
              isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-600 dark:text-slate-400"
            )} />

            {/* Label */}
            {(!isCollapsed || variant !== "sidebar") && (
              <span className={cn(
                "font-medium truncate",
                isActive ? "text-blue-700 dark:text-blue-400" : "text-slate-700 dark:text-slate-300"
              )}>
                {orientation === "horizontal" && item.shortLabel ? item.shortLabel : item.label}
              </span>
            )}

            {/* Badge */}
            {item.badge && (!isCollapsed || variant !== "sidebar") && (
              <Badge
                variant={item.badge.variant || "secondary"}
                className="ml-auto flex-shrink-0"
              >
                {item.badge.label}
              </Badge>
            )}
          </div>

          {/* Expand/Collapse Indicator */}
          {hasChildren && (!isCollapsed || variant !== "sidebar") && (
            <ChevronRight className={cn(
              "w-4 h-4 flex-shrink-0 transition-transform duration-200",
              isExpanded && "rotate-90",
              isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400"
            )} />
          )}
        </button>

        {/* Children */}
        {hasChildren && isExpanded && (!isCollapsed || variant !== "sidebar") && (
          <div className="space-y-1 mt-1">
            {item.children!.map((child) => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <nav className={cn(
      "relative",
      orientation === "horizontal" ? "flex items-center" : "space-y-1",
      variant === "sidebar" && "w-64 transition-all duration-300",
      variant === "sidebar" && isCollapsed && "w-16",
      className
    )}>
      {/* Collapse Toggle (Sidebar only) */}
      {allowCollapse && variant === "sidebar" && (
        <div className="flex items-center justify-between p-2 mb-4">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Navigation
            </h2>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2"
          >
            {isCollapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </Button>
        </div>
      )}

      {/* Navigation Items */}
      <div className={cn(
        orientation === "horizontal" ? "flex items-center space-x-1" : "space-y-1"
      )}>
        {items.map((item) => renderNavItem(item))}
      </div>
    </nav>
  );
}

/**
 * Breadcrumb Navigation
 * Enhanced breadcrumb with JDDB styling
 */
interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
  icon?: React.ComponentType<{ className?: string }>;
}

interface EnhancedBreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
}

export function EnhancedBreadcrumb({
  items,
  separator = <ChevronRight className="w-4 h-4 text-slate-400" />,
  className
}: EnhancedBreadcrumbProps) {
  return (
    <nav className={cn("flex items-center space-x-2 text-sm", className)} aria-label="Breadcrumb">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const Icon = item.icon;

        return (
          <React.Fragment key={index}>
            {index > 0 && separator}
            <div className="flex items-center space-x-1">
              {Icon && (
                <Icon className="w-4 h-4 text-slate-500" />
              )}
              {isLast ? (
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  {item.label}
                </span>
              ) : (
                <button
                  onClick={item.onClick}
                  className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors duration-200"
                >
                  {item.label}
                </button>
              )}
            </div>
          </React.Fragment>
        );
      })}
    </nav>
  );
}

/**
 * Quick Action Bar
 * Floating action bar for common operations
 */
interface QuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  onClick: () => void;
  color?: "blue" | "emerald" | "amber" | "red";
  disabled?: boolean;
}

interface QuickActionBarProps {
  actions: QuickAction[];
  position?: "bottom-right" | "bottom-left" | "bottom-center";
  className?: string;
}

export function QuickActionBar({
  actions,
  position = "bottom-right",
  className
}: QuickActionBarProps) {
  const positionClasses = {
    "bottom-right": "bottom-6 right-6",
    "bottom-left": "bottom-6 left-6",
    "bottom-center": "bottom-6 left-1/2 transform -translate-x-1/2"
  };

  const colors = {
    blue: "bg-blue-600 hover:bg-blue-700 text-white",
    emerald: "bg-emerald-600 hover:bg-emerald-700 text-white",
    amber: "bg-amber-600 hover:bg-amber-700 text-white",
    red: "bg-red-600 hover:bg-red-700 text-white"
  };

  return (
    <div className={cn(
      "fixed z-50",
      positionClasses[position],
      className
    )}>
      <div className="flex items-center space-x-3 bg-white dark:bg-slate-800 rounded-full shadow-lg border border-slate-200 dark:border-slate-700 p-2">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <Button
              key={action.id}
              onClick={action.onClick}
              disabled={action.disabled}
              className={cn(
                "rounded-full w-12 h-12 p-0 shadow-lg hover:scale-110 transition-all duration-200",
                colors[action.color || "blue"]
              )}
              title={action.label}
            >
              <Icon className="w-5 h-5" />
            </Button>
          );
        })}
      </div>
    </div>
  );
}