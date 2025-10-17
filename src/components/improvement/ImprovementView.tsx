/**
 * ImprovementView Component
 *
 * Smart Inline Diff Viewer with granular change control.
 * Main container for the improvement workflow with dual-pane diff highlighting.
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { DiffHighlighter, DiffSummary } from "./DiffHighlighter";
import { ChangeControls } from "./ChangeControls";
import { LiveSuggestionsPanel } from "./LiveSuggestionsPanel";
import { useImprovement } from "@/hooks/useImprovement";
import { useLiveImprovement } from "@/hooks/useLiveImprovement";
import { useAISuggestions } from "@/hooks/useAISuggestions";
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges";
import { LoadingState } from "@/components/ui/states";
import {
  ChevronLeft,
  Save,
  Sparkles,
  FileText,
  Eye,
  EyeOff,
  RefreshCw,
  Info,
  Download,
  Check,
  X,
} from "lucide-react";
import { WorkflowStepper } from "@/components/ui/workflow-stepper";
import { apiClient } from "@/lib/api";
import { logger } from "@/utils/logger";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";

export interface ImprovementViewProps {
  jobId?: number;
  initialOriginalText?: string;
  onBack?: () => void;
  onSave?: (finalText: string) => void;
  className?: string;
}

/**
 * Main ImprovementView Component
 */
