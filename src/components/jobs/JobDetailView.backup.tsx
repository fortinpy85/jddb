/**
 * Job Detail View Component
 * Displays job description with each section as a separate card
 * Includes action buttons and properties panel
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn, getLanguageName, getStatusColor } from "@/lib/utils";
import { apiClient } from "@/lib/api";
import type { JobDescription } from "@/lib/types";
import {
  ChevronLeft,
  Edit,
  CheckCircle,
  Copy,
  Languages,
  GitCompare,
  Download,
  Archive,
  FileText,
  Calendar,
  User,
  Building,
  DollarSign,
  AlertCircle,
  MoreVertical,
  Trash2,
  Share2,
  Printer,
} from "lucide-react";
import { LoadingState, ErrorState } from "@/components/ui/states";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";

interface JobDetailViewProps {
  jobId: number;
  onBack: () => void;
  onEdit?: (job: JobDescription) => void;
  onTranslate?: (job: JobDescription) => void;
  onCompare?: (job: JobDescription) => void;
  className?: string;
}

export function JobDetailView({
  jobId,
  onBack,
  onEdit,
  onTranslate,
  onCompare,
  className,
}: JobDetailViewProps) {
  const [job, setJob] = useState<JobDescription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addToast } = useToast();

  // Load job details
  useEffect(() => {
    loadJobDetails();
  }, [jobId]);

  const loadJobDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const jobData = await apiClient.getJob(jobId);
      setJob(jobData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load job details",
      );
    } finally {
      setLoading(false);
    }
  };

  // Action handlers
  const handleApprove = () => {
    addToast({
      title: "Job Approved",
      description: `Job ${job?.job_number} has been approved`,
      type: "success",
    });
  };

  const handleDuplicate = () => {
    addToast({
      title: "Job Duplicated",
      description: `Created a copy of job ${job?.job_number}`,
      type: "info",
    });
  };

  const handleExport = () => {
    addToast({
      title: "Exporting Job",
      description: `Exporting job ${job?.job_number} as PDF...`,
      type: "info",
    });
  };

  const handleArchive = () => {
    addToast({
      title: "Job Archived",
      description: `Job ${job?.job_number} has been archived`,
      type: "info",
    });
  };

  // Loading state
  if (loading) {
    return <LoadingState message="Loading job details..." />;
  }

  // Error state
  if (error) {
    return (
      <ErrorState
        title="Failed to load job"
        message={error}
        onAction={loadJobDetails}
        actionLabel="Try Again"
      />
    );
  }

  // Not found state
  if (!job) {
    return (
      <EmptyState
        type="general"
        title="Job not found"
        description="The requested job description could not be found"
        actions={[
          {
            label: "Back to Jobs",
            onClick: onBack,
          },
        ]}
      />
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Back Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onBack}
        className="-ml-2 shadow-button"
      >
        <ChevronLeft className="w-4 h-4 mr-1" />
        Back to Jobs
      </Button>

      {/* Header with Sticky Action Toolbar */}
      <div className="space-y-4">
        {/* Title Section */}
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            {job.job_number || "Untitled Job"}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {job.file_path}
          </p>
        </div>

        {/* Action Toolbar - Sticky with elevation */}
        <Card className="sticky top-16 z-40 elevation-3 shadow-card border-slate-200/50 dark:border-slate-700/50 bg-white/95 dark:bg-slate-800/95 backdrop-blur-md">
          <CardContent className="p-3">
            <div className="flex items-center justify-between gap-4">
              {/* Primary Actions */}
              <div className="flex items-center gap-2 flex-wrap">
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => onEdit?.(job)}
                  className="shadow-button"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Edit</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleApprove}
                  className="shadow-button"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Approve</span>
                </Button>

                <Separator
                  orientation="vertical"
                  className="h-6 hidden md:block"
                />

                {/* Secondary Actions - Hidden on mobile */}
                <div className="hidden md:flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onTranslate?.(job)}
                    className="shadow-button"
                  >
                    <Languages className="w-4 h-4 mr-2" />
                    Translate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onCompare?.(job)}
                    className="shadow-button"
                  >
                    <GitCompare className="w-4 h-4 mr-2" />
                    Compare
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExport}
                    className="shadow-button"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>

              {/* More Actions Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="shadow-button">
                    <MoreVertical className="w-4 h-4" />
                    <span className="sr-only">More actions</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="w-48 shadow-dropdown"
                >
                  {/* Mobile-only actions */}
                  <div className="md:hidden">
                    <DropdownMenuItem onClick={() => onTranslate?.(job)}>
                      <Languages className="w-4 h-4 mr-2" />
                      Translate
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onCompare?.(job)}>
                      <GitCompare className="w-4 h-4 mr-2" />
                      Compare
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleExport}>
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </div>

                  {/* Additional actions */}
                  <DropdownMenuItem onClick={handleDuplicate}>
                    <Copy className="w-4 h-4 mr-2" />
                    Duplicate
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Share2 className="w-4 h-4 mr-2" />
                    Share
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Printer className="w-4 h-4 mr-2" />
                    Print
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleArchive}>
                    <Archive className="w-4 h-4 mr-2" />
                    Archive
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-red-600 dark:text-red-400">
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metadata Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetadataCard
          icon={Building}
          label="Classification"
          value={job.classification || "N/A"}
          badge
        />
        <MetadataCard
          icon={Languages}
          label="Language"
          value={getLanguageName(job.language || "en")}
        />
        <MetadataCard
          icon={Calendar}
          label="Created"
          value={
            job.created_at
              ? new Date(job.created_at).toLocaleDateString()
              : "N/A"
          }
        />
        <MetadataCard
          icon={FileText}
          label="Status"
          value="N/A"
          statusBadge="N/A"
        />
      </div>

      {/* Job Sections */}
      <div className="grid grid-cols-1 gap-6">
        {job.sections && job.sections.length > 0 ? (
          job.sections.map((section, index) => (
            <JobSectionCard
              key={index}
              title={section.section_type}
              content={section.section_content}
            />
          ))
        ) : (
          <Card>
            <CardContent className="p-6">
              <p className="text-slate-600 dark:text-slate-400">
                No sections available for this job description.
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Additional Metadata */}
      {job.metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="w-5 h-5" />
              <span>Additional Information</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {job.metadata.reports_to && (
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Reports To
                  </label>
                  <p className="text-sm text-slate-900 dark:text-slate-100 mt-1">
                    {job.metadata.reports_to}
                  </p>
                </div>
              )}
              {job.metadata.department && (
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Department
                  </label>
                  <p className="text-sm text-slate-900 dark:text-slate-100 mt-1">
                    {job.metadata.department}
                  </p>
                </div>
              )}
              {job.metadata.salary_budget != null && (
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Budget Authority
                  </label>
                  <p className="text-sm text-slate-900 dark:text-slate-100 mt-1">
                    ${job.metadata.salary_budget?.toLocaleString() ?? "N/A"}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/**
 * Metadata Card Component
 */
interface MetadataCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  badge?: boolean;
  statusBadge?: string;
}

function MetadataCard({
  icon: Icon,
  label,
  value,
  badge,
  statusBadge,
}: MetadataCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
              {label}
            </p>
            {badge ? (
              <Badge variant="outline" className="mt-1 font-mono">
                {value}
              </Badge>
            ) : statusBadge ? (
              <Badge className={cn("mt-1", getStatusColor(statusBadge))}>
                {value}
              </Badge>
            ) : (
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate mt-1">
                {value}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Job Section Card Component
 */
interface JobSectionCardProps {
  title: string;
  content: string;
  className?: string;
}

function JobSectionCard({ title, content, className }: JobSectionCardProps) {
  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="capitalize">{title.replace(/_/g, " ")}</span>
          <Button variant="ghost" size="sm">
            <Edit className="w-4 h-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
            {content}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
