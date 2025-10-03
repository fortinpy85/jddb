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
import { Checkbox } from "@/components/ui/checkbox";
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
import type { JobDescription } from "@/lib/types";
import { useStore } from "@/lib/store";
import { cn, getLanguageName, getStatusColor } from "@/lib/utils";
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
} from "lucide-react";
import { useToast } from "@/components/ui/toast";
import {
  LoadingState,
  ErrorState,
  TableSkeleton,
} from "@/components/ui/states";
import { EmptyState } from "@/components/ui/empty-state";

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

export function JobsTable({
  onJobSelect,
  onNavigateToUpload,
  onNavigateToSearch,
  onCreateNew,
  className,
}: JobsTableProps) {
  const { jobs, loading, error, fetchJobs } = useStore();
  const { addToast } = useToast();

  // Local state
  const [selectedJobs, setSelectedJobs] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [filterClassification, setFilterClassification] =
    useState<string>("all");
  const [filterLanguage, setFilterLanguage] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

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
    addToast({
      title: action,
      description: `${action} job ${job.job_number}`,
      type: "info",
    });
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
    return (
      <EmptyState
        type="no-jobs"
        actions={
          onNavigateToUpload
            ? [
                {
                  label: "Upload Jobs",
                  onClick: onNavigateToUpload,
                  variant: "default" as const,
                  icon: Upload,
                },
              ]
            : []
        }
      />
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
            Job Descriptions
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            {filteredJobs.length} of {jobs.length} jobs
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
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
      <Card className="elevation-1 shadow-card">
        <CardContent className="p-4">
          <div className="flex flex-col gap-3">
            {/* Search */}
            <div className="w-full">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search by job number, filename, or classification..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 shadow-input"
                />
              </div>
            </div>

            {/* Filters Row */}
            <div className="flex flex-wrap gap-3">
              {/* Classification Filter */}
              <Select
                value={filterClassification}
                onValueChange={setFilterClassification}
              >
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="Classification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Classifications</SelectItem>
                  {classifications.map((c) => (
                    <SelectItem key={c} value={c!}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Language Filter */}
              <Select value={filterLanguage} onValueChange={setFilterLanguage}>
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="Language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Languages</SelectItem>
                  {languages.map((lang) => (
                    <SelectItem key={lang} value={lang!}>
                      {getLanguageName(lang!)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Status Filter */}
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

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
        </CardContent>
      </Card>

      {/* Table */}
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
                      <Badge variant="outline" className="font-mono">
                        {job.classification || "N/A"}
                      </Badge>
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
                      <Badge className={getStatusColor("N/A")}>
                        N/A
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-1">
                        <div className="w-16 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500"
                            style={{ width: "85%" }}
                          />
                        </div>
                        <span className="text-xs text-slate-600 dark:text-slate-400">
                          85%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {new Date(job.created_at || Date.now()).toLocaleDateString()}
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
                          >
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onJobSelect?.(job)}>
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
                            onClick={() => handleJobAction(job, "Delete")}
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
    </div>
  );
}
