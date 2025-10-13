/**
 * Edit Job Modal Component
 * Allows users to edit existing job descriptions
 */

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiClient } from "@/lib/api";
import { Loader2, Edit, AlertCircle } from "lucide-react";
import type { JobDescription } from "@/lib/types";

interface EditJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJobUpdated: (jobId: number) => void;
  job: JobDescription | null;
}

export function EditJobModal({
  isOpen,
  onClose,
  onJobUpdated,
  job,
}: EditJobModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingJobData, setLoadingJobData] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: "",
    classification: "",
    language: "en",
    department: "",
    reports_to: "",
    raw_content: "",
  });

  // Load job data when modal opens or job changes
  useEffect(() => {
    if (isOpen && job) {
      setLoadingJobData(true);
      setError(null);

      // Fetch full job details including metadata
      apiClient
        .getJob(job.id, {
          include_content: true,
          include_metadata: true,
          include_sections: false,
        })
        .then((fullJob) => {
          setFormData({
            title: fullJob.title || "",
            classification: fullJob.classification || "",
            language: fullJob.language || "en",
            department: fullJob.metadata?.department || "",
            reports_to: fullJob.metadata?.reports_to || "",
            raw_content: fullJob.raw_content || "",
          });
        })
        .catch((err) => {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load job details"
          );
        })
        .finally(() => {
          setLoadingJobData(false);
        });
    }
  }, [isOpen, job]);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!job) return;

    setError(null);

    // Validation
    if (!formData.title || !formData.classification) {
      setError("Title and Classification are required");
      return;
    }

    setLoading(true);

    try {
      // Only send fields that have values (partial update)
      const updates: Record<string, string> = {};

      if (formData.title) updates.title = formData.title;
      if (formData.classification) updates.classification = formData.classification;
      if (formData.language) updates.language = formData.language;
      if (formData.department) updates.department = formData.department;
      if (formData.reports_to) updates.reports_to = formData.reports_to;
      if (formData.raw_content) updates.raw_content = formData.raw_content;

      await apiClient.updateJob(job.id, updates);

      onJobUpdated(job.id);
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update job description"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setError(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleCancel}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex-shrink-0">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Edit Job Description
            </DialogTitle>
            <DialogDescription>
              {job
                ? `Update details for ${job.job_number} - ${job.title}`
                : "Loading job details..."}
            </DialogDescription>
          </DialogHeader>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          {loadingJobData ? (
            <div className="flex flex-1 items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {/* Title */}
              <div className="space-y-2">
                <Label htmlFor="title">
                  Title <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="title"
                  placeholder="e.g., Director, Business Analysis"
                  value={formData.title}
                  onChange={(e) => handleInputChange("title", e.target.value)}
                  required
                />
              </div>

              {/* Classification */}
              <div className="space-y-2">
                <Label htmlFor="classification">
                  Classification <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="classification"
                  placeholder="e.g., EX-01"
                  value={formData.classification}
                  onChange={(e) =>
                    handleInputChange("classification", e.target.value)
                  }
                  required
                />
              </div>

              {/* Language */}
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select
                  value={formData.language}
                  onValueChange={(value) => handleInputChange("language", value)}
                >
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Department */}
              <div className="space-y-2">
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  placeholder="e.g., Information Technology"
                  value={formData.department}
                  onChange={(e) =>
                    handleInputChange("department", e.target.value)
                  }
                />
              </div>

              {/* Reports To */}
              <div className="space-y-2">
                <Label htmlFor="reports_to">Reports To</Label>
                <Input
                  id="reports_to"
                  placeholder="e.g., Chief Information Officer"
                  value={formData.reports_to}
                  onChange={(e) =>
                    handleInputChange("reports_to", e.target.value)
                  }
                />
              </div>

              {/* Content */}
              <div className="space-y-2">
                <Label htmlFor="raw_content">Job Description Content</Label>
                <Textarea
                  id="raw_content"
                  placeholder="Enter the full job description content..."
                  value={formData.raw_content}
                  onChange={(e) =>
                    handleInputChange("raw_content", e.target.value)
                  }
                  rows={8}
                  className="resize-y"
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}
            </div>
          )}

          <DialogFooter className="flex-shrink-0 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading || loadingJobData}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading || loadingJobData}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Edit className="w-4 h-4 mr-2" />
                  Update Job
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
