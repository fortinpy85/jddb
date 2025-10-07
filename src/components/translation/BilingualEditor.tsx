/**
 * Bilingual Editor Component
 *
 * Provides concurrent bilingual editing with:
 * - Side-by-side English/French editing
 * - Segment-level translation alignment
 * - Translation status tracking (draft, review, approved)
 * - Translation completeness indicators
 * - Synchronized scrolling and navigation
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Languages,
  CheckCircle,
  AlertCircle,
  Clock,
  Link2,
  Unlink,
  Save,
  Eye,
  Split,
  ArrowLeftRight,
  Sparkles,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import { BiasDetector } from "@/components/ai/BiasDetector";
import { useAISuggestions } from "@/hooks/useAISuggestions";

export type TranslationStatus = "draft" | "review" | "approved";

export interface BilingualSegment {
  id: string;
  english: string;
  french: string;
  status: TranslationStatus;
  lastModified: Date;
  modifiedBy?: string;
}

export interface BilingualDocument {
  id: string;
  job_id: number;
  title: string;
  segments: BilingualSegment[];
  metadata: {
    created: Date;
    modified: Date;
    englishCompleteness: number; // 0-100%
    frenchCompleteness: number; // 0-100%
    overallStatus: TranslationStatus;
  };
}

interface BilingualEditorProps {
  document?: BilingualDocument;
  jobId?: number;
  sourceLanguage?: string;
  targetLanguage?: string;
  onBack?: () => void;
  onSave?: (document: BilingualDocument) => void;
  onSegmentChange?: (
    segmentId: string,
    language: "en" | "fr",
    content: string,
  ) => void;
  onStatusChange?: (segmentId: string, status: TranslationStatus) => void;
  readOnly?: boolean;
  className?: string;
}

export const BilingualEditor: React.FC<BilingualEditorProps> = ({
  document: initialDocument,
  jobId,
  sourceLanguage,
  targetLanguage,
  onBack,
  onSave,
  onSegmentChange,
  onStatusChange,
  readOnly = false,
  className,
}) => {
  const [document, setDocument] = useState<BilingualDocument | null>(
    initialDocument || null,
  );
  const [loading, setLoading] = useState(!initialDocument && !!jobId);
  const [error, setError] = useState<string | null>(null);
  const [activeSegment, setActiveSegment] = useState<string | null>(null);
  const [linkedScrolling, setLinkedScrolling] = useState(true);
  const [viewMode, setViewMode] = useState<"split" | "tabs">("split");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showBiasAnalysis, setShowBiasAnalysis] = useState(false);
  const [analyzingSegment, setAnalyzingSegment] = useState<string | null>(null);
  const {
    biasAnalysis,
    analyzeBias,
    isLoading: biasLoading,
  } = useAISuggestions();

  const englishScrollRef = useRef<HTMLDivElement>(null);
  const frenchScrollRef = useRef<HTMLDivElement>(null);

  // Fetch document if jobId is provided
  useEffect(() => {
    if (!initialDocument && jobId) {
      fetchBilingualDocument(jobId);
    }
  }, [jobId, initialDocument]);

  const fetchBilingualDocument = async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      // Use window.location to construct API URL for browser environment
      const apiBaseUrl =
        typeof window !== "undefined"
          ? `${window.location.protocol}//${window.location.hostname}:8000/api`
          : "http://localhost:8000/api";
      const response = await fetch(`${apiBaseUrl}/bilingual-documents/${id}`);

      if (!response.ok) {
        throw new Error(
          `Failed to fetch bilingual document: ${response.statusText}`,
        );
      }

      const data = await response.json();

      if (data.success && data.document) {
        const doc: BilingualDocument = {
          id: data.document.id || `doc-${id}`,
          job_id: id,
          title: data.document.title || `Job ${id}`,
          segments: data.document.segments.map((seg: any, index: number) => ({
            id: seg.id || `segment-${index}`,
            english: seg.english || "",
            french: seg.french || "",
            status: seg.status || "draft",
            lastModified: seg.lastModified
              ? new Date(seg.lastModified)
              : new Date(),
            modifiedBy: seg.modifiedBy,
          })) as BilingualSegment[],
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
      console.error("Error fetching bilingual document:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load bilingual document",
      );
    } finally {
      setLoading(false);
    }
  };

  // Update document when prop changes
  useEffect(() => {
    if (initialDocument) {
      setDocument(initialDocument);
    }
  }, [initialDocument]);

  // Calculate completeness for each language
  const calculateCompleteness = (language: "en" | "fr"): number => {
    if (!document) return 0;
    const segments = document.segments;
    if (segments.length === 0) return 0;

    const filledSegments = segments.filter((seg) => {
      const content = language === "en" ? seg.english : seg.french;
      return content.trim().length > 0;
    });

    return Math.round((filledSegments.length / segments.length) * 100);
  };

  // Handle segment content change
  const handleSegmentChange = (
    segmentId: string,
    language: "en" | "fr",
    content: string,
  ) => {
    setDocument((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        segments: prev.segments.map((seg) =>
          seg.id === segmentId
            ? {
                ...seg,
                [language === "en" ? "english" : "french"]: content,
                lastModified: new Date(),
              }
            : seg,
        ),
        metadata: {
          ...prev.metadata,
          modified: new Date(),
          englishCompleteness: calculateCompleteness("en"),
          frenchCompleteness: calculateCompleteness("fr"),
        },
      };
    });

    setHasUnsavedChanges(true);

    if (onSegmentChange) {
      onSegmentChange(segmentId, language, content);
    }
  };

  // Handle status change
  const handleStatusChange = (segmentId: string, status: TranslationStatus) => {
    setDocument((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        segments: prev.segments.map((seg) =>
          seg.id === segmentId
            ? {
                ...seg,
                status,
                lastModified: new Date(),
              }
            : seg,
        ),
      };
    });

    setHasUnsavedChanges(true);

    if (onStatusChange) {
      onStatusChange(segmentId, status);
    }
  };

  // Handle save
  const handleSave = () => {
    if (onSave && document) {
      onSave(document);
      setHasUnsavedChanges(false);
    }
  };

  // Handle bias analysis for a segment
  const handleAnalyzeBias = async (
    segmentId: string,
    language: "en" | "fr",
  ) => {
    if (!document) return;
    const segment = document.segments.find((seg) => seg.id === segmentId);
    if (!segment) return;

    const content = language === "en" ? segment.english : segment.french;
    setAnalyzingSegment(segmentId);
    await analyzeBias(content, true);
  };

  // Synchronized scrolling
  const handleScroll = (
    source: "en" | "fr",
    event: React.UIEvent<HTMLDivElement>,
  ) => {
    if (!linkedScrolling) return;

    const sourceElement = event.currentTarget;
    const targetElement =
      source === "en" ? frenchScrollRef.current : englishScrollRef.current;

    if (targetElement) {
      const scrollPercentage =
        sourceElement.scrollTop /
        (sourceElement.scrollHeight - sourceElement.clientHeight);

      targetElement.scrollTop =
        scrollPercentage *
        (targetElement.scrollHeight - targetElement.clientHeight);
    }
  };

  // Get status badge color
  const getStatusColor = (status: TranslationStatus): string => {
    switch (status) {
      case "draft":
        return "bg-yellow-100 text-yellow-800";
      case "review":
        return "bg-blue-100 text-blue-800";
      case "approved":
        return "bg-green-100 text-green-800";
    }
  };

  // Get status icon
  const getStatusIcon = (status: TranslationStatus) => {
    switch (status) {
      case "draft":
        return <Clock className="w-3 h-3" />;
      case "review":
        return <Eye className="w-3 h-3" />;
      case "approved":
        return <CheckCircle className="w-3 h-3" />;
    }
  };

  // Render segment editor
  const renderSegmentEditor = (
    segment: BilingualSegment,
    language: "en" | "fr",
  ) => {
    const content = language === "en" ? segment.english : segment.french;
    const isActive = activeSegment === segment.id;

    return (
      <div
        key={`${segment.id}-${language}`}
        className={`mb-4 p-3 border rounded-lg ${
          isActive ? "border-blue-500 bg-blue-50" : "border-gray-200"
        }`}
        onClick={() => setActiveSegment(segment.id)}
      >
        {/* Segment Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              Segment {segment.id}
            </Badge>
            <Badge className={`text-xs ${getStatusColor(segment.status)}`}>
              {getStatusIcon(segment.status)}
              <span className="ml-1">{segment.status}</span>
            </Badge>
          </div>

          {isActive && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAnalyzeBias(segment.id, language)}
                disabled={readOnly || biasLoading}
                className="h-7 text-xs"
              >
                <Sparkles className="w-3 h-3 mr-1" />
                {biasLoading && analyzingSegment === segment.id
                  ? "Analyzing..."
                  : "Check Bias"}
              </Button>
              <Select
                value={segment.status}
                onValueChange={(value) =>
                  handleStatusChange(segment.id, value as TranslationStatus)
                }
                disabled={readOnly}
              >
                <SelectTrigger className="h-7 w-[120px] text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="review">Review</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Segment Content */}
        <Textarea
          value={content}
          onChange={(e) =>
            handleSegmentChange(segment.id, language, e.target.value)
          }
          disabled={readOnly}
          className="min-h-[100px] text-sm"
          placeholder={`Enter ${language === "en" ? "English" : "French"} content...`}
        />

        {/* Segment Footer */}
        {isActive && segment.lastModified && (
          <div className="mt-2 text-xs text-gray-500">
            Last modified: {segment.lastModified.toLocaleString()}
            {segment.modifiedBy && ` by ${segment.modifiedBy}`}
          </div>
        )}

        {/* Bias Analysis Results */}
        {isActive && analyzingSegment === segment.id && biasAnalysis && (
          <div className="mt-3">
            <BiasDetector
              text={content}
              biasAnalysis={biasAnalysis}
              onReplace={(original, replacement) => {
                handleSegmentChange(
                  segment.id,
                  language,
                  content.replace(original, replacement),
                );
              }}
              compact
            />
          </div>
        )}
      </div>
    );
  };

  // Split view layout
  const renderSplitView = () => {
    if (!document) return null;
    return (
      <div className="grid grid-cols-2 gap-4">
        {/* English Column */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium flex items-center gap-2">
              <Languages className="w-4 h-4" />
              English
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600">
                {calculateCompleteness("en")}% complete
              </span>
              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${calculateCompleteness("en")}%` }}
                />
              </div>
            </div>
          </div>

          <ScrollArea
            className="h-[600px] pr-4"
            ref={englishScrollRef}
            onScroll={(e) => handleScroll("en", e)}
          >
            {document.segments.map((segment) =>
              renderSegmentEditor(segment, "en"),
            )}
          </ScrollArea>
        </div>

        {/* French Column */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium flex items-center gap-2">
              <Languages className="w-4 h-4" />
              Français
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600">
                {calculateCompleteness("fr")}% complete
              </span>
              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${calculateCompleteness("fr")}%` }}
                />
              </div>
            </div>
          </div>

          <ScrollArea
            className="h-[600px] pr-4"
            ref={frenchScrollRef}
            onScroll={(e) => handleScroll("fr", e)}
          >
            {document.segments.map((segment) =>
              renderSegmentEditor(segment, "fr"),
            )}
          </ScrollArea>
        </div>
      </div>
    );
  };

  // Tabbed view layout
  const renderTabbedView = () => {
    if (!document) return null;
    return (
      <Tabs defaultValue="en" className="w-full">
        <TabsList>
          <TabsTrigger value="en" className="flex items-center gap-2">
            <Languages className="w-4 h-4" />
            English ({calculateCompleteness("en")}%)
          </TabsTrigger>
          <TabsTrigger value="fr" className="flex items-center gap-2">
            <Languages className="w-4 h-4" />
            Français ({calculateCompleteness("fr")}%)
          </TabsTrigger>
        </TabsList>

        <TabsContent value="en">
          <ScrollArea className="h-[600px] pr-4">
            {document.segments.map((segment) =>
              renderSegmentEditor(segment, "en"),
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="fr">
          <ScrollArea className="h-[600px] pr-4">
            {document.segments.map((segment) =>
              renderSegmentEditor(segment, "fr"),
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    );
  };

  // Handle loading state
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {onBack && (
              <Button variant="ghost" size="sm" onClick={onBack}>
                <ArrowLeft className="w-4 h-4" />
              </Button>
            )}
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

  // Handle error state
  if (error || !document) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {onBack && (
              <Button variant="ghost" size="sm" onClick={onBack}>
                <ArrowLeft className="w-4 h-4" />
              </Button>
            )}
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
              {onBack && (
                <Button variant="outline" onClick={onBack}>
                  Go Back
                </Button>
              )}
              {jobId && (
                <Button onClick={() => fetchBilingualDocument(jobId)}>
                  Retry
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Languages className="w-4 h-4" />
            Bilingual Editor
            {hasUnsavedChanges && (
              <Badge variant="outline" className="ml-2">
                <AlertCircle className="w-3 h-3 mr-1" />
                Unsaved
              </Badge>
            )}
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setViewMode(viewMode === "split" ? "tabs" : "split")
              }
            >
              {viewMode === "split" ? (
                <>
                  <ArrowLeftRight className="w-3 h-3 mr-1" />
                  Tabs
                </>
              ) : (
                <>
                  <Split className="w-3 h-3 mr-1" />
                  Split
                </>
              )}
            </Button>

            {/* Linked Scrolling Toggle */}
            {viewMode === "split" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setLinkedScrolling(!linkedScrolling)}
              >
                {linkedScrolling ? (
                  <>
                    <Link2 className="w-3 h-3 mr-1" />
                    Linked
                  </>
                ) : (
                  <>
                    <Unlink className="w-3 h-3 mr-1" />
                    Independent
                  </>
                )}
              </Button>
            )}

            {/* Save Button */}
            {!readOnly && (
              <Button
                size="sm"
                onClick={handleSave}
                disabled={!hasUnsavedChanges}
              >
                <Save className="w-3 h-3 mr-1" />
                Save
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {viewMode === "split" ? renderSplitView() : renderTabbedView()}
      </CardContent>
    </Card>
  );
};
