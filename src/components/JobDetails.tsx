"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api";
import {
  getClassificationLevel,
  getLanguageName,
  handleExport,
} from "@/lib/utils";

import { useStore } from "@/lib/store";
import {
  ArrowLeft,
  AlertCircle,
  Calendar,
  CheckCircle,
  DollarSign,
  Download,
  FileText,
  MapPin,
  RefreshCw,
  Share,
  Users,
} from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { Breadcrumb } from "@/components/ui/breadcrumb";

interface JobDetailsProps {
  jobId: number;
  onBack?: () => void;
}

export function JobDetails({ jobId, onBack }: JobDetailsProps) {
  const { selectedJob, loading, error, selectJob } = useStore();
  const [activeTab, setActiveTab] = useState("overview");
  const { addToast } = useToast();

  useEffect(() => {
    const loadJobDetails = async () => {
      try {
        const response = await apiClient.getJob(jobId, {
          include_content: true,
          include_sections: true,
          include_metadata: true,
        });
        selectJob(response);
        addToast({
          title: "Job details loaded",
          description: `Successfully loaded details for ${response.title}`,
          type: "success",
          duration: 3000,
        });
      } catch (err) {
        console.error(err);
        addToast({
          title: "Failed to load job details",
          description: "Unable to fetch job details. Please try again.",
          type: "error",
        });
      }
    };

    if (
      jobId &&
      (!selectedJob || selectedJob.id !== jobId || !selectedJob.sections)
    ) {
      loadJobDetails();
    }
  }, [jobId, selectedJob, selectJob, addToast]);

  // Handle share
  const handleShare = async () => {
    if (!selectedJob) return;

    const shareData = {
      title: `Job Description: ${selectedJob.title}`,
      text: `${selectedJob.title} (${selectedJob.job_number}) - ${getClassificationLevel(selectedJob.classification)}`,
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        addToast({
          title: "Shared successfully",
          description: "Job details have been shared",
          type: "success",
        });
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(
          `${shareData.title}\n${shareData.text}\n${shareData.url}`,
        );
        addToast({
          title: "Copied to clipboard",
          description: "Job details have been copied to your clipboard",
          type: "success",
        });
      }
    } catch (err) {
      console.error("Share failed:", err);
      addToast({
        title: "Share failed",
        description: "Unable to share job details. Please try again.",
        type: "error",
      });
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {/* Header Skeleton */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <Skeleton className="h-8 w-24 mb-4" /> {/* Back button */}
                <div className="space-y-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <Skeleton className="h-8 w-64" /> {/* Job title */}
                    <Skeleton className="h-6 w-20" /> {/* Job number badge */}
                    <Skeleton className="h-6 w-16" />{" "}
                    {/* Classification badge */}
                    <Skeleton className="h-6 w-20" /> {/* Language badge */}
                  </div>
                  <Skeleton className="h-6 w-48" /> {/* Classification level */}
                  <div className="flex items-center gap-4 text-sm">
                    <Skeleton className="h-4 w-32" /> {/* Processed date */}
                    <Skeleton className="h-4 w-40" /> {/* File info */}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Skeleton className="h-8 w-16" /> {/* Share button */}
                <Skeleton className="h-8 w-20" /> {/* Export button */}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Skeleton */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin mr-2" />
              Loading job details...
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center text-red-600">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
          {onBack && (
            <Button variant="outline" onClick={onBack} className="mt-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to List
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  if (!selectedJob) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-gray-500">
            Job description not found.
          </div>
          {onBack && (
            <Button variant="outline" onClick={onBack} className="mt-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to List
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb
        items={[
          {
            label: "Jobs",
            onClick: onBack,
          },
          {
            label: selectedJob.job_number,
            current: true,
          },
        ]}
        className="mb-4"
      />

      {/* Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {onBack && (
                <Button variant="ghost" onClick={onBack} className="mb-4 px-0">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to List
                </Button>
              )}

              <div className="space-y-2">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-2xl font-bold">{selectedJob.title}</h2>
                  <Badge variant="secondary">{selectedJob.job_number}</Badge>
                  <Badge variant="outline">{selectedJob.classification}</Badge>
                  <Badge variant="outline">
                    {getLanguageName(selectedJob.language)}
                  </Badge>
                </div>

                <p className="text-lg text-gray-600">
                  {getClassificationLevel(selectedJob.classification)}
                </p>

                <div className="flex items-center gap-4 text-sm text-gray-500">
                  {selectedJob.processed_date && (
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      Processed:{" "}
                      {new Date(
                        selectedJob.processed_date,
                      ).toLocaleDateString()}
                    </div>
                  )}

                  <div className="flex items-center">
                    <FileText className="w-4 h-4 mr-1" />
                    File: {selectedJob.file_path.split("/").pop()}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Share className="w-4 h-4 mr-1" />
                Share
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport(selectedJob)}
              >
                <Download className="w-4 h-4 mr-1" />
                Export
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sections">Sections</TabsTrigger>
          <TabsTrigger value="metadata">Metadata</TabsTrigger>
          <TabsTrigger value="raw">Raw Content</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Information */}
          <Card>
            <CardHeader>
              <CardTitle>Key Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      Position Title
                    </label>
                    <p className="text-base">{selectedJob.title}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      Classification
                    </label>
                    <p className="text-base">
                      {selectedJob.classification} -{" "}
                      {getClassificationLevel(selectedJob.classification)}
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      Language
                    </label>
                    <p className="text-base">
                      {getLanguageName(selectedJob.language)}
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      Job Number
                    </label>
                    <p className="text-base font-mono">
                      {selectedJob.job_number}
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      File Hash
                    </label>
                    <p className="text-xs font-mono">{selectedJob.file_hash}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      Processing Status
                    </label>
                    <div className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                      <span className="text-green-600">Completed</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          {selectedJob.sections && selectedJob.sections.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Content Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold">
                      {selectedJob.sections.length}
                    </div>
                    <div className="text-sm text-gray-600">Sections</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {selectedJob.raw_content
                        ? Math.round(selectedJob.raw_content.length / 1000)
                        : 0}
                      K
                    </div>
                    <div className="text-sm text-gray-600">Characters</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {selectedJob.raw_content
                        ? selectedJob.raw_content.split(/\s+/).length
                        : 0}
                    </div>
                    <div className="text-sm text-gray-600">Words</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {selectedJob.metadata ? "✓" : "–"}
                    </div>
                    <div className="text-sm text-gray-600">Metadata</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Sections Tab */}
        <TabsContent value="sections" className="space-y-4">
          {selectedJob.sections && selectedJob.sections.length > 0 ? (
            selectedJob.sections
              .sort((a, b) => a.section_order - b.section_order)
              .map((section) => (
                <Card key={section.id}>
                  <CardHeader>
                    <CardTitle className="text-lg">
                      {section.section_type
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (l) => l.toUpperCase())}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose max-w-none">
                      <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                        {section.section_content}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              ))
          ) : (
            <EmptyState
              type="no-sections"
              title="No Sections Available"
              description="This job description hasn't been processed into sections yet. The content might need to be reprocessed or the original format may not be supported."
              actions={[
                {
                  label: "Reprocess Job",
                  onClick: async () => {
                    try {
                      const result = await apiClient.reprocessJob(
                        selectedJob.id,
                      );
                      addToast({
                        title: "Reprocessing started",
                        description: result.message,
                        type: "success",
                        duration: 4000,
                      });
                    } catch {
                      addToast({
                        title: "Reprocess failed",
                        description:
                          "Unable to reprocess job description. Please try again.",
                        type: "error",
                      });
                    }
                  },
                  variant: "default",
                },
                {
                  label: "View Raw Content",
                  onClick: () => setActiveTab("raw"),
                  variant: "outline",
                },
              ]}
            />
          )}
        </TabsContent>

        {/* Metadata Tab */}
        <TabsContent value="metadata" className="space-y-6">
          {selectedJob.metadata ? (
            <Card>
              <CardHeader>
                <CardTitle>Job Metadata</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    {selectedJob.metadata.reports_to && (
                      <div className="flex items-start">
                        <Users className="w-5 h-5 mr-3 mt-0.5 text-gray-400" />
                        <div>
                          <label className="text-sm font-medium text-gray-600">
                            Reports To
                          </label>
                          <p className="text-base">
                            {selectedJob.metadata.reports_to}
                          </p>
                        </div>
                      </div>
                    )}

                    {selectedJob.metadata.department && (
                      <div className="flex items-start">
                        <FileText className="w-5 h-5 mr-3 mt-0.5 text-gray-400" />
                        <div>
                          <label className="text-sm font-medium text-gray-600">
                            Department
                          </label>
                          <p className="text-base">
                            {selectedJob.metadata.department}
                          </p>
                        </div>
                      </div>
                    )}

                    {selectedJob.metadata.location && (
                      <div className="flex items-start">
                        <MapPin className="w-5 h-5 mr-3 mt-0.5 text-gray-400" />
                        <div>
                          <label className="text-sm font-medium text-gray-600">
                            Location
                          </label>
                          <p className="text-base">
                            {selectedJob.metadata.location}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-4">
                    {selectedJob.metadata.fte_count !== null &&
                      selectedJob.metadata.fte_count !== undefined && (
                        <div className="flex items-start">
                          <Users className="w-5 h-5 mr-3 mt-0.5 text-gray-400" />
                          <div>
                            <label className="text-sm font-medium text-gray-600">
                              FTE Count
                            </label>
                            <p className="text-base">
                              {selectedJob.metadata.fte_count}
                            </p>
                          </div>
                        </div>
                      )}

                    {selectedJob.metadata.salary_budget && (
                      <div className="flex items-start">
                        <DollarSign className="w-5 h-5 mr-3 mt-0.5 text-gray-400" />
                        <div>
                          <label className="text-sm font-medium text-gray-600">
                            Salary Budget
                          </label>
                          <p className="text-base">
                            $
                            {selectedJob.metadata.salary_budget.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    )}

                    {selectedJob.metadata.effective_date && (
                      <div className="flex items-start">
                        <Calendar className="w-5 h-5 mr-3 mt-0.5 text-gray-400" />
                        <div>
                          <label className="text-sm font-medium text-gray-600">
                            Effective Date
                          </label>
                          <p className="text-base">
                            {new Date(
                              selectedJob.metadata.effective_date,
                            ).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-gray-500">
                  No metadata available for this job description.
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Raw Content Tab */}
        <TabsContent value="raw">
          <Card>
            <CardHeader>
              <CardTitle>Raw Content</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedJob.raw_content ? (
                <div className="bg-gray-50 border rounded p-4 max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                    {selectedJob.raw_content}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No raw content available.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Wrap with error boundary for reliability
const JobDetailsWithErrorBoundary = (props: JobDetailsProps) => (
  <ErrorBoundaryWrapper>
    <JobDetails {...props} />
  </ErrorBoundaryWrapper>
);

export default React.memo(JobDetailsWithErrorBoundary);
