/**
 * FilterBar Component
 * Reusable filter bar for consistent filtering UI across views
 * Addresses Usability Issue #8.1: Inconsistent Filter Layouts
 */

"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Filter, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface FilterConfig {
  id: string;
  label: string;
  placeholder?: string;
  value: string;
  options: FilterOption[];
  onChange: (value: string) => void;
  className?: string;
}

export interface FilterBarProps {
  searchValue?: string;
  searchPlaceholder?: string;
  onSearchChange?: (value: string) => void;
  filters?: FilterConfig[];
  onClearAll?: () => void;
  showClearAll?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export function FilterBar({
  searchValue = "",
  searchPlaceholder = "Search...",
  onSearchChange,
  filters = [],
  onClearAll,
  showClearAll = true,
  children,
  className,
}: FilterBarProps) {
  const hasActiveFilters =
    searchValue ||
    filters.some((f) => f.value && f.value !== "all" && f.value !== "");

  const handleClearAll = () => {
    onSearchChange?.("");
    filters.forEach((f) => f.onChange("all"));
    onClearAll?.();
  };

  return (
    <Card className={cn("elevation-1 shadow-card", className)}>
      <CardContent className="p-4">
        <div className="flex flex-col gap-3">
          {/* Search Input */}
          {onSearchChange && (
            <div className="w-full">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder={searchPlaceholder}
                  value={searchValue}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="pl-10 shadow-input"
                />
              </div>
            </div>
          )}

          {/* Filters Row */}
          {filters.length > 0 && (
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex flex-wrap gap-3 flex-1">
                {filters.map((filter) => (
                  <Select
                    key={filter.id}
                    value={filter.value}
                    onValueChange={filter.onChange}
                  >
                    <SelectTrigger
                      className={cn("w-full sm:w-48", filter.className)}
                      aria-label={filter.label}
                    >
                      <SelectValue
                        placeholder={filter.placeholder || filter.label}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {filter.options.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.count !== undefined
                            ? `${option.label} (${option.count})`
                            : option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ))}
              </div>

              {/* Clear All Button */}
              {showClearAll && hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearAll}
                  className="text-slate-600 hover:text-slate-900"
                >
                  <X className="w-4 h-4 mr-1" />
                  Clear All
                </Button>
              )}
            </div>
          )}

          {/* Custom Children (e.g., Bulk Actions) */}
          {children}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * FilterBarHeader Component
 * Header with title and clear button for filter sections
 */
interface FilterBarHeaderProps {
  title: string;
  onClearAll?: () => void;
  showClearAll?: boolean;
}

export function FilterBarHeader({
  title,
  onClearAll,
  showClearAll = true,
}: FilterBarHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center space-x-2">
        <Filter className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-700">{title}</span>
      </div>
      {showClearAll && onClearAll && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="text-slate-500 hover:text-slate-700"
        >
          <X className="w-4 h-4 mr-1" />
          Clear All
        </Button>
      )}
    </div>
  );
}

/**
 * Hook to manage filter state
 */
export function useFilters<T extends Record<string, string>>(
  initialFilters: T
) {
  const [filters, setFilters] = React.useState<T>(initialFilters);

  const updateFilter = React.useCallback((key: keyof T, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const clearFilters = React.useCallback(() => {
    setFilters(initialFilters);
  }, [initialFilters]);

  const hasActiveFilters = React.useMemo(() => {
    return Object.entries(filters).some(
      ([key, value]) =>
        value && value !== "all" && value !== initialFilters[key as keyof T]
    );
  }, [filters, initialFilters]);

  return {
    filters,
    updateFilter,
    clearFilters,
    hasActiveFilters,
    setFilters,
  };
}
