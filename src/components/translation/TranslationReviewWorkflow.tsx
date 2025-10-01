/**
 * TranslationReviewWorkflow Component
 *
 * Comprehensive review workflow for bilingual job descriptions.
 * Combines bilingual editing, quality assessment, and approval workflow.
 */

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  Save,
  Send,
  RefreshCw,
  FileText,
  BarChart3,
  BookOpen,
} from "lucide-react";
import { BilingualEditor, BilingualDocument } from "./BilingualEditor";
import { QualityIndicator, QualityAssessment } from "./QualityIndicator";

export interface TranslationReviewWorkflowProps {
  document: BilingualDocument;
  onSave?: (document: BilingualDocument) => void;
  onSubmit?: (document: BilingualDocument) => void;
  onApprove?: (document: BilingualDocument) => void;
  readOnly?: boolean;
}

type WorkflowStage = "editing" | "review" | "approved";

/**
 * Get stage status based on document state
 */
const getStageStatus = (
  document: BilingualDocument
): {
  stage: WorkflowStage;
  label: string;
  color: string;
  icon: React.ReactNode;
} => {
  const draftCount = document.segments.filter((s) => s.status === "draft").length;
  const reviewCount = document.segments.filter((s) => s.status === "review").length;
  const approvedCount = document.segments.filter(
    (s) => s.status === "approved"
  ).length;
  const totalCount = document.segments.length;

  if (approvedCount === totalCount) {
    return {
      stage: "approved",
      label: "Approved",
      color: "bg-green-500",
      icon: <CheckCircle2 className="h-4 w-4" />,
    };
  } else if (reviewCount > 0 || (draftCount === 0 && approvedCount > 0)) {
    return {
      stage: "review",
      label: "In Review",
      color: "bg-blue-500",
      icon: <AlertCircle className="h-4 w-4" />,
    };
  } else {
    return {
      stage: "editing",
      label: "Editing",
      color: "bg-yellow-500",
      icon: <Clock className="h-4 w-4" />,
    };
  }
};

/**
 * TranslationReviewWorkflow Component
 */
export const TranslationReviewWorkflow: React.FC<
  TranslationReviewWorkflowProps
