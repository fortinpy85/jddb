import React from "react";
import { StatsOverview } from "./StatsOverview";
import { ChartsSection } from "./ChartsSection";
import { RecentJobsList } from "./RecentJobsList";
import { QuickActionsGrid } from "./QuickActionsGrid";
import type { ProcessingStats, JobDescription } from "@/lib/types";

interface DashboardProps {
  stats: ProcessingStats | null;
  recentJobs: JobDescription[];
  onJobSelect: (job: JobDescription) => void;
  onNavigateToTab: (tab: string) => void;
}

export function Dashboard({
  stats,
  recentJobs,
  onJobSelect,
  onNavigateToTab,
}: DashboardProps) {
  // Navigation handlers
  const handleNavigateToJobs = () => onNavigateToTab("jobs");
  const handleNavigateToUpload = () => onNavigateToTab("upload");
  const handleNavigateToSearch = () => onNavigateToTab("search");
  const handleNavigateToCompare = () => onNavigateToTab("compare");

  return (
    <div className="space-y-6 md:space-y-8">
      {/* Stats Overview - Enhanced spacing for mobile */}
      <section aria-label="Statistics Overview">
        <StatsOverview stats={stats} />
      </section>

      {/* Charts Row - Conditional rendering with proper spacing */}
      {stats && (
        <section aria-label="Performance Charts">
          <ChartsSection stats={stats} />
        </section>
      )}

      {/* Recent Jobs - Improved spacing and semantics */}
      <section aria-label="Recent Jobs">
        <RecentJobsList
          jobs={recentJobs}
          onJobSelect={onJobSelect}
          onNavigateToJobs={handleNavigateToJobs}
          onNavigateToUpload={handleNavigateToUpload}
        />
      </section>

      {/* Quick Actions - Enhanced mobile layout */}
      <section aria-label="Quick Actions">
        <QuickActionsGrid
          onNavigateToUpload={handleNavigateToUpload}
          onNavigateToJobs={handleNavigateToJobs}
          onNavigateToSearch={handleNavigateToSearch}
          onNavigateToCompare={handleNavigateToCompare}
        />
      </section>
    </div>
  );
}
