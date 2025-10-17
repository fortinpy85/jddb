/**
 * Bilingual Editor Wrapper
 * Fetches bilingual document data and renders BilingualEditor component
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  BilingualEditor,
  BilingualDocument,
  BilingualSegment,
} from "./BilingualEditor";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, AlertCircle, Loader2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { logger } from "@/utils/logger";

interface BilingualEditorWrapperProps {
  jobId: number;
  sourceLanguage: string;
  targetLanguage: string;
  onBack: () => void;
}

const BilingualEditorWrapper: React.FC<BilingualEditorWrapperProps> = ({
  jobId,
  sourceLanguage,
  targetLanguage,
  onBack,
}) => {
  const [document, setDocument] = useState<BilingualDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBilingualDocument();
  }, [jobId]);

  const fetchBilingualDocument = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/bilingual-documents/${jobId}`,
      );

      if (!response.ok) {
        throw new Error(
          `Failed to fetch bilingual document: ${response.statusText}`,
        );
      }

      const data = await response.json();

      if (data.success && data.document) {
        // Transform API response to BilingualDocument format
        const doc: BilingualDocument = {
          id: data.document.id || `doc-${jobId}`,
          job_id: jobId,
          title: data.document.title || `Job ${jobId}`,
          segments: Array.isArray(data.document.segments)
            ? data.document.segments.map((seg: any, index: number) => ({
                id: seg.id || `segment-${index}`,
                english: seg.english || "",
                french: seg.french || "",
                status: seg.status || "draft",
                lastModified: seg.lastModified
                  ? new Date(seg.lastModified)
                  : new Date(),
                modifiedBy: seg.modifiedBy,
              }))
            : [],
          metadata: {
            created: data.document.metadata?.created
              ? new Date(data.document.metadata.created)
              : new Date(),
            modified: data.document.metadata?.modified
              ? new Date(data.document.metadata.modified)
              : new Date(),
            englishCompleteness:
              data.document.metadata?.englishCompleteness || 0,
            frenchCompleteness: data.document.metadata?.frenchCompleteness || 0,
            overallStatus: data.document.metadata?.overallStatus || "draft",
          },
        };

        setDocument(doc);
      } else {
        throw new Error("Invalid response format from server");
      }
    } catch (err) {
      logger.error("Error fetching bilingual document:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load bilingual document",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (updatedDocument: BilingualDocument) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/bilingual-documents/${jobId}/save`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            segments: updatedDocument.segments.map((seg) => ({
              id: seg.id,
              english: seg.english,
              french: seg.french,
              status: seg.status,
            })),
          }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to save bilingual document");
      }

      const data = await response.json();

      if (data.success) {
        // Optionally show success notification
        logger.info("Document saved successfully");
      }
    } catch (err) {
      logger.error("Error saving bilingual document:", err);
      // Optionally show error notification
      alert("Failed to save changes. Please try again.");
    }
  };

  const handleSegmentChange = async (
    segmentId: string,
    language: "en" | "fr",
    content: string,
  ) => {
    try {
      await fetch(
        `${API_BASE_URL}/bilingual-documents/${jobId}/segments/${segmentId}?language=${language}&content=${encodeURIComponent(content)}`,
        {
          method: "PUT",
        },
      );
    } catch (err) {
      logger.error("Error updating segment:", err);
    }
  };

  const handleStatusChange = async (segmentId: string, status: string) => {
    try {
      await fetch(
        `${API_BASE_URL}/bilingual-documents/${jobId}/segments/${segmentId}/status`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            segment_id: segmentId,
            status,
          }),
        },
      );
    } catch (err) {
      logger.error("Error updating segment status:", err);
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            Loading Bilingual Editor...
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <p className="text-sm text-muted-foreground">
              Loading translation editor for Job {jobId}...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !document) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            Error Loading Editor
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <AlertCircle className="w-12 h-12 text-red-600" />
            <div className="text-center">
              <p className="text-sm font-medium text-red-600">
                {error || "Failed to load bilingual document"}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Please try again or select a different job.
              </p>
            </div>
            <div className="flex gap-2 mt-4">
              <Button variant="outline" onClick={onBack}>
                Go Back
              </Button>
              <Button onClick={fetchBilingualDocument}>Retry</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Back Button */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Job Details
        </Button>
      </div>

      {/* Bilingual Editor */}
      <BilingualEditor
        document={document}
        onSave={handleSave}
        onSegmentChange={handleSegmentChange}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
};

export default BilingualEditorWrapper;