> = ({ document: initialDocument, onSave, onSubmit, onApprove, readOnly = false }) => {
  const [document, setDocument] = useState<BilingualDocument>(initialDocument);
  const [activeTab, setActiveTab] = useState<string>("editor");
  const [qualityAssessment, setQualityAssessment] =
    useState<QualityAssessment | null>(null);
  const [loadingQuality, setLoadingQuality] = useState(false);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const stageStatus = getStageStatus(document);

  // Update document when initialDocument changes
  useEffect(() => {
    setDocument(initialDocument);
  }, [initialDocument]);

  /**
   * Assess overall document quality
   */
  const assessDocumentQuality = async () => {
    setLoadingQuality(true);
    try {
      // Combine all segments for overall assessment
      const englishText = document.segments.map((s) => s.english).join("\n\n");
      const frenchText = document.segments.map((s) => s.french).join("\n\n");

      const response = await fetch(
        "http://localhost:8000/api/translation-quality/assess",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            english_text: englishText,
            french_text: frenchText,
            context: { job_id: document.job_id },
          }),
        }
      );

      const data = await response.json();
      if (data.success) {
        setQualityAssessment(data.assessment);
      }
    } catch (error) {
      console.error("Error assessing quality:", error);
    } finally {
      setLoadingQuality(false);
    }
  };

  /**
   * Check document consistency
   */
  const checkConsistency = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/translation-quality/consistency",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            segments: document.segments.map((s) => ({
              id: s.id,
              english: s.english,
              french: s.french,
            })),
          }),
        }
      );

      const data = await response.json();
      if (data.success && data.consistency.issues.length > 0) {
        alert(
          `Found ${data.consistency.issues.length} consistency issues. Check the Quality tab for details.`
        );
      }
    } catch (error) {
      console.error("Error checking consistency:", error);
    }
  };

  /**
   * Handle save
   */
  const handleSave = () => {
    if (onSave) {
      onSave(document);
      setHasUnsavedChanges(false);
    }
  };

  /**
   * Handle submit for review
   */
  const handleSubmitForReview = () => {
    // Check if all segments are translated
    const missingTranslations = document.segments.filter(
      (s) => !s.french.trim()
    );
    if (missingTranslations.length > 0) {
      alert(
        `${missingTranslations.length} segment(s) are missing translations. Please complete all translations before submitting.`
      );
      return;
    }

    setShowSubmitDialog(true);
  };

  /**
   * Confirm submit for review
   */
  const confirmSubmit = () => {
    // Update all draft segments to review
    const updatedDocument = {
      ...document,
      segments: document.segments.map((s) =>
        s.status === "draft" ? { ...s, status: "review" as const } : s
      ),
    };

    setDocument(updatedDocument);
    setShowSubmitDialog(false);
    setHasUnsavedChanges(true);

    if (onSubmit) {
      onSubmit(updatedDocument);
    }
  };

  /**
   * Handle approve
   */
  const handleApprove = () => {
    // Check quality score
    if (qualityAssessment && qualityAssessment.overall_score < 70) {
      alert(
        "Quality score is below 70%. Please address quality issues before approving."
      );
      return;
    }

    setShowApproveDialog(true);
  };

  /**
   * Confirm approve
   */
  const confirmApprove = () => {
    // Update all segments to approved
    const updatedDocument = {
      ...document,
      segments: document.segments.map((s) => ({
        ...s,
        status: "approved" as const,
      })),
    };

    setDocument(updatedDocument);
    setShowApproveDialog(false);
    setHasUnsavedChanges(true);

    if (onApprove) {
      onApprove(updatedDocument);
    }
  };

  /**
   * Calculate review statistics
   */
  const stats = {
    total: document.segments.length,
    draft: document.segments.filter((s) => s.status === "draft").length,
    review: document.segments.filter((s) => s.status === "review").length,
    approved: document.segments.filter((s) => s.status === "approved").length,
    completeness: Math.round(
      (document.segments.filter((s) => s.french.trim()).length /
        document.segments.length) *
        100
    ),
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Translation Review Workflow</CardTitle>
              <CardDescription>
                Job ID: {document.job_id} - {document.title}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={stageStatus.color}>
                {stageStatus.icon}
                <span className="ml-2">{stageStatus.label}</span>
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Statistics */}
          <div className="grid grid-cols-5 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-muted-foreground">Total Segments</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">{stats.draft}</div>
              <div className="text-xs text-muted-foreground">Draft</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">{stats.review}</div>
              <div className="text-xs text-muted-foreground">In Review</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {stats.approved}
              </div>
              <div className="text-xs text-muted-foreground">Approved</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.completeness}%</div>
              <div className="text-xs text-muted-foreground">Complete</div>
            </div>
          </div>

          <Separator className="my-4" />

          {/* Actions */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={assessDocumentQuality}
                disabled={loadingQuality}
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                {loadingQuality ? "Assessing..." : "Assess Quality"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={checkConsistency}
              >
                <BookOpen className="h-4 w-4 mr-2" />
                Check Consistency
              </Button>
            </div>

            <div className="flex gap-2">
              {hasUnsavedChanges && (
                <Button variant="outline" size="sm" onClick={handleSave}>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
              )}

              {stageStatus.stage === "editing" && (
                <Button size="sm" onClick={handleSubmitForReview}>
                  <Send className="h-4 w-4 mr-2" />
                  Submit for Review
                </Button>
              )}

              {stageStatus.stage === "review" && (
                <Button size="sm" onClick={handleApprove}>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="editor">
            <FileText className="h-4 w-4 mr-2" />
            Editor
          </TabsTrigger>
          <TabsTrigger value="quality">
            <BarChart3 className="h-4 w-4 mr-2" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="history">
            <Clock className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Editor Tab */}
        <TabsContent value="editor">
          <BilingualEditor
            document={document}
            onSave={handleSave}
            onSegmentChange={(segmentId, updates) => {
              const updatedDocument = {
                ...document,
                segments: document.segments.map((s) =>
                  s.id === segmentId ? { ...s, ...updates } : s
                ),
              };
              setDocument(updatedDocument);
              setHasUnsavedChanges(true);
            }}
            onStatusChange={(segmentId, status) => {
              const updatedDocument = {
                ...document,
                segments: document.segments.map((s) =>
                  s.id === segmentId ? { ...s, status } : s
                ),
              };
              setDocument(updatedDocument);
              setHasUnsavedChanges(true);
            }}
            readOnly={readOnly || stageStatus.stage === "approved"}
          />
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality">
          <QualityIndicator
            assessment={qualityAssessment}
            loading={loadingQuality}
            onRefresh={assessDocumentQuality}
          />
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Translation History</CardTitle>
              <CardDescription>
                Review history and change tracking
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  {document.segments.map((segment) => (
                    <div key={segment.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">Segment {segment.id}</span>
                        <Badge
                          variant={
                            segment.status === "approved"
                              ? "default"
                              : segment.status === "review"
                                ? "secondary"
                                : "outline"
                          }
                        >
                          {segment.status}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Last modified:{" "}
                        {new Date(segment.lastModified).toLocaleString()}
                      </div>
                      {segment.modifiedBy && (
                        <div className="text-sm text-muted-foreground">
                          By: {segment.modifiedBy}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Submit Dialog */}
      <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit for Review</DialogTitle>
            <DialogDescription>
              Are you sure you want to submit this document for review?
            </DialogDescription>
          </DialogHeader>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Review Checklist</AlertTitle>
            <AlertDescription>
              <ul className="mt-2 space-y-1 list-disc list-inside text-sm">
                <li>All segments have been translated</li>
                <li>Terminology is consistent</li>
                <li>Formatting matches source document</li>
                <li>Quality assessment has been performed</li>
              </ul>
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowSubmitDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={confirmSubmit}>
              <Send className="h-4 w-4 mr-2" />
              Submit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Approve Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Translation</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve this translation?
            </DialogDescription>
          </DialogHeader>
          <Alert>
            <CheckCircle2 className="h-4 w-4" />
            <AlertTitle>Approval Checklist</AlertTitle>
            <AlertDescription>
              <ul className="mt-2 space-y-1 list-disc list-inside text-sm">
                <li>Quality score is 70% or higher</li>
                <li>All issues have been addressed</li>
                <li>Terminology is consistent across document</li>
                <li>Final review has been completed</li>
              </ul>
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApproveDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={confirmApprove}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};