function ImprovementView({
  jobId,
  initialOriginalText = "",
  onBack,
  onSave,
  className = "",
}: ImprovementViewProps) {
  // State
  const [originalText, setOriginalText] = useState(initialOriginalText);
  const [improvedText, setImprovedText] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [showOriginal, setShowOriginal] = useState(true);
  const [viewMode, setViewMode] = useState<"split" | "diff">("diff");
  const [rightPanelTab, setRightPanelTab] = useState<"changes" | "live">(
    "live",
  );

  // AI Suggestions hook
  const {
    suggestions,
    isLoading: aiLoading,
    fetchSuggestions,
  } = useAISuggestions();

  // Live Improvement hook with debounced analysis
  const liveImprovement = useLiveImprovement({
    debounceMs: 2000,
    minLength: 50,
    autoAnalyze: true,
    captureRLHF: true,
    onImprovedTextGenerated: (improved) => {
      setImprovedText(improved);
    },
    onAnalysisComplete: (_result) => {
      // Analysis complete
    },
  });

  // Improvement hook (for granular change control)
  const improvement = useImprovement({
    originalText,
    improvedText,
    aiSuggestions: suggestions,
    captureRLHF: true,
    onAcceptChange: (_change) => {
      // Change accepted
    },
    onRejectChange: (_change) => {
      // Change rejected
    },
    onApplyChanges: (_finalText, _acceptedChanges) => {
      // Changes applied
    },
  });

  // Unsaved changes protection
  const { confirmNavigation } = useUnsavedChanges({
    hasUnsavedChanges: improvement.hasPendingChanges || improvement.hasChanges,
    message:
      "You have unsaved improvements. Are you sure you want to leave? All pending changes will be lost.",
    enabled: true,
  });

  // Generate improved version
  const handleGenerateImprovement = async () => {
    setIsGenerating(true);
    try {
      const { enhanced_text } = await apiClient.enhanceContent({
        text: originalText,
        enhancement_types: [
          "grammar",
          "style",
          "clarity",
          "bias",
          "compliance",
        ],
      });
      setImprovedText(enhanced_text);
      setIsGenerating(false);
    } catch (error) {
      logger.error("Failed to generate improvement:", error);
      setIsGenerating(false);
    }
  };

  // Save final version
  const handleSave = async () => {
    const finalText = improvement.applyAcceptedChanges();
    if (jobId) {
      try {
        await apiClient.saveImprovedContent({
          job_id: jobId,
          improved_content: finalText,
        });
        onSave?.(finalText);
      } catch (error) {
        logger.error("Failed to save changes:", error);
      }
    }
  };

  // Sync original text with live improvement hook
  useEffect(() => {
    if (originalText) {
      liveImprovement.setOriginalText(originalText);
    }
  }, [originalText]);

  // Auto-generate on mount if we have original text
  useEffect(() => {
    if (originalText && !improvedText) {
      handleGenerateImprovement();
    }
  }, []);

  // Loading state
  if (isGenerating) {
    return (
      <LoadingState message="AI is analyzing and improving your job description..." />
    );
  }

  return (
    <div className={cn("h-full flex flex-col space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (confirmNavigation()) {
                onBack?.();
              }
            }}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Job Description Improvement
              </h2>
              {(improvement.hasPendingChanges || improvement.hasChanges) && (
                <Badge
                  variant="outline"
                  className="text-amber-600 border-amber-600"
                >
                  Unsaved Changes
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Review AI-suggested changes with inline diff highlighting
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setViewMode(viewMode === "split" ? "diff" : "split")}
          >
            {viewMode === "split" ? (
              <>
                <FileText className="w-4 h-4 mr-2" />
                Show Diff
              </>
            ) : (
              <>
                <Eye className="w-4 h-4 mr-2" />
                Show Split
              </>
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateImprovement}
            disabled={!originalText}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Regenerate
          </Button>

          <Button
            variant="default"
            size="sm"
            onClick={handleSave}
            disabled={!improvement.hasChanges || improvement.hasPendingChanges}
          >
            <Save className="w-4 h-4 mr-2" />
            Save Changes ({improvement.acceptedChangeIds.length})
          </Button>
        </div>
      </div>

      {/* Workflow Progress Indicator */}
      <div className="bg-card border rounded-lg p-4">
        <WorkflowStepper
          currentStep="improve"
          completedSteps={["upload", "review"]}
        />
      </div>

      {/* Summary Alert */}
      {improvement.hasChanges && (
        <Alert>
          <Sparkles className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <DiffSummary
                totalChanges={improvement.diffResult.totalChanges}
                additionCount={improvement.diffResult.additionCount}
                deletionCount={improvement.diffResult.deletionCount}
                modificationCount={improvement.diffResult.modificationCount}
              />
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <Info className="h-3 w-3" />
                Click on any highlighted change to review details
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">
        {/* Left/Center: Diff View */}
        <div className="lg:col-span-2 flex flex-col min-h-0">
          <Card className="flex-1 flex flex-col min-h-0">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-blue-600" />
                  <span>
                    {viewMode === "diff"
                      ? "Inline Diff View"
                      : "Side-by-Side Comparison"}
                  </span>
                </CardTitle>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">
                    {improvement.acceptedChangeIds.length} accepted
                  </Badge>
                  <Badge variant="outline">
                    {improvement.rejectedChangeIds.length} rejected
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full p-6">
                {viewMode === "diff" ? (
                  <DiffHighlighter
                    originalText={originalText}
                    changes={improvement.filteredChanges}
                    onChangeClick={(change) =>
                      improvement.selectChange(change.id)
                    }
                    selectedChangeId={improvement.selectedChangeId}
                    showCategories={true}
                  />
                ) : (
                  <SplitView
                    originalText={originalText}
                    improvedText={improvement.finalText}
                    changes={improvement.filteredChanges}
                    onAcceptChange={improvement.acceptChange}
                    onRejectChange={improvement.rejectChange}
                    acceptedChangeIds={improvement.acceptedChangeIds}
                    rejectedChangeIds={improvement.rejectedChangeIds}
                  />
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Right: Tabbed Panel (Live AI + Change Controls) */}
        <div className="flex flex-col min-h-0">
          <Tabs
            value={rightPanelTab}
            onValueChange={(value) =>
              setRightPanelTab(value as "changes" | "live")
            }
            className="flex-1 flex flex-col min-h-0"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="live" className="text-xs">
                <Sparkles className="w-3 h-3 mr-1" />
                Live AI
              </TabsTrigger>
              <TabsTrigger value="changes" className="text-xs">
                <FileText className="w-3 h-3 mr-1" />
                Changes
              </TabsTrigger>
            </TabsList>

            <TabsContent value="live" className="flex-1 min-h-0 mt-2">
              <LiveSuggestionsPanel
                suggestions={liveImprovement.suggestions}
                changes={liveImprovement.changes}
                currentSuggestion={liveImprovement.currentSuggestion}
                overallScore={liveImprovement.overallScore}
                isAnalyzing={liveImprovement.isAnalyzing}
                onAccept={liveImprovement.acceptSuggestion}
                onReject={liveImprovement.rejectSuggestion}
                onSuggestionClick={(suggestion) => {
                  liveImprovement.setCurrentSuggestion(suggestion);
                }}
                className="h-full"
              />
            </TabsContent>

            <TabsContent value="changes" className="flex-1 min-h-0 mt-2">
              <ChangeControls
                changes={improvement.filteredChanges}
                acceptedChangeIds={improvement.acceptedChangeIds}
                rejectedChangeIds={improvement.rejectedChangeIds}
                currentChangeIndex={improvement.currentChangeIndex}
                onAccept={improvement.acceptChange}
                onReject={improvement.rejectChange}
                onAcceptAll={improvement.acceptAll}
                onRejectAll={improvement.rejectAll}
                onNavigate={improvement.navigateChange}
                onFilterCategory={improvement.setSelectedCategory}
                selectedCategory={improvement.selectedCategory}
                finalText={improvement.finalText}
                className="flex-1"
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

// Wrap with error boundary for reliability
export function ImprovementViewWithErrorBoundary(props: ImprovementViewProps) {
  return (
    <ErrorBoundaryWrapper>
      <ImprovementView {...props} />
    </ErrorBoundaryWrapper>
  );
}

// Export wrapped version
export { ImprovementViewWithErrorBoundary as ImprovementView };

/**
 * Split View Component (Side-by-Side) - Enhanced with granular diff
 */
interface SplitViewProps {
  originalText: string;
  improvedText: string;
  changes?: any[];
  onAcceptChange?: (changeId: string) => void;
  onRejectChange?: (changeId: string) => void;
  acceptedChangeIds?: string[];
  rejectedChangeIds?: string[];
}

// Helper to map character index to line number
function getLineNumberFromIndex(text: string, charIndex: number): number {
  const textUpToIndex = text.substring(0, charIndex);
  return textUpToIndex.split("\n").length - 1;
}

// Helper to get changes for a specific line
function getChangesForLine(
  changes: any[],
  text: string,
  lineNumber: number,
): any[] {
  return changes.filter((change) => {
    const startLine = getLineNumberFromIndex(text, change.startIndex);
    const endLine = getLineNumberFromIndex(text, change.endIndex);
    return lineNumber >= startLine && lineNumber <= endLine;
  });
}

function SplitView({
  originalText,
  improvedText,
  changes = [],
  onAcceptChange,
  onRejectChange,
  acceptedChangeIds = [],
  rejectedChangeIds = [],
}: SplitViewProps) {
  const [focusedLineIndex, setFocusedLineIndex] = React.useState<number | null>(
    null,
  );

  // Split into lines for side-by-side comparison
  const originalLines = originalText.split("\n");
  const improvedLines = improvedText.split("\n");
  const maxLines = Math.max(originalLines.length, improvedLines.length);

  // Get line-level change information
  const getLineChanges = (lineNumber: number) => {
    const lineChanges = getChangesForLine(changes, originalText, lineNumber);
    const hasAddition = lineChanges.some((c) => c.type === "addition");
    const hasDeletion = lineChanges.some((c) => c.type === "deletion");
    const hasModification = lineChanges.some((c) => c.type === "modification");

    return { lineChanges, hasAddition, hasDeletion, hasModification };
  };

  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if split view is focused
      if (!focusedLineIndex && focusedLineIndex !== 0) return;

      const lineChanges = getLineChanges(focusedLineIndex);
      if (lineChanges.lineChanges.length === 0) return;

      const pendingChanges = lineChanges.lineChanges.filter(
        (c) =>
          !acceptedChangeIds.includes(c.id) &&
          !rejectedChangeIds.includes(c.id),
      );
      if (pendingChanges.length === 0) return;

      switch (e.key) {
        case "Enter":
        case "a":
        case "A":
          e.preventDefault();
          pendingChanges.forEach((c) => onAcceptChange?.(c.id));
          break;
        case "Delete":
        case "r":
        case "R":
          e.preventDefault();
          pendingChanges.forEach((c) => onRejectChange?.(c.id));
          break;
        case "ArrowDown":
        case "j":
          e.preventDefault();
          // Move to next change
          for (let i = focusedLineIndex + 1; i < maxLines; i++) {
            const nextLineChanges = getLineChanges(i);
            if (nextLineChanges.lineChanges.length > 0) {
              setFocusedLineIndex(i);
              break;
            }
          }
          break;
        case "ArrowUp":
        case "k":
          e.preventDefault();
          // Move to previous change
          for (let i = focusedLineIndex - 1; i >= 0; i--) {
            const prevLineChanges = getLineChanges(i);
            if (prevLineChanges.lineChanges.length > 0) {
              setFocusedLineIndex(i);
              break;
            }
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    focusedLineIndex,
    changes,
    acceptedChangeIds,
    rejectedChangeIds,
    maxLines,
  ]);

  return (
    <div className="grid grid-cols-2 gap-2 divide-x divide-gray-200">
      {/* Left Column - Original */}
      <div className="space-y-1 pr-2">
        <div className="sticky top-0 bg-white dark:bg-gray-900 pb-2 border-b border-gray-200 mb-2">
          <div className="flex items-center space-x-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            <FileText className="w-4 h-4 text-red-600" />
            <span>Original</span>
          </div>
        </div>
        {originalLines.map((line, index) => {
          const { lineChanges, hasAddition, hasDeletion, hasModification } =
            getLineChanges(index);
          const hasChange = lineChanges.length > 0;
          const isAccepted = lineChanges.some((c) =>
            acceptedChangeIds.includes(c.id),
          );
          const isRejected = lineChanges.some((c) =>
            rejectedChangeIds.includes(c.id),
          );
          const isFocused = focusedLineIndex === index;

          // Determine background color based on change type
          let bgClass = "hover:bg-gray-50 dark:hover:bg-gray-800/50";
          if (isFocused) {
            bgClass = "bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-500";
          } else if (isAccepted) {
            bgClass =
              "bg-green-50 dark:bg-green-900/20 border-l-2 border-green-500";
          } else if (isRejected) {
            bgClass = "bg-red-50 dark:bg-red-900/20 border-l-2 border-red-500";
          } else if (hasDeletion) {
            bgClass =
              "bg-red-50/50 dark:bg-red-900/10 hover:bg-red-100 dark:hover:bg-red-900/20";
          } else if (hasModification) {
            bgClass =
              "bg-yellow-50/50 dark:bg-yellow-900/10 hover:bg-yellow-100 dark:hover:bg-yellow-900/20";
          }

          return (
            <div
              key={`orig-${index}`}
              className={cn(
                "flex items-start gap-2 px-3 py-1.5 rounded transition-colors group",
                bgClass,
                hasChange && "cursor-pointer",
              )}
              onClick={() => hasChange && setFocusedLineIndex(index)}
              tabIndex={hasChange ? 0 : -1}
            >
              <span className="text-xs text-gray-400 select-none w-8 flex-shrink-0 text-right">
                {index + 1}
              </span>
              <span className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed flex-1">
                {line || "\u00A0"}
              </span>
              {/* Inline controls for changes */}
              {hasChange && !isAccepted && !isRejected && (
                <div
                  className={cn(
                    "flex items-center gap-1 transition-opacity",
                    isFocused
                      ? "opacity-100"
                      : "opacity-0 group-hover:opacity-100",
                  )}
                >
                  {lineChanges.map((change) => (
                    <React.Fragment key={change.id}>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 text-xs text-green-600 hover:bg-green-100 dark:hover:bg-green-900/30"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAcceptChange?.(change.id);
                        }}
                      >
                        <Check className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 text-xs text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRejectChange?.(change.id);
                        }}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </React.Fragment>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Right Column - Improved */}
      <div className="space-y-1 pl-2">
        <div className="sticky top-0 bg-white dark:bg-gray-900 pb-2 border-b border-gray-200 mb-2">
          <div className="flex items-center space-x-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            <Sparkles className="w-4 h-4 text-green-600" />
            <span>Improved</span>
          </div>
        </div>
        {improvedLines.map((line, index) => {
          const { lineChanges, hasAddition, hasDeletion, hasModification } =
            getLineChanges(index);
          const hasChange = lineChanges.length > 0;
          const isAccepted = lineChanges.some((c) =>
            acceptedChangeIds.includes(c.id),
          );
          const isRejected = lineChanges.some((c) =>
            rejectedChangeIds.includes(c.id),
          );

          // Determine background color based on change type
          let bgClass = "hover:bg-gray-50 dark:hover:bg-gray-800/50";
          if (isAccepted) {
            bgClass =
              "bg-green-50 dark:bg-green-900/20 border-l-2 border-green-500";
          } else if (isRejected) {
            bgClass = "bg-red-50 dark:bg-red-900/20 border-l-2 border-red-500";
          } else if (hasAddition) {
            bgClass =
              "bg-green-50/50 dark:bg-green-900/10 hover:bg-green-100 dark:hover:bg-green-900/20";
          } else if (hasModification) {
            bgClass =
              "bg-yellow-50/50 dark:bg-yellow-900/10 hover:bg-yellow-100 dark:hover:bg-yellow-900/20";
          }

          return (
            <div
              key={`imp-${index}`}
              className={cn(
                "flex items-start gap-2 px-3 py-1.5 rounded transition-colors",
                bgClass,
              )}
            >
              <span className="text-xs text-gray-400 select-none w-8 flex-shrink-0 text-right">
                {index + 1}
              </span>
              <span className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed flex-1">
                {line || "\u00A0"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
