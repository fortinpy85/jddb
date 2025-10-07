"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { getClassificationLevel, getLanguageName } from "@/lib/utils";
import { useStore } from "@/lib/store";
import {
  RefreshCw,
  Search,
  AlertCircle,
  Filter,
  Eye,
  Download,
  Trash2,
  Upload,
  Calendar,
  Database,
} from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import SkeletonLoader from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
interface JobListProps {
  onJobSelect?: (job: JobDescription) => void;
  showFilters?: boolean;
  initialFilters?: {
    classification?: string;
    language?: string;
    department?: string;
  };
}

export function JobList({
  onJobSelect,
  showFilters = true,
  initialFilters = {},
}: JobListProps) {
  // Separate selectors for data and actions to prevent re-renders
  const { jobs, loading, error, pagination, stats, filters } = useStore(
    (state) => ({
      jobs: state.jobs,
      loading: state.loading,
      error: state.error,
      pagination: state.pagination,
      stats: state.stats,
      filters: state.filters,
    }),
  );

  const fetchJobs = useStore((state) => state.fetchJobs);
  const fetchStats = useStore((state) => state.fetchStats);
  const setFilters = useStore((state) => state.setFilters);
  const searchJobs = useStore((state) => state.searchJobs);

  const [searchQuery, setSearchQuery] = useState("");
  const { addToast } = useToast();

  // Manual initialization only - prevent any automatic loading
  const [initialized, setInitialized] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);

  const initializeData = async () => {
    if (initialized || isInitializing) {
      return;
    }

    try {
      setIsInitializing(true);
      setFilters(initialFilters);
      await fetchJobs(true);
      await fetchStats();
      setInitialized(true);
      setIsInitializing(false);
    } catch (error) {
      console.error("Failed to initialize data:", error);
      setIsInitializing(false);
    }
  };

  const handleSearch = () => {
    searchJobs(searchQuery);
  };

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = {
      ...filters,
      [key]: value || undefined,
    };
    setFilters(newFilters);
    fetchJobs(true); // Explicitly trigger fetch with new filters
  };

  const handleJobView = (job: JobDescription) => {
    onJobSelect?.(job);
  };

  const handleJobDelete = async (jobId: number, jobNumber: string) => {
    if (!confirm(`Are you sure you want to delete job ${jobNumber}?`)) {
      return;
    }

    try {
      await apiClient.deleteJob(jobId);
      fetchJobs(true); // Refetch jobs after deletion
      fetchStats(); // Refresh stats

      addToast({
        type: "success",
        title: "Job Deleted",
        description: `Job ${jobNumber} has been successfully deleted.`,
      });
    } catch (err) {
      addToast({
        type: "error",
        title: "Delete Failed",
        description: `Failed to delete job: ${err instanceof Error ? err.message : "Unknown error"}`,
      });
    }
  };

  const loadMoreJobs = () => {
    fetchJobs();
  };

  const handleJobExport = async (job: JobDescription) => {
    try {
      // Fetch full job details with content, sections, and metadata
      const fullJob = await apiClient.getJob(job.id, {
        include_content: true,
        include_sections: true,
        include_metadata: true,
      });

      // Create a formatted text export
      const exportData = `
Job Description Export
=====================

Title: ${fullJob.title}
Job Number: ${fullJob.job_number}
Classification: ${fullJob.classification}
Language: ${getLanguageName(fullJob.language)}
${fullJob.processed_date ? `Processed: ${new Date(fullJob.processed_date).toLocaleDateString()}` : ""}

${
  fullJob.raw_content
    ? `
Content:
--------
${fullJob.raw_content}
`
    : ""
}

${
  fullJob.sections && fullJob.sections.length > 0
    ? `
Sections:
---------
${fullJob.sections
  .map(
    (section) => `
${section.section_type}:
${section.section_content}
`,
  )
  .join("")}
`
    : ""
}

${
  fullJob.metadata && Object.keys(fullJob.metadata).length > 0
    ? `
Metadata:
---------
${Object.entries(fullJob.metadata)
  .map(([key, value]) => `${key}: ${value}`)
  .join("\n")}
`
    : ""
}
      `.trim();

      // Create and download file
      const blob = new Blob([exportData], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = `${fullJob.job_number}_${fullJob.title.replace(/[^a-zA-Z0-9]/g, "_")}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      addToast({
        type: "success",
        title: "Export Complete",
        description: `Job ${job.job_number} has been exported successfully.`,
      });
    } catch (err) {
      addToast({
        type: "error",
        title: "Export Failed",
        description: `Failed to export job: ${err instanceof Error ? err.message : "Unknown error"}`,
      });
    }
  };

  console.log(
    "🎯 JobList render - initialized:",
    initialized,
    "isInitializing:",
    isInitializing,
    "loading:",
    loading,
    "jobs.length:",
    jobs.length,
  );

  // Show initialization UI if not initialized AND no jobs data available
  const hasJobData = jobs.length > 0;
  const shouldShowInitUI = !initialized && !hasJobData;

  if (shouldShowInitUI) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="pt-6 text-center">
            <h3 className="text-lg font-semibold mb-4">Job Descriptions</h3>
            <p className="text-gray-600 mb-4">
              Click the button below to load job data
            </p>
            <Button
              onClick={initializeData}
              disabled={loading || isInitializing}
            >
              <Database className="w-4 h-4 mr-2" />
              {isInitializing
                ? "Initializing..."
                : loading
                  ? "Loading..."
                  : "Load Job Data"}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Job Descriptions ({stats.total_jobs})</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                fetchJobs(true);
                fetchStats();
              }}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Processing Status Overview */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {stats.processing_status.completed}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stats.processing_status.processing}
              </div>
              <div className="text-sm text-gray-600">Processing</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {stats.processing_status.pending}
              </div>
              <div className="text-sm text-gray-600">Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {stats.processing_status.needs_review}
              </div>
              <div className="text-sm text-gray-600">Needs Review</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {stats.processing_status.failed}
              </div>
              <div className="text-sm text-gray-600">Failed</div>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search job descriptions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-10"
                />
              </div>
              <Button onClick={handleSearch}>Search</Button>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <select
                    aria-label="Classification filter"
                    value={filters.classification || ""}
                    onChange={(e) =>
                      handleFilterChange("classification", e.target.value)
                    }
                    className="border rounded px-3 py-1 text-sm"
                  >
                    <option value="">All Classifications</option>
                    {Object.entries(stats.by_classification).map(
                      ([classification, count]) => (
                        <option key={classification} value={classification}>
                          {classification} ({count})
                        </option>
                      ),
                    )}
                  </select>
                </div>

                <select
                  aria-label="Language filter"
                  value={filters.language || ""}
                  onChange={(e) =>
                    handleFilterChange("language", e.target.value)
                  }
                  className="border rounded px-3 py-1 text-sm"
                >
                  <option value="">All Languages</option>
                  {Object.entries(stats.by_language).map(
                    ([language, count]) => (
                      <option key={language} value={language}>
                        {getLanguageName(language)} ({count})
                      </option>
                    ),
                  )}
                </select>

                <Input
                  placeholder="Department filter..."
                  value={filters.department || ""}
                  onChange={(e) =>
                    handleFilterChange("department", e.target.value)
                  }
                  className="w-48"
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center text-red-600">
              <AlertCircle className="w-5 h-5 mr-2" />
              {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job List - Enhanced Card Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {jobs.map((job) => (
          <Card
            key={job.id}
            className="group h-full flex flex-col transition-all duration-300 hover:shadow-xl hover:scale-[1.02] border border-gray-100 hover:border-gray-200 bg-white hover:bg-gradient-to-br hover:from-white hover:to-gray-50"
          >
            <CardContent className="p-6 flex-1 flex flex-col">
              {/* Header with badges */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex flex-wrap gap-2">
                  <Badge
                    variant="secondary"
                    className="bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition-colors"
                  >
                    {job.job_number}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 transition-colors"
                  >
                    {job.classification}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="border-blue-200 text-blue-700 hover:bg-blue-50 transition-colors"
                  >
                    {getLanguageName(job.language)}
                  </Badge>
                  {"relevance_score" in job && (
                    <Badge className="bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 border-0">
                      {Math.round((job as any).relevance_score * 100)}% match
                    </Badge>
                  )}
                </div>
              </div>

              {/* Title and description */}
              <div className="flex-1 mb-4">
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors duration-200 mb-2 line-clamp-2">
                  {job.title}
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  {getClassificationLevel(job.classification)}
                </p>
                {job.processed_date && (
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Processed:{" "}
                    {new Date(job.processed_date).toLocaleDateString()}
                  </p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2 pt-4 border-t border-gray-100">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobView(job)}
                  className="flex-1 transition-all duration-200 hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 group/btn"
                >
                  <Eye className="w-4 h-4 mr-1 group-hover/btn:scale-110 transition-transform duration-200" />
                  View
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobExport(job)}
                  className="flex-1 transition-all duration-200 hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700 group/btn"
                >
                  <Download className="w-4 h-4 mr-1 group-hover/btn:scale-110 transition-transform duration-200" />
                  Export
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobDelete(job.id, job.job_number)}
                  className="transition-all duration-200 hover:bg-red-50 hover:border-red-300 hover:text-red-700 group/btn px-3"
                >
                  <Trash2 className="w-4 h-4 group-hover/btn:scale-110 transition-transform duration-200" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Load More Button */}
      {pagination.has_more && (
        <div className="text-center">
          <Button variant="outline" onClick={loadMoreJobs} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              "Load More"
            )}
          </Button>
        </div>
      )}

      {/* Loading State */}
      {loading && jobs.length === 0 && (
        <SkeletonLoader type="job-list" count={5} />
      )}

      {/* Empty State */}
      {!loading && jobs.length === 0 && !error && (
        <EmptyState
          type={searchQuery ? "no-search-results" : "no-jobs"}
          searchQuery={searchQuery}
          actions={
            searchQuery
              ? [
                  {
                    label: "Clear Search",
                    onClick: () => {
                      setSearchQuery("");
                      fetchJobs(true);
                    },
                    variant: "outline",
                  },
                  {
                    label: "Browse All Jobs",
                    onClick: () => {
                      setSearchQuery("");
                      setFilters({});
                      fetchJobs(true);
                    },
                    variant: "outline",
                  },
                ]
              : [
                  {
                    label: "Upload Files",
                    onClick: () => (window.location.hash = "#upload"),
                    icon: Upload,
                  },
                ]
          }
        />
      )}
    </div>
  );
}

// Wrap with error boundary for reliability
const JobListWithErrorBoundary = (props: JobListProps) => (
  <ErrorBoundaryWrapper>
    <JobList {...props} />
  </ErrorBoundaryWrapper>
);

export default React.memo(JobListWithErrorBoundary);
