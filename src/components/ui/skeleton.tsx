"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
}

function Skeleton({
  className = "",
  width,
  height,
  rounded = false,
  ...props
}: SkeletonProps & React.HTMLAttributes<HTMLDivElement>) {
  const style = width || height ? { width, height } : undefined;

  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gray-200",
        rounded && "rounded-full",
        className
      )}
      style={style}
      {...props}
    />
  );
}

interface SkeletonTextProps {
  lines?: number;
  className?: string;
}

function SkeletonText({ lines = 3, className = "" }: SkeletonTextProps) {
  return (
    <div className={className}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={cn(
            "h-4 mb-2",
            index === lines - 1 ? "w-3/4" : "w-full",
            index === 0 ? "w-5/6" : "",
          )}
        />
      ))}
    </div>
  );
}

interface SkeletonCardProps {
  className?: string;
  showActions?: boolean;
}

function SkeletonCard({
  className = "",
  showActions = false,
}: SkeletonCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border bg-card text-card-foreground shadow-sm p-6",
        className,
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Skeleton className="h-6 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        {showActions && (
          <div className="flex gap-2">
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-8 w-16" />
          </div>
        )}
      </div>
      <SkeletonText lines={3} />
      <div className="flex gap-2 mt-4">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
      </div>
    </div>
  );
}

interface SkeletonStatsProps {
  className?: string;
}

function SkeletonStats({ className = "" }: SkeletonStatsProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4",
        className,
      )}
    >
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-lg border bg-white shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-8 w-12" />
            </div>
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface SkeletonJobCardProps {
  className?: string;
}

function SkeletonJobCard({ className = "" }: SkeletonJobCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border bg-white shadow-sm p-4 space-y-3",
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-3 w-1/3" />
        </div>
        <Skeleton className="h-8 w-20 rounded-full" />
      </div>
      <div className="flex space-x-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-14 rounded-full" />
      </div>
    </div>
  );
}

interface SkeletonListProps {
  count?: number;
  className?: string;
}

function SkeletonList({ count = 6, className = "" }: SkeletonListProps) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonJobCard key={i} />
      ))}
    </div>
  );
}

interface SkeletonTableProps {
  rows?: number;
  className?: string;
}

