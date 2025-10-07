/**
 * Create Job Modal Component
 * Allows users to manually create new job descriptions
 */

import React, { useState } from "react";
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
import { Loader2, FileText } from "lucide-react";

interface CreateJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJobCreated: (jobId: number) => void;
}

export function CreateJobModal({
  isOpen,
  onClose,
  onJobCreated,
}: CreateJobModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    job_number: "",
    title: "",
    classification: "",
    language: "en",
    department: "",
    reports_to: "",
    content: "",
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.job_number || !formData.title || !formData.classification) {
      setError("Job Number, Title, and Classification are required");
      return;
    }

    setLoading(true);

    try {
      const result = await apiClient.createJob({
        job_number: formData.job_number,
        title: formData.title,
        classification: formData.classification,
        language: formData.language,
        department: formData.department || undefined,
        reports_to: formData.reports_to || undefined,
        content: formData.content || undefined,
      });

      // Reset form
      setFormData({
        job_number: "",
        title: "",
        classification: "",
        language: "en",
        department: "",
        reports_to: "",
        content: "",
      });

      onJobCreated(result.job_id);
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create job description",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      job_number: "",
      title: "",
      classification: "",
      language: "en",
      department: "",
      reports_to: "",
      content: "",
    });
    setError(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleCancel}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex-shrink-0">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Create New Job Description
            </DialogTitle>
            <DialogDescription>
              Manually create a new job description by filling out the form
              below.
            </DialogDescription>
          </DialogHeader>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          <div className="space-y-3 flex-1 overflow-y-auto pr-1">
            {/* Job Number */}
            <div className="space-y-2">
              <Label htmlFor="job_number">
                Job Number <span className="text-red-500">*</span>
              </Label>
              <Input
                id="job_number"
                placeholder="e.g., EX-01-123456"
                value={formData.job_number}
                onChange={(e) =>
                  handleInputChange("job_number", e.target.value)
                }
                required
              />
            </div>

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
              <Label htmlFor="content">Job Description Content</Label>
              <Textarea
                id="content"
                placeholder="Enter the full job description content..."
                value={formData.content}
                onChange={(e) => handleInputChange("content", e.target.value)}
                rows={8}
                className="resize-y"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}
          </div>

          <DialogFooter className="flex-shrink-0 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Create Job
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
