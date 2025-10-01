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
    <div className="space-y-8">
      {/* Stats Overview */}
      <StatsOverview stats={stats} />

      {/* Charts Row */}
      {stats && <ChartsSection stats={stats} />}

      {/* Recent Jobs */}
      <RecentJobsList
        jobs={recentJobs}
        onJobSelect={onJobSelect}
        onNavigateToJobs={handleNavigateToJobs}
        onNavigateToUpload={handleNavigateToUpload}
      />

      {/* Quick Actions */}
      <QuickActionsGrid
        onNavigateToUpload={handleNavigateToUpload}
        onNavigateToJobs={handleNavigateToJobs}
        onNavigateToSearch={handleNavigateToSearch}
        onNavigateToCompare={handleNavigateToCompare}
      />
    </div>
  );
}