function SkeletonTable({ rows = 5, className = "" }: SkeletonTableProps) {
  return (
    <div className={cn("rounded-lg border bg-white", className)}>
      <div className="p-4 border-b">
        <div className="flex justify-between items-center">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-8 w-24" />
        </div>
      </div>
      <div className="divide-y">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-4 flex items-center space-x-4">
            <Skeleton className="h-10 w-10 rounded" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-8 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Enhanced SkeletonLoader with type-based rendering from skeleton-loader.tsx
interface SkeletonLoaderProps {
  type:
    | "job-list"
    | "job-card"
    | "job-details"
    | "stats-dashboard"
    | "search-results"
    | "upload-area"
    | "comparison"
    | "table-rows";
  count?: number;
  showHeader?: boolean;
  className?: string;
}

function SkeletonLoader({
  type,
  count = 1,
  showHeader = true,
  className = "",
}: SkeletonLoaderProps) {
  const renderJobCardSkeleton = () => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex justify-between items-start">
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-3">
              <Skeleton width="200px" height="1.5rem" />
              <Skeleton width="60px" height="1.25rem" rounded />
              <Skeleton width="80px" height="1.25rem" rounded />
              <Skeleton width="70px" height="1.25rem" rounded />
            </div>
            <Skeleton width="300px" height="1rem" />
            <Skeleton width="150px" height="0.75rem" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton width="70px" height="2rem" />
            <Skeleton width="80px" height="2rem" />
            <Skeleton width="40px" height="2rem" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderJobListSkeleton = () => (
    <div className="space-y-6">
      {/* Header Card Skeleton */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton width="200px" height="1.5rem" />
            <Skeleton width="80px" height="2rem" />
          </div>
        </CardHeader>
        <CardContent>
          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="text-center space-y-2">
                <Skeleton width="40px" height="2rem" className="mx-auto" />
                <Skeleton width="60px" height="0.875rem" className="mx-auto" />
              </div>
            ))}
          </div>

          {/* Search and Filters */}
          <div className="space-y-4">
            <div className="flex gap-2">
              <Skeleton height="2.5rem" />
              <Skeleton width="80px" height="2.5rem" />
            </div>
            <div className="flex flex-wrap gap-4">
              <Skeleton width="150px" height="2rem" />
              <Skeleton width="120px" height="2rem" />
              <Skeleton width="200px" height="2rem" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Job Cards */}
      <div className="space-y-4">
        {[...Array(count)].map((_, i) => (
          <div key={i}>{renderJobCardSkeleton()}</div>
        ))}
      </div>
    </div>
  );

  const renderJobDetailsSkeleton = () => (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton width="300px" height="2rem" />
              <div className="flex gap-2">
                <Skeleton width="80px" height="1.25rem" rounded />
                <Skeleton width="100px" height="1.25rem" rounded />
                <Skeleton width="70px" height="1.25rem" rounded />
              </div>
            </div>
            <Skeleton width="100px" height="2.5rem" />
          </div>
        </CardHeader>
      </Card>

      {/* Content Sections */}
      {[...Array(4)].map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton width="200px" height="1.5rem" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton height="1rem" />
            <Skeleton height="1rem" />
            <Skeleton width="80%" height="1rem" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderStatsDashboardSkeleton = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton width="80px" height="0.875rem" />
                  <Skeleton width="60px" height="2rem" />
                </div>
                <Skeleton width="48px" height="48px" rounded />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts and Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(2)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton width="150px" height="1.5rem" />
            </CardHeader>
            <CardContent className="space-y-3">
              {[...Array(5)].map((_, j) => (
                <div key={j} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Skeleton width="12px" height="12px" rounded />
                    <Skeleton width="100px" height="1rem" />
                  </div>
                  <Skeleton width="30px" height="1rem" />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderSearchResultsSkeleton = () => (
    <div className="space-y-4">
      {/* Search Header */}
      <div className="flex items-center justify-between">
        <Skeleton width="200px" height="1.5rem" />
        <Skeleton width="100px" height="1rem" />
      </div>

      {/* Results */}
      {[...Array(count)].map((_, i) => (
        <div key={i}>{renderJobCardSkeleton()}</div>
      ))}
    </div>
  );

  const renderUploadAreaSkeleton = () => (
    <Card className="border-dashed border-2">
      <CardContent className="pt-8 pb-8">
        <div className="text-center space-y-4">
          <Skeleton width="80px" height="80px" rounded className="mx-auto" />
          <Skeleton width="200px" height="1.5rem" className="mx-auto" />
          <Skeleton width="300px" height="1rem" className="mx-auto" />
          <div className="flex justify-center gap-2 pt-4">
            <Skeleton width="120px" height="2.5rem" />
            <Skeleton width="100px" height="2.5rem" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderComparisonSkeleton = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Skeleton width="250px" height="2rem" />
        <Skeleton width="100px" height="2.5rem" />
      </div>

      {/* Comparison Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(2)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <div className="space-y-2">
                <Skeleton width="200px" height="1.5rem" />
                <div className="flex gap-2">
                  <Skeleton width="60px" height="1.25rem" rounded />
                  <Skeleton width="80px" height="1.25rem" rounded />
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {[...Array(4)].map((_, j) => (
                <div key={j}>
                  <Skeleton width="120px" height="1rem" className="mb-2" />
                  <Skeleton height="1rem" />
                  <Skeleton width="90%" height="1rem" />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderTableRowsSkeleton = () => (
    <div className="space-y-2">
      {[...Array(count)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 py-3 border-b">
          <Skeleton width="150px" height="1rem" />
          <Skeleton width="100px" height="1rem" />
          <Skeleton width="80px" height="1rem" />
          <Skeleton width="120px" height="1rem" />
          <div className="flex gap-2 ml-auto">
            <Skeleton width="60px" height="1.5rem" />
            <Skeleton width="60px" height="1.5rem" />
          </div>
        </div>
      ))}
    </div>
  );

  const renderSkeleton = () => {
    switch (type) {
      case "job-list":
        return renderJobListSkeleton();
      case "job-card":
        return renderJobCardSkeleton();
      case "job-details":
        return renderJobDetailsSkeleton();
      case "stats-dashboard":
        return renderStatsDashboardSkeleton();
      case "search-results":
        return renderSearchResultsSkeleton();
      case "upload-area":
        return renderUploadAreaSkeleton();
      case "comparison":
        return renderComparisonSkeleton();
      case "table-rows":
        return renderTableRowsSkeleton();
      default:
        return <Skeleton />;
    }
  };

  return <div className={className}>{renderSkeleton()}</div>;
}

export {
  Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonStats,
  SkeletonJobCard,
  SkeletonList,
  SkeletonTable,
  SkeletonLoader,
};

export default SkeletonLoader;