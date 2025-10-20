"use client";

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { logger } from "@/utils/logger";
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
  Edit,
} from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import SkeletonLoader from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { EditJobModal } from "@/components/jobs/EditJobModal";

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
  const { t } = useTranslation(["jobs", "common"]);

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
  const [deleteTarget, setDeleteTarget] = useState<JobDescription | null>(null);
  const [editTarget, setEditTarget] = useState<JobDescription | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

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
      logger.error("Failed to initialize data:", error);
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

  const handleJobEdit = (job: JobDescription) => {
    setEditTarget(job);
    setIsEditModalOpen(true);
  };

  const handleJobUpdated = (jobId: number) => {
    fetchJobs(true); // Refetch jobs after update
    fetchStats(); // Refresh stats

    addToast({
      type: "success",
      title: t("jobs:messages.updateSuccess"),
      description: t("jobs:messages.updateSuccessDescription"),
    });
  };

  const handleJobDelete = async (job: JobDescription) => {
    setDeleteTarget(job);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await apiClient.deleteJob(deleteTarget.id);
      fetchJobs(true); // Refetch jobs after deletion
      fetchStats(); // Refresh stats

      addToast({
        type: "success",
        title: t("jobs:messages.deleteSuccess"),
        description: t("jobs:messages.deleteSuccessDescription", {
          jobNumber: deleteTarget.job_number,
        }),
      });
    } catch (err) {
      addToast({
        type: "error",
        title: t("jobs:messages.deleteFailed"),
        description: t("jobs:messages.deleteFailedDescription", {
          error:
            err instanceof Error ? err.message : t("common:errors.unknown"),
        }),
      });
    } finally {
      setDeleteTarget(null);
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
        title: t("jobs:messages.exportSuccess"),
        description: t("jobs:messages.exportSuccessDescription", {
          jobNumber: job.job_number,
        }),
      });
    } catch (err) {
      addToast({
        type: "error",
        title: t("jobs:messages.exportFailed"),
        description: t("jobs:messages.exportFailedDescription", {
          error:
            err instanceof Error ? err.message : t("common:errors.unknown"),
        }),
      });
    }
  };

  logger.debug("🎯 JobList render", {
    initialized,
    isInitializing,
    loading,
    jobsLength: jobs.length,
  });

  // Show initialization UI if not initialized AND no jobs data available
  const hasJobData = jobs.length > 0;
  const shouldShowInitUI = !initialized && !hasJobData;

  if (shouldShowInitUI) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="pt-6 text-center">
            <h3 className="text-lg font-semibold mb-4">
              {t("jobs:list.title")}
            </h3>
            <p className="text-gray-600 mb-4">{t("jobs:list.loadPrompt")}</p>
            <Button
              onClick={initializeData}
              disabled={loading || isInitializing}
            >
              <Database className="w-4 h-4 mr-2" />
              {isInitializing
                ? t("common:loading.initializing")
                : loading
                  ? t("common:loading.loading")
                  : t("jobs:actions.loadData")}
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
            <span>
              {t("jobs:list.title")} ({stats.total_jobs})
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                fetchJobs(true);
                fetchStats();
              }}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {t("jobs:actions.refresh")}
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
              <div className="text-sm text-gray-600">
                {t("jobs:status.completed")}
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stats.processing_status.partial}
              </div>
              <div className="text-sm text-gray-600">
                {t("jobs:status.processing")}
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {stats.processing_status.needs_embeddings}
              </div>
              <div className="text-sm text-gray-600">
                {t("jobs:status.pending")}
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {stats.processing_status.needs_sections}
              </div>
              <div className="text-sm text-gray-600">
                {t("jobs:status.needsReview")}
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {stats.processing_status.needs_metadata}
              </div>
              <div className="text-sm text-gray-600">
                {t("jobs:status.failed")}
              </div>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder={t("jobs:search.placeholder")}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-10"
                />
              </div>
              <Button onClick={handleSearch}>{t("jobs:actions.search")}</Button>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <select
                    aria-label={t("jobs:filters.classificationLabel")}
                    value={filters.classification || ""}
                    onChange={(e) =>
                      handleFilterChange("classification", e.target.value)
                    }
                    className="border rounded px-3 py-1 text-sm"
                  >
                    <option value="">
                      {t("jobs:filters.allClassifications")}
                    </option>
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
                  aria-label={t("jobs:filters.languageLabel")}
                  value={filters.language || ""}
                  onChange={(e) =>
                    handleFilterChange("language", e.target.value)
                  }
                  className="border rounded px-3 py-1 text-sm"
                >
                  <option value="">{t("jobs:filters.allLanguages")}</option>
                  {Object.entries(stats.by_language).map(
                    ([language, count]) => (
                      <option key={language} value={language}>
                        {getLanguageName(language)} ({count})
                      </option>
                    ),
                  )}
                </select>

                <Input
                  placeholder={t("jobs:filters.departmentPlaceholder")}
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
                    {t("jobs:details.processed")}:{" "}
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
                  {t("jobs:actions.view")}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobEdit(job)}
                  className="transition-all duration-200 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 group/btn px-3"
                  title={t("jobs:actions.edit")}
                >
                  <Edit className="w-4 h-4 group-hover/btn:scale-110 transition-transform duration-200" />
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobExport(job)}
                  className="flex-1 transition-all duration-200 hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700 group/btn"
                >
                  <Download className="w-4 h-4 mr-1 group-hover/btn:scale-110 transition-transform duration-200" />
                  {t("jobs:actions.export")}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobDelete(job)}
                  className="transition-all duration-200 hover:bg-red-50 hover:border-red-300 hover:text-red-700 group/btn px-3"
                  title={t("jobs:actions.delete")}
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
                {t("common:loading.loading")}...
              </>
            ) : (
              t("jobs:actions.loadMore")
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
                    label: t("jobs:actions.clearSearch"),
                    onClick: () => {
                      setSearchQuery("");
                      fetchJobs(true);
                    },
                    variant: "outline",
                  },
                  {
                    label: t("jobs:actions.browseAll"),
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
                    label: t("jobs:actions.uploadFiles"),
                    onClick: () => (window.location.hash = "#upload"),
                    icon: Upload,
                  },
                ]
          }
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t("jobs:actions.confirmDelete", {
                jobNumber: deleteTarget?.job_number,
              })}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t("jobs:actions.confirmDeleteDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteTarget(null)}>
              {t("common:actions.cancel")}
            </AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete}>
              {t("common:actions.delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Job Modal */}
      <EditJobModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditTarget(null);
        }}
        onJobUpdated={handleJobUpdated}
        job={editTarget}
      />
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
