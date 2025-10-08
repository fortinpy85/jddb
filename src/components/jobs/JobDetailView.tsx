/**
 * Job Detail View Component
 * Displays job description with each section as a separate card
 * Includes action buttons and properties panel
 */

"use client";

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ClassificationBadge } from "@/components/ui/classification-badge";
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
import { QualityDashboard } from "@/components/ai/QualityDashboard";
import { ContentGeneratorModal } from "@/components/ai/ContentGeneratorModal";
import { useAISuggestions } from "@/hooks/useAISuggestions";
import { WorkflowStepper } from "@/components/ui/workflow-stepper";
import { SkillTagsSection } from "@/components/skills/SkillTags";

interface JobDetailViewProps {
  jobId: number;
  onBack: () => void;
  onEdit?: (job: JobDescription) => void;
  onTranslate?: (job: JobDescription) => void;
  onCompare?: (job: JobDescription) => void;
  className?: string;
}

function JobDetailView({
  jobId,
  onBack,
  onEdit,
  onTranslate,
  onCompare,
  className,
}: JobDetailViewProps) {
  const { t } = useTranslation(["jobs", "common"]);
  const [job, setJob] = useState<JobDescription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addToast } = useToast();
  const {
    qualityScore,
    calculateQuality,
    isLoading: qualityLoading,
  } = useAISuggestions();

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

      // Calculate quality score if sections are available
      if (jobData.sections && jobData.sections.length > 0) {
        const sectionsMap: Record<string, string> = {};
        jobData.sections.forEach((section) => {
          sectionsMap[section.section_type] = section.section_content;
        });
        await calculateQuality(sectionsMap);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t("jobs:messages.loadFailed"),
      );
    } finally {
      setLoading(false);
    }
  };

  // Action handlers
  const handleApprove = () => {
    addToast({
      title: t("jobs:messages.jobApproved"),
      description: t("jobs:messages.jobApprovedDescription", {
        jobNumber: job?.job_number,
      }),
      type: "success",
    });
  };

  const handleDuplicate = () => {
    addToast({
      title: t("jobs:messages.jobDuplicated"),
      description: t("jobs:messages.jobDuplicatedDescription", {
        jobNumber: job?.job_number,
      }),
      type: "info",
    });
  };

  const handleExport = () => {
    addToast({
      title: t("jobs:messages.exportingJob"),
      description: t("jobs:messages.exportingJobDescription", {
        jobNumber: job?.job_number,
      }),
      type: "info",
    });
  };

  const handleArchive = () => {
    addToast({
      title: t("jobs:messages.jobArchived"),
      description: t("jobs:messages.jobArchivedDescription", {
        jobNumber: job?.job_number,
      }),
      type: "info",
    });
  };

  // Loading state
  if (loading) {
    return <LoadingState message={t("jobs:messages.loadingDetails")} />;
  }

  // Error state
  if (error) {
    return (
      <ErrorState
        title={t("jobs:messages.loadFailed")}
        message={error}
        onAction={loadJobDetails}
        actionLabel={t("common:actions.tryAgain")}
      />
    );
  }

  // Not found state
  if (!job) {
    return (
      <EmptyState
        type="general"
        title={t("jobs:messages.jobNotFound")}
        description={t("jobs:messages.jobNotFoundDescription")}
        actions={[
          {
            label: t("jobs:actions.backToJobs"),
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
        aria-label={t("jobs:actions.backToJobsAria")}
      >
        <ChevronLeft className="w-4 h-4 mr-1" />
        {t("jobs:actions.backToJobs")}
      </Button>

      {/* Workflow Progress Indicator */}
      <div className="bg-card border rounded-lg p-4">
        <WorkflowStepper currentStep="review" completedSteps={["upload"]} />
      </div>

      {/* Header with Sticky Action Toolbar */}
      <div className="space-y-4">
        {/* Title Section */}
        <div className="space-y-1">
          <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            {job.job_number || "Untitled Job"}
          </h2>
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
                  aria-label={t("jobs:actions.editJobAria", {
                    jobNumber: job.job_number || "description",
                  })}
                >
                  <Edit className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">
                    {t("jobs:actions.edit")}
                  </span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleApprove}
                  className="shadow-button"
                  aria-label={t("jobs:actions.approveJobAria", {
                    jobNumber: job.job_number || "description",
                  })}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">
                    {t("jobs:actions.approve")}
                  </span>
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
                    {t("jobs:actions.translate")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onCompare?.(job)}
                    className="shadow-button"
                  >
                    <GitCompare className="w-4 h-4 mr-2" />
                    {t("jobs:actions.compare")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExport}
                    className="shadow-button"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {t("jobs:actions.export")}
                  </Button>
                </div>
              </div>

              {/* More Actions Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="shadow-button">
                    <MoreVertical className="w-4 h-4" />
                    <span className="sr-only">
                      {t("jobs:actions.moreActions")}
                    </span>
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
                      {t("jobs:actions.translate")}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onCompare?.(job)}>
                      <GitCompare className="w-4 h-4 mr-2" />
                      {t("jobs:actions.compare")}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleExport}>
                      <Download className="w-4 h-4 mr-2" />
                      {t("jobs:actions.export")}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </div>

                  {/* Additional actions */}
                  <DropdownMenuItem onClick={handleDuplicate}>
                    <Copy className="w-4 h-4 mr-2" />
                    {t("jobs:actions.duplicate")}
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Share2 className="w-4 h-4 mr-2" />
                    {t("jobs:actions.share")}
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Printer className="w-4 h-4 mr-2" />
                    {t("jobs:actions.print")}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleArchive}>
                    <Archive className="w-4 h-4 mr-2" />
                    {t("jobs:actions.archive")}
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-red-600 dark:text-red-400">
                    <Trash2 className="w-4 h-4 mr-2" />
                    {t("jobs:actions.delete")}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metadata Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Classification Card with ClassificationBadge */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <Building className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                  {t("jobs:fields.classification")}
                </p>
                <div className="mt-1">
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
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <MetadataCard
          icon={Languages}
          label={t("jobs:fields.language")}
          value={getLanguageName(job.language || "en")}
        />
        <MetadataCard
          icon={Calendar}
          label={t("jobs:fields.createdDate")}
          value={
            job.created_at
              ? new Date(job.created_at).toLocaleDateString()
              : "N/A"
          }
        />
        <MetadataCard
          icon={FileText}
          label={t("jobs:fields.status")}
          value="N/A"
          statusBadge="N/A"
        />
      </div>

      {/* Quality Dashboard */}
      {qualityScore && (
        <QualityDashboard
          qualityScore={qualityScore}
          loading={qualityLoading}
          className="mb-6"
        />
      )}

      {/* Extracted Skills */}
      {job.skills && job.skills.length > 0 && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <SkillTagsSection skills={job.skills} />
          </CardContent>
        </Card>
      )}

      {/* Job Sections */}
      <div className="grid grid-cols-1 gap-6">
        {job.sections && job.sections.length > 0 ? (
          job.sections.map((section, index) => (
            <JobSectionCard
              key={index}
              title={section.section_type}
              content={section.section_content}
              jobNumber={job.job_number}
              classification={job.classification}
              onContentUpdate={(newContent) => {
                // Update section content
                setJob((prev) => {
                  if (!prev || !prev.sections) return prev;
                  return {
                    ...prev,
                    sections: prev.sections.map((s, i) =>
                      i === index ? { ...s, section_content: newContent } : s,
                    ),
                  };
                });
                addToast({
                  title: t("jobs:messages.contentUpdated"),
                  description: t("jobs:messages.sectionUpdated", {
                    section: section.section_type,
                  }),
                  type: "success",
                });
              }}
            />
          ))
        ) : (
          <EmptyState type="no-sections" />
        )}
      </div>

      {/* Additional Metadata */}
      {job.metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="w-5 h-5" />
              <span>{t("jobs:details.additionalInformation")}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {job.metadata.reports_to && (
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    {t("jobs:fields.reportsTo")}
                  </label>
                  <p className="text-sm text-slate-900 dark:text-slate-100 mt-1">
                    {job.metadata.reports_to}
                  </p>
                </div>
              )}
              {job.metadata.department && (
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    {t("jobs:fields.department")}
                  </label>
                  <p className="text-sm text-slate-900 dark:text-slate-100 mt-1">
                    {job.metadata.department}
                  </p>
                </div>
              )}
              {job.metadata.salary_budget != null && (
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    {t("jobs:fields.budget")}
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
  jobNumber?: string;
  classification?: string;
  onContentUpdate?: (newContent: string) => void;
  className?: string;
}

function JobSectionCard({
  title,
  content,
  jobNumber,
  classification,
  onContentUpdate,
  className,
}: JobSectionCardProps) {
  const [showGenerator, setShowGenerator] = useState(false);

  const handleGenerate = (generatedContent: string) => {
    if (onContentUpdate) {
      onContentUpdate(generatedContent);
    }
    setShowGenerator(false);
  };

  return (
    <>
      <Card className={cn("hover:shadow-md transition-shadow", className)}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="capitalize">{title.replace(/_/g, " ")}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowGenerator(true)}
              aria-label={t("jobs:actions.editSectionAria", {
                section: title.replace(/_/g, " "),
              })}
            >
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

      <ContentGeneratorModal
        open={showGenerator}
        onClose={() => setShowGenerator(false)}
        onInsert={handleGenerate}
        mode="enhance"
        initialContent={content}
        classification={classification || "EX-01"}
        language="en"
      />
    </>
  );
}

// Export memoized component for performance
export default React.memo(JobDetailView);
export { JobDetailView };
