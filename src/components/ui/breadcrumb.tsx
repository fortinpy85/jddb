"use client";

import React from "react";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";
import { logger } from "@/utils/logger";

export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
  current?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
  showHome?: boolean;
  separator?: "chevron" | "slash";
}

export function Breadcrumb({
  items,
  className = "",
  showHome = true,
  separator = "chevron",
}: BreadcrumbProps) {
  const SeparatorComponent =
    separator === "chevron" ? ChevronRight : () => <span>/</span>;

  const allItems = showHome
    ? [{ label: "Home", href: "#", onClick: () => {} }, ...items]
    : items;

  return (
    <nav
      className={cn(
        "flex items-center space-x-1 text-sm text-gray-600",
        className,
      )}
    >
      {allItems.map((item, index) => {
        const isLast = index === allItems.length - 1;
        const isHome = showHome && index === 0;

        return (
          <React.Fragment key={index}>
            {index > 0 && (
              <SeparatorComponent className="h-4 w-4 text-gray-400 mx-1" />
            )}

            <div className="flex items-center">
              {isHome && <Home className="h-4 w-4 mr-1 text-gray-500" />}

              {item.href || item.onClick ? (
                <button
                  onClick={() => {
                    if (item.onClick) {
                      item.onClick();
                    } else if (item.href) {
                      // Handle href navigation if needed
                      logger.debug("Navigate to:", { href: item.href });
                    }
                  }}
                  className={cn(
                    "hover:text-blue-600 transition-colors",
                    isLast || item.current
                      ? "text-gray-900 font-medium cursor-default"
                      : "text-gray-600 hover:underline",
                  )}
                  disabled={isLast || item.current}
                >
                  {item.label}
                </button>
              ) : (
                <span
                  className={cn(
                    isLast || item.current
                      ? "text-gray-900 font-medium"
                      : "text-gray-600",
                  )}
                >
                  {item.label}
                </span>
              )}
            </div>
          </React.Fragment>
        );
      })}
    </nav>
  );
}

// Specialized breadcrumb for job details
interface JobDetailBreadcrumbProps {
  jobId: string;
  jobTitle?: string;
  onNavigateHome: () => void;
  onNavigateToJobs: () => void;
  className?: string;
}

export function JobDetailBreadcrumb({
  jobId,
  jobTitle,
  onNavigateHome,
  onNavigateToJobs,
  className = "",
}: JobDetailBreadcrumbProps) {
  const items: BreadcrumbItem[] = [
    {
      label: "Jobs",
      onClick: onNavigateToJobs,
    },
    {
      label: jobTitle || `Job ${jobId}`,
      current: true,
    },
  ];

  return <Breadcrumb items={items} className={className} showHome={true} />;
}

// Specialized breadcrumb for search results
interface SearchBreadcrumbProps {
  query?: string;
  resultsCount?: number;
  onNavigateHome: () => void;
  onClearSearch: () => void;
  className?: string;
}

export function SearchBreadcrumb({
  query,
  resultsCount,
  onNavigateHome,
  onClearSearch,
  className = "",
}: SearchBreadcrumbProps) {
  const items: BreadcrumbItem[] = [
    {
      label: "Search",
      onClick: onClearSearch,
    },
  ];

  if (query) {
    items.push({
      label: `"${query}"`,
      current: true,
    });
  }

  if (resultsCount !== undefined) {
    items.push({
      label: `${resultsCount} results`,
      current: true,
    });
  }

  return <Breadcrumb items={items} className={className} showHome={true} />;
}
