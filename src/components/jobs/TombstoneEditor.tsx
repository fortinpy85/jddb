/**
 * Tombstone Editor Modal
 * Quick edit for job metadata (tombstone information) from the job list
 * Edits: title, classification, language, department, reports_to, effective_date
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
import { useTranslation } from "react-i18next";

export interface TombstoneEditorProps {
  isOpen: boolean;
  onClose: () => void;
  onJobUpdated: (jobId: number) => void;
  job: JobDescription | null;
}

export function TombstoneEditor({
  isOpen,
  onClose,
  onJobUpdated,
  job,
}: TombstoneEditorProps) {
  const { t } = useTranslation(["jobs", "common"]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state - tombstone fields only
  const [formData, setFormData] = useState({
    title: "",
    classification: "",
    language: "en",
    department: "",
    reports_to: "",
  });

  // Load job metadata when modal opens or job changes
  useEffect(() => {
    if (isOpen && job) {
      setError(null);

      // Fetch metadata if not already loaded
      apiClient
        .getJob(job.id, {
          include_content: false,
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
          });
        })
        .catch((err) => {
          setError(
            err instanceof Error ? err.message : t("jobs:messages.loadFailed"),
          );
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
      setError(t("jobs:messages.titleClassificationRequired"));
      return;
    }

    setLoading(true);

    try {
      // Send all tombstone fields to the backend
      const updates: Record<string, string> = {
        title: formData.title,
        classification: formData.classification,
        language: formData.language,
        department: formData.department,
        reports_to: formData.reports_to,
      };

      await apiClient.updateJob(job.id, updates);

      onJobUpdated(job.id);
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t("jobs:messages.updateFailed"),
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
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="w-5 h-5" />
            {t("jobs:actions.editTombstone")}
          </DialogTitle>
          <DialogDescription>
            {job
              ? t("jobs:messages.editingTombstone", {
                  jobNumber: job.job_number,
                })
              : t("jobs:messages.loadingJob")}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="tomb-title">
              {t("jobs:fields.title")} <span className="text-red-500">*</span>
            </Label>
            <Input
              id="tomb-title"
              placeholder={t("jobs:placeholders.title")}
              value={formData.title}
              onChange={(e) => handleInputChange("title", e.target.value)}
              required
            />
          </div>

          {/* Classification */}
          <div className="space-y-2">
            <Label htmlFor="tomb-classification">
              {t("jobs:fields.classification")}{" "}
              <span className="text-red-500">*</span>
            </Label>
            <Input
              id="tomb-classification"
              placeholder={t("jobs:placeholders.classification")}
              value={formData.classification}
              onChange={(e) =>
                handleInputChange("classification", e.target.value)
              }
              required
            />
          </div>

          {/* Language */}
          <div className="space-y-2">
            <Label htmlFor="tomb-language">{t("jobs:fields.language")}</Label>
            <Select
              value={formData.language}
              onValueChange={(value) => handleInputChange("language", value)}
            >
              <SelectTrigger id="tomb-language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">
                  {t("jobs:languages.english")}
                </SelectItem>
                <SelectItem value="fr">{t("jobs:languages.french")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Department */}
          <div className="space-y-2">
            <Label htmlFor="tomb-department">
              {t("jobs:fields.department")}
            </Label>
            <Input
              id="tomb-department"
              placeholder={t("jobs:placeholders.department")}
              value={formData.department}
              onChange={(e) => handleInputChange("department", e.target.value)}
            />
          </div>

          {/* Reports To */}
          <div className="space-y-2">
            <Label htmlFor="tomb-reports-to">
              {t("jobs:fields.reportsTo")}
            </Label>
            <Input
              id="tomb-reports-to"
              placeholder={t("jobs:placeholders.reportsTo")}
              value={formData.reports_to}
              onChange={(e) => handleInputChange("reports_to", e.target.value)}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded flex items-start gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <DialogFooter className="pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
            >
              {t("common:actions.cancel")}
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t("common:actions.saving")}
                </>
              ) : (
                <>
                  <Edit className="w-4 h-4 mr-2" />
                  {t("common:actions.save")}
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
