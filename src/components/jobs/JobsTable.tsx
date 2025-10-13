/**
 * Jobs Table Component
 * Advanced table view for job descriptions with sorting, filtering, and bulk actions
 * Displayed in center panel of landing page
 */

"use client";

import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ClassificationBadge } from "@/components/ui/classification-badge";
import { Checkbox } from "@/components/ui/checkbox";
import { FilterBar, type FilterConfig } from "@/components/ui/filter-bar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { JobDescription } from "@/lib/types";
import { useStore } from "@/lib/store";
import { cn, getLanguageName, getStatusColor } from "@/lib/utils";
import { apiClient } from "@/lib/api";
import {
  Search,
  Filter,
  Upload,
  Plus,
  Download,
  MoreVertical,
  Eye,
  Edit,
  Copy,
  Trash2,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  FileText,
  ChevronLeft,
  ChevronRight,
  Languages,
  Briefcase,
  Grid3x3,
  List,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";
import {
  LoadingState,
  ErrorState,
  TableSkeleton,
} from "@/components/ui/states";
import { EmptyState } from "@/components/ui/empty-state";
import { JobGridView } from "./JobGridView";

interface JobsTableProps {
  onJobSelect?: (job: JobDescription) => void;
  onNavigateToUpload?: () => void;
  onNavigateToSearch?: () => void;
  onCreateNew?: () => void;
  className?: string;
}

type SortField =
  | "id"
  | "job_number"
  | "classification"
  | "language"
  | "created_at";
type SortDirection = "asc" | "desc";

function JobsTable({
  onJobSelect,
  onNavigateToUpload,
  onNavigateToSearch,
  onCreateNew,
  className,
}: JobsTableProps) {
  const { jobs, loading, error, fetchJobs, pagination } = useStore();
  const { addToast } = useToast();

  // Local state
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [selectedJobs, setSelectedJobs] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [filterClassification, setFilterClassification] =
    useState<string>("all");
  const [filterLanguage, setFilterLanguage] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterSkills, setFilterSkills] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Delete confirmation dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<JobDescription | null>(null);

  // Filtered and sorted jobs
  const filteredJobs = useMemo(() => {
    let filtered = [...jobs];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (job) =>
          job.job_number?.toLowerCase().includes(query) ||
          job.file_path?.toLowerCase().includes(query) ||
          job.classification?.toLowerCase().includes(query),
      );
    }

    // Classification filter
    if (filterClassification !== "all") {
      filtered = filtered.filter(
        (job) => job.classification === filterClassification,
      );
    }

    // Language filter
    if (filterLanguage !== "all") {
      filtered = filtered.filter((job) => job.language === filterLanguage);
    }

    // Skill filter - jobs must have ALL selected skills
    if (filterSkills.length > 0) {
      filtered = filtered.filter((job) => {
        if (!job.skills || job.skills.length === 0) return false;
        const jobSkillIds = job.skills.map((skill) => skill.id);
        return filterSkills.every((skillId) => jobSkillIds.includes(skillId));
      });
    }

    // Sorting
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortField) {
        case "id":
          aVal = a.id;
          bVal = b.id;
          break;
        case "job_number":
          aVal = a.job_number || "";
          bVal = b.job_number || "";
          break;
        case "classification":
          aVal = a.classification || "";
          bVal = b.classification || "";
          break;
        case "language":
          aVal = a.language || "";
          bVal = b.language || "";
          break;
        case "created_at":
          aVal = new Date(a.created_at || 0).getTime();
          bVal = new Date(b.created_at || 0).getTime();
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [
    jobs,
    searchQuery,
    filterClassification,
    filterLanguage,
    filterSkills,
    sortField,
    sortDirection,
  ]);

  // Pagination
  const totalPages = Math.ceil(filteredJobs.length / pageSize);
  const paginatedJobs = filteredJobs.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  // Get unique values for filters
  const classifications = useMemo(
    () =>
      Array.from(new Set(jobs.map((j) => j.classification).filter(Boolean))),
    [jobs],
  );
  const languages = useMemo(
    () => Array.from(new Set(jobs.map((j) => j.language).filter(Boolean))),
    [jobs],
  );

  // Get all unique skills across all jobs
  const availableSkills = useMemo(() => {
    const skillMap = new Map();
    jobs.forEach((job) => {
      job.skills?.forEach((skill) => {
        if (!skillMap.has(skill.id)) {
          skillMap.set(skill.id, skill);
        }
      });
    });
    return Array.from(skillMap.values()).sort((a, b) =>
      a.name.localeCompare(b.name),
    );
  }, [jobs]);

  // Handlers
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedJobs(paginatedJobs.map((j) => j.id));
    } else {
      setSelectedJobs([]);
    }
  };

  const handleSelectJob = (jobId: number, checked: boolean) => {
    if (checked) {
      setSelectedJobs([...selectedJobs, jobId]);
    } else {
      setSelectedJobs(selectedJobs.filter((id) => id !== jobId));
    }
  };

  const handleBulkAction = (action: string) => {
    addToast({
      title: "Bulk Action",
      description: `${action} ${selectedJobs.length} jobs`,
      type: "info",
    });
    setSelectedJobs([]);
  };

  const handleJobAction = (job: JobDescription, action: string) => {
    if (action === "Delete") {
      // Show delete confirmation dialog
      setJobToDelete(job);
      setDeleteDialogOpen(true);
    } else {
      // For other actions, just show toast (placeholder)
      addToast({
        title: action,
        description: `${action} job ${job.job_number}`,
        type: "info",
      });
    }
  };

  const handleConfirmDelete = async () => {
    if (!jobToDelete) return;

    try {
      // Call delete API using apiClient
      await apiClient.deleteJob(jobToDelete.id);

      addToast({
        title: "Job Deleted",
        description: `Successfully deleted job ${jobToDelete.job_number}`,
        type: "success",
      });

      // Refresh jobs list
      await fetchJobs(true);

      // Close dialog and reset state
      setDeleteDialogOpen(false);
      setJobToDelete(null);
    } catch (error) {
      addToast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Failed to delete job",
        type: "error",
      });
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setJobToDelete(null);
  };

  // Render sort icon
  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 ml-1 text-slate-400" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="w-4 h-4 ml-1 text-blue-600" />
    ) : (
      <ArrowDown className="w-4 h-4 ml-1 text-blue-600" />
    );
  };

  // Loading and error states
  if (loading && jobs.length === 0) {
    return (
      <div className="space-y-4">
        {/* Header skeleton */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-2 animate-pulse">
            <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-48"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-32"></div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="h-9 w-24 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
            <div className="h-9 w-32 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
            <div className="h-9 w-36 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
          </div>
        </div>
        {/* Table skeleton */}
        <TableSkeleton rows={8} columns={5} showHeader={false} />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to load jobs"
        message={error}
        onAction={() => fetchJobs(true)}
      />
    );
  }

  if (jobs.length === 0) {
    const actions = [];

    if (onNavigateToUpload) {
      actions.push({
        label: "Upload Jobs",
        onClick: onNavigateToUpload,
        variant: "default" as const,
        icon: Upload,
      });
    }

    if (onCreateNew) {
      actions.push({
        label: "Create New",
        onClick: onCreateNew,
        variant: "outline" as const,
        icon: Plus,
      });
    }

    return <EmptyState type="no-jobs" actions={actions} />;
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
            Job Descriptions
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            {filteredJobs.length} of {pagination.total} jobs
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex gap-1 border rounded-md">
            <Button
              variant={viewMode === "table" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-r-none"
              onClick={() => setViewMode("table")}
              title="Table View"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "grid" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-l-none"
              onClick={() => setViewMode("grid")}
              title="Grid View"
            >
              <Grid3x3 className="h-4 w-4" />
            </Button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={onNavigateToUpload}
            className="shadow-button"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onCreateNew}
            className="shadow-button"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create New
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onNavigateToSearch}
            className="shadow-button"
          >
            <Search className="w-4 h-4 mr-2" />
            Advanced Search
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <FilterBar
        searchValue={searchQuery}
        searchPlaceholder="Search by job number, filename, or classification..."
        onSearchChange={setSearchQuery}
        filters={[
          {
            id: "classification",
            label: "Classification",
            placeholder: "All Classifications",
            value: filterClassification,
            options: [
              { value: "all", label: "All Classifications" },
              ...classifications.map((c) => ({ value: c!, label: c! })),
            ],
            onChange: setFilterClassification,
          },
          {
            id: "language",
            label: "Language",
            placeholder: "All Languages",
            value: filterLanguage,
            options: [
              { value: "all", label: "All Languages" },
              ...languages.map((lang) => ({
                value: lang!,
                label: getLanguageName(lang!),
              })),
            ],
            onChange: setFilterLanguage,
          },
          {
            id: "status",
            label: "Status",
            placeholder: "All Statuses",
            value: filterStatus,
            options: [
              { value: "all", label: "All Statuses" },
              { value: "completed", label: "Completed" },
              { value: "in_progress", label: "In Progress" },
              { value: "failed", label: "Failed" },
            ],
            onChange: setFilterStatus,
          },
        ]}
        onClearAll={() => {
          setSearchQuery("");
          setFilterClassification("all");
          setFilterLanguage("all");
          setFilterStatus("all");
          setFilterSkills([]);
        }}
      >
        {/* Bulk Actions */}
        {selectedJobs.length > 0 && (
          <div className="mt-3 flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
              {selectedJobs.length} selected
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBulkAction("Export")}
              className="shadow-button"
            >
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBulkAction("Delete")}
              className="shadow-button"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Delete
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedJobs([])}
              className="ml-auto shadow-button"
            >
              Clear
            </Button>
          </div>
        )}
      </FilterBar>

      {/* Skills Filter */}
      {availableSkills.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Filter by Skills:
          </span>
          {filterSkills.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap">
              {filterSkills.map((skillId) => {
                const skill = availableSkills.find((s) => s.id === skillId);
                if (!skill) return null;
                return (
                  <Badge
                    key={skillId}
                    variant="default"
                    className="cursor-pointer hover:bg-primary/80"
                    onClick={() =>
                      setFilterSkills(
                        filterSkills.filter((id) => id !== skillId),
                      )
                    }
                  >
                    {skill.name} ×
                  </Badge>
                );
              })}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilterSkills([])}
                className="h-6 px-2 text-xs"
              >
                Clear
              </Button>
            </div>
          )}
          <Select
            value=""
            onValueChange={(value) => {
              const skillId = parseInt(value);
              if (!filterSkills.includes(skillId)) {
                setFilterSkills([...filterSkills, skillId]);
              }
            }}
          >
            <SelectTrigger className="w-[250px] h-8 text-sm">
              <SelectValue placeholder="Add skill filter..." />
            </SelectTrigger>
            <SelectContent>
              {availableSkills.map((skill) => (
                <SelectItem
                  key={skill.id}
                  value={skill.id.toString()}
                  disabled={filterSkills.includes(skill.id)}
                >
                  {skill.name}
                  {skill.skill_type && (
                    <span className="text-xs text-muted-foreground ml-2">
                      ({skill.skill_type})
                    </span>
                  )}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Conditional View: Table or Grid */}
      {viewMode === "grid" ? (
        <JobGridView
          jobs={filteredJobs}
          onJobSelect={onJobSelect || (() => {})}
          onJobEdit={(job) => handleJobAction(job, "Edit")}
          onJobDelete={(job) => handleJobAction(job, "Delete")}
          isLoading={loading}
        />
      ) : (
        <Card className="elevation-1 shadow-card">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-4 py-3 text-left w-12">
                      <Checkbox
                        checked={
                          selectedJobs.length === paginatedJobs.length &&
                          paginatedJobs.length > 0
                        }
                        onCheckedChange={handleSelectAll}
                      />
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort("job_number")}
                        className="flex items-center text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider hover:text-slate-900 dark:hover:text-slate-100"
                      >
                        Job Number
                        {renderSortIcon("job_number")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                        Job Title
                      </span>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort("classification")}
                        className="flex items-center text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider hover:text-slate-900 dark:hover:text-slate-100"
                      >
                        Classification
                        {renderSortIcon("classification")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort("language")}
                        className="flex items-center text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider hover:text-slate-900 dark:hover:text-slate-100"
                      >
                        Language
                        {renderSortIcon("language")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                        Status
                      </span>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                        Quality
                      </span>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort("created_at")}
                        className="flex items-center text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider hover:text-slate-900 dark:hover:text-slate-100"
                      >
                        Created
                        {renderSortIcon("created_at")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-right w-20">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                        Actions
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {paginatedJobs.map((job) => (
                    <tr
                      key={job.id}
                      className="shadow-table-row cursor-pointer"
                      onClick={() => onJobSelect?.(job)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onJobSelect?.(job);
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`View job ${job.job_number || "N/A"}: ${job.title || "Untitled"}`}
                    >
                      <td
                        className="px-4 py-3"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Checkbox
                          checked={selectedJobs.includes(job.id)}
                          onCheckedChange={(checked) =>
                            handleSelectJob(job.id, checked as boolean)
                          }
                          aria-label={`Select job ${job.job_number || job.id}`}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <FileText className="w-4 h-4 text-slate-400" />
                          <span className="font-medium text-slate-900 dark:text-slate-100">
                            {job.job_number || "N/A"}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-slate-700 dark:text-slate-300">
                          {job.title || "N/A"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {job.classification ? (
                          <ClassificationBadge
                            code={job.classification}
                            showHelpIcon
                          />
                        ) : (
                          <Badge variant="outline" className="font-mono">
                            N/A
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-1">
                          <Languages className="w-4 h-4 text-slate-400" />
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {getLanguageName(job.language || "en")}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={getStatusColor("N/A")}>N/A</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-1">
                          <div className="w-16 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                (job.quality_score || 0) >= 0.7
                                  ? "bg-green-500"
                                  : (job.quality_score || 0) >= 0.4
                                    ? "bg-yellow-500"
                                    : "bg-red-500"
                              }`}
                              style={{
                                width: `${Math.round((job.quality_score || 0) * 100)}%`,
                              }}
                            />
                          </div>
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {Math.round((job.quality_score || 0) * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {new Date(
                            job.created_at || Date.now(),
                          ).toLocaleDateString()}
                        </span>
                      </td>
                      <td
                        className="px-4 py-3 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              aria-label={`Actions for job ${job.job_number || job.id}`}
                            >
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => onJobSelect?.(job)}
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleJobAction(job, "Edit")}
                            >
                              <Edit className="w-4 h-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleJobAction(job, "Duplicate")}
                            >
                              <Copy className="w-4 h-4 mr-2" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onSelect={(e) => {
                                e.preventDefault();
                                handleJobAction(job, "Delete");
                              }}
                              className="text-red-600"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Page {currentPage} of {totalPages}
                  </span>
                  <Select
                    value={pageSize.toString()}
                    onValueChange={(value) => setPageSize(parseInt(value))}
                  >
                    <SelectTrigger className="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="20">20</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    per page
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentPage(Math.min(totalPages, currentPage + 1))
                    }
                    disabled={currentPage === totalPages}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Job Description?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete job{" "}
              <span className="font-semibold">{jobToDelete?.job_number}</span>
              {jobToDelete?.title && (
                <>
                  {" "}
                  - <span className="font-semibold">{jobToDelete.title}</span>
                </>
              )}
              ? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDelete}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// Export memoized component for performance
export { JobsTable };
