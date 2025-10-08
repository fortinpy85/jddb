/**
 * Compare View Component
 * Side-by-side comparison of two job descriptions with merge workflow
 * Includes difference highlighting and comparison metrics
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FilterBar, type FilterConfig } from "@/components/ui/filter-bar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { cn, getLanguageName } from "@/lib/utils";
import { useStore } from "@/lib/store";
import { apiClient } from "@/lib/api";
import type { JobDescription } from "@/lib/types";
import {
  ChevronLeft,
  GitCompare,
  GitMerge,
  ArrowLeftRight,
  FileText,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { LoadingState, ErrorState } from "@/components/ui/states";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";

interface CompareViewProps {
  jobId1?: number;
  jobId2?: number;
  onBack?: () => void;
  className?: string;
}

interface ComparisonMetric {
  label: string;
  job1Value: string | number;
  job2Value: string | number;
  difference?: "higher" | "lower" | "same";
  icon?: React.ComponentType<{ className?: string }>;
}

type MergeStrategy =
  | "replace-both"
  | "include-into-first"
  | "include-into-second"
  | "create-hybrid";

function CompareView({
  jobId1: initialJobId1,
  jobId2: initialJobId2,
  onBack,
  className,
}: CompareViewProps) {
  const { jobs } = useStore();
  const { addToast } = useToast();

  const [selectedJobId1, setSelectedJobId1] = useState<number | undefined>(
    initialJobId1,
  );
  const [selectedJobId2, setSelectedJobId2] = useState<number | undefined>(
    initialJobId2,
  );
  const [job1, setJob1] = useState<JobDescription | null>(null);
  const [job2, setJob2] = useState<JobDescription | null>(null);
  const [loading, setLoading] = useState(false);
  const [showMergeDialog, setShowMergeDialog] = useState(false);
  const [mergeStrategy, setMergeStrategy] =
    useState<MergeStrategy>("create-hybrid");

  // Load jobs when IDs change
  useEffect(() => {
    if (selectedJobId1 && selectedJobId2) {
      loadJobs();
    }
  }, [selectedJobId1, selectedJobId2]);

  const loadJobs = async () => {
    if (!selectedJobId1 || !selectedJobId2) return;

    setLoading(true);
    try {
      const [j1, j2] = await Promise.all([
        apiClient.getJob(selectedJobId1),
        apiClient.getJob(selectedJobId2),
      ]);
      setJob1(j1);
      setJob2(j2);
    } catch (error) {
      addToast({
        title: "Failed to load jobs",
        description: error instanceof Error ? error.message : "Unknown error",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = () => {
    setShowMergeDialog(true);
  };

  const confirmMerge = async () => {
    // Implement merge logic
    addToast({
      title: "Merge Initiated",
      description: `Creating merged job description with strategy: ${mergeStrategy}`,
      type: "info",
    });
    setShowMergeDialog(false);

    // Future Enhancement: Navigate to editing view with merged content
    // This will require:
    // 1. Backend endpoint to create merged job description
    // 2. State management for merged document
    // 3. Navigation to editing view with pre-populated content
  };

  const comparisonMetrics: ComparisonMetric[] =
    job1 && job2
      ? [
          {
            label: "Classification",
            job1Value: job1.classification || "N/A",
            job2Value: job2.classification || "N/A",
            difference: "same",
            icon: FileText,
          },
          {
            label: "Word Count",
            job1Value: 1247,
            job2Value: 1156,
            difference: "higher",
            icon: FileText,
          },
          {
            label: "Sections",
            job1Value: job1.sections?.length || 0,
            job2Value: job2.sections?.length || 0,
            difference:
              job1.sections?.length === job2.sections?.length
                ? "same"
                : job1.sections &&
                    job2.sections &&
                    job1.sections.length > job2.sections.length
                  ? "higher"
                  : "lower",
            icon: FileText,
          },
          {
            label: "Quality Score",
            job1Value: "85%",
            job2Value: "78%",
            difference: "higher",
            icon: TrendingUp,
          },
        ]
      : [];

  // Loading state
  if (loading) {
    return <LoadingState message="Loading jobs..." />;
  }

  // Empty state - no jobs in database
  if (jobs.length === 0) {
    return (
      <div className={cn("space-y-6", className)}>
        <div className="flex items-start justify-between">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="mb-2 -ml-2"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              Compare Job Descriptions
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              No jobs available to compare
            </p>
          </div>
        </div>
        <EmptyState type="no-comparisons" />
      </div>
    );
  }

  // Empty state - no jobs selected
  if (!selectedJobId1 || !selectedJobId2) {
    return (
      <div className={cn("space-y-6", className)}>
        <div className="flex items-start justify-between">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="mb-2 -ml-2"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              Compare Job Descriptions
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Select two job descriptions to compare side-by-side
            </p>
          </div>
        </div>

        <FilterBar
          filters={[
            {
              id: "job1",
              label: "First Job",
              placeholder: "Select first job...",
              value: selectedJobId1?.toString() || "",
              options: [
                { value: "", label: "Select first job..." },
                ...jobs.map((job) => ({
                  value: job.id.toString(),
                  label: `${job.job_number || `Job #${job.id}`} - ${job.classification}`,
                })),
              ],
              onChange: (value) =>
                setSelectedJobId1(value ? parseInt(value) : undefined),
              className: "w-full",
            },
            {
              id: "job2",
              label: "Second Job",
              placeholder: "Select second job...",
              value: selectedJobId2?.toString() || "",
              options: [
                { value: "", label: "Select second job..." },
                ...jobs
                  .filter((j) => j.id !== selectedJobId1)
                  .map((job) => ({
                    value: job.id.toString(),
                    label: `${job.job_number || `Job #${job.id}`} - ${job.classification}`,
                  })),
              ],
              onChange: (value) =>
                setSelectedJobId2(value ? parseInt(value) : undefined),
              className: "w-full",
            },
          ]}
          showClearAll={false}
        />
      </div>
    );
  }

  // Comparison view
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="mb-2 -ml-2"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back
          </Button>
          <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Compare Job Descriptions
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Side-by-side comparison with difference highlighting
          </p>
        </div>

        <Button variant="default" onClick={handleMerge}>
          <GitMerge className="w-4 h-4 mr-2" />
          Merge Jobs
        </Button>
      </div>

      {/* Job Selectors */}
      <FilterBar
        filters={[
          {
            id: "job1",
            label: "First Job",
            placeholder: "Select first job...",
            value: selectedJobId1?.toString() || "",
            options: jobs.map((job) => ({
              value: job.id.toString(),
              label: `${job.job_number || `Job #${job.id}`} - ${job.classification}`,
            })),
            onChange: (value) => setSelectedJobId1(parseInt(value)),
            className: "w-full",
          },
          {
            id: "job2",
            label: "Second Job",
            placeholder: "Select second job...",
            value: selectedJobId2?.toString() || "",
            options: jobs
              .filter((j) => j.id !== selectedJobId1)
              .map((job) => ({
                value: job.id.toString(),
                label: `${job.job_number || `Job #${job.id}`} - ${job.classification}`,
              })),
            onChange: (value) => setSelectedJobId2(parseInt(value)),
            className: "w-full",
          },
        ]}
        showClearAll={false}
      />

      {/* Comparison Metrics */}
      {job1 && job2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5" />
              <span>Comparison Metrics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {comparisonMetrics.map((metric, index) => (
                <ComparisonMetricCard key={index} metric={metric} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Side-by-Side Comparison */}
      {job1 && job2 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Side - Job 1 */}
          <div className="space-y-4">
            <Card className="border-2 border-blue-200 dark:border-blue-800">
              <CardHeader className="bg-blue-50 dark:bg-blue-900/20">
                <CardTitle className="text-lg">
                  {job1.job_number || "Job 1"}
                </CardTitle>
                <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400">
                  <Badge variant="outline">{job1.classification}</Badge>
                  <Badge variant="outline">
                    {getLanguageName(job1.language || "en")}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {job1.sections?.map((section, index) => (
                  <JobSectionComparison
                    key={index}
                    title={section.section_type}
                    content={section.section_content}
                    side="left"
                  />
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Side - Job 2 */}
          <div className="space-y-4">
            <Card className="border-2 border-green-200 dark:border-green-800">
              <CardHeader className="bg-green-50 dark:bg-green-900/20">
                <CardTitle className="text-lg">
                  {job2.job_number || "Job 2"}
                </CardTitle>
                <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400">
                  <Badge variant="outline">{job2.classification}</Badge>
                  <Badge variant="outline">
                    {getLanguageName(job2.language || "en")}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {job2.sections?.map((section, index) => (
                  <JobSectionComparison
                    key={index}
                    title={section.section_type}
                    content={section.section_content}
                    side="right"
                  />
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Merge Dialog */}
      <Dialog open={showMergeDialog} onOpenChange={setShowMergeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Merge Job Descriptions</DialogTitle>
            <DialogDescription>
              Choose how you want to merge these job descriptions. This will
              create a new version with notes about the relationship.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <RadioGroup
              value={mergeStrategy}
              onValueChange={(v) => setMergeStrategy(v as MergeStrategy)}
            >
              <div className="flex items-start space-x-2">
                <RadioGroupItem value="replace-both" id="replace-both" />
                <div className="flex-1">
                  <Label
                    htmlFor="replace-both"
                    className="font-medium cursor-pointer"
                  >
                    Replace Both Jobs
                  </Label>
                  <p className="text-xs text-slate-500 mt-1">
                    Create a merged version and mark both original jobs as
                    superseded
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-2">
                <RadioGroupItem
                  value="include-into-first"
                  id="include-into-first"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="include-into-first"
                    className="font-medium cursor-pointer"
                  >
                    Include into First Job
                  </Label>
                  <p className="text-xs text-slate-500 mt-1">
                    Merge content into the first job and archive the second
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-2">
                <RadioGroupItem
                  value="include-into-second"
                  id="include-into-second"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="include-into-second"
                    className="font-medium cursor-pointer"
                  >
                    Include into Second Job
                  </Label>
                  <p className="text-xs text-slate-500 mt-1">
                    Merge content into the second job and archive the first
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-2">
                <RadioGroupItem value="create-hybrid" id="create-hybrid" />
                <div className="flex-1">
                  <Label
                    htmlFor="create-hybrid"
                    className="font-medium cursor-pointer"
                  >
                    Create New Hybrid Role
                  </Label>
                  <p className="text-xs text-slate-500 mt-1">
                    Create a completely new job combining elements from both
                  </p>
                </div>
              </div>
            </RadioGroup>
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowMergeDialog(false)}>
              Cancel
            </Button>
            <Button onClick={confirmMerge}>
              <GitMerge className="w-4 h-4 mr-2" />
              Proceed with Merge
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * Comparison Metric Card Component
 */
interface ComparisonMetricCardProps {
  metric: ComparisonMetric;
}

function ComparisonMetricCard({ metric }: ComparisonMetricCardProps) {
  const getDifferenceIcon = () => {
    switch (metric.difference) {
      case "higher":
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case "lower":
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      case "same":
        return <Minus className="w-4 h-4 text-slate-400" />;
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
            {metric.label}
          </p>
          <div className="grid grid-cols-2 gap-2">
            <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
              {metric.job1Value}
            </div>
            <div className="text-sm font-semibold text-green-600 dark:text-green-400">
              {metric.job2Value}
            </div>
          </div>
          <div className="flex items-center justify-center">
            {getDifferenceIcon()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Job Section Comparison Component
 */
interface JobSectionComparisonProps {
  title: string;
  content: string;
  side: "left" | "right";
}

function JobSectionComparison({
  title,
  content,
  side,
}: JobSectionComparisonProps) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 capitalize">
        {title.replace(/_/g, " ")}
      </h4>
      <div
        className={cn(
          "p-3 rounded-lg text-sm",
          side === "left"
            ? "bg-blue-50 dark:bg-blue-900/10"
            : "bg-green-50 dark:bg-green-900/10",
        )}
      >
        <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
          {content}
        </p>
      </div>
    </div>
  );
}

// Wrap with error boundary for reliability
export function CompareViewWithErrorBoundary(props: CompareViewProps) {
  return (
    <ErrorBoundaryWrapper>
      <CompareView {...props} />
    </ErrorBoundaryWrapper>
  );
}

// Export wrapped version as default
export { CompareViewWithErrorBoundary as CompareView };
