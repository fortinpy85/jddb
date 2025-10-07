/**
 * DiffHighlighter Component
 *
 * Renders text with inline diff highlighting similar to Google Docs suggestion mode.
 * Shows additions, deletions, and modifications with color-coded visual cues.
 */

"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type {
  TextChange,
  ChangeType,
  ChangeCategory,
  ChangeSeverity,
} from "@/utils/diffAnalysis";
import {
  getChangeColorClass,
  getCategoryColorClass,
  getSeverityBadgeClass,
} from "@/utils/diffAnalysis";
import { AlertCircle, CheckCircle, Info } from "lucide-react";

export interface DiffHighlighterProps {
  originalText: string;
  changes: TextChange[];
  onChangeClick?: (change: TextChange) => void;
  selectedChangeId?: string | null;
  showCategories?: boolean;
  className?: string;
}

/**
 * Main DiffHighlighter Component
 */
export function DiffHighlighter({
  originalText,
  changes,
  onChangeClick,
  selectedChangeId,
  showCategories = true,
  className = "",
}: DiffHighlighterProps) {
  // Build segments from original text and changes
  const segments = buildTextSegments(originalText, changes);

  return (
    <div className={cn("prose prose-sm max-w-none", className)}>
      <div className="relative leading-relaxed">
        {segments.map((segment, index) => {
          if (segment.change) {
            return (
              <ChangeHighlight
                key={`${segment.change.id}-${index}`}
                change={segment.change}
                onClick={() => onChangeClick?.(segment.change!)}
                isSelected={selectedChangeId === segment.change.id}
                showCategory={showCategories}
              />
            );
          } else {
            return (
              <span
                key={`text-${index}`}
                className="text-gray-900 dark:text-gray-100"
              >
                {segment.text}
              </span>
            );
          }
        })}
      </div>
    </div>
  );
}

/**
 * Text segment type for rendering
 */
interface TextSegment {
  text: string;
  change?: TextChange;
}

/**
 * Build text segments from original text and changes
 */
function buildTextSegments(
  originalText: string,
  changes: TextChange[],
): TextSegment[] {
  const segments: TextSegment[] = [];
  let currentIndex = 0;

  // Sort changes by start index
  const sortedChanges = [...changes].sort(
    (a, b) => a.startIndex - b.startIndex,
  );

  sortedChanges.forEach((change) => {
    // Add unchanged text before this change
    if (currentIndex < change.startIndex) {
      segments.push({
        text: originalText.slice(currentIndex, change.startIndex),
      });
    }

    // Add the change
    segments.push({
      text:
        change.type === "deletion" ? change.originalText : change.suggestedText,
      change,
    });

    // Update current index
    currentIndex = change.endIndex;
  });

  // Add remaining unchanged text
  if (currentIndex < originalText.length) {
    segments.push({
      text: originalText.slice(currentIndex),
    });
  }

  return segments;
}

/**
 * Change Highlight Component
 */
interface ChangeHighlightProps {
  change: TextChange;
  onClick: () => void;
  isSelected: boolean;
  showCategory: boolean;
}

function ChangeHighlight({
  change,
  onClick,
  isSelected,
  showCategory,
}: ChangeHighlightProps) {
  const colorClass = getChangeColorClass(change.type);
  const categoryClass = showCategory
    ? getCategoryColorClass(change.category)
    : "";

  const content = (
    <span
      onClick={onClick}
      className={cn(
        "relative inline-block px-1 py-0.5 rounded cursor-pointer transition-all border-l-4",
        colorClass,
        categoryClass,
        isSelected && "ring-2 ring-blue-500 ring-offset-1",
        "hover:shadow-sm",
      )}
    >
      {change.type === "deletion" && (
        <span className="line-through">{change.originalText}</span>
      )}
      {change.type === "addition" && (
        <span className="underline decoration-2">{change.suggestedText}</span>
      )}
      {change.type === "modification" && (
        <>
          <span className="line-through text-red-600 mr-1">
            {change.originalText}
          </span>
          <span className="underline decoration-2 text-green-600">
            {change.suggestedText}
          </span>
        </>
      )}
    </span>
  );

  if (change.explanation || change.confidence !== undefined) {
    return (
      <TooltipProvider>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent>
          <ChangeTooltip change={change} />
        </TooltipContent>
      </TooltipProvider>
    );
  }

  return content;
}

/**
 * Change Tooltip Content
 */
function ChangeTooltip({ change }: { change: TextChange }) {
  return (
    <div className="max-w-xs space-y-2">
      {/* Category & Severity */}
      <div className="flex items-center gap-2">
        <Badge className={getCategoryBadgeClass(change.category)}>
          {change.category}
        </Badge>
        <Badge className={getSeverityBadgeClass(change.severity)}>
          {change.severity}
        </Badge>
      </div>

      {/* Explanation */}
      {change.explanation && (
        <p className="text-xs text-gray-700 dark:text-gray-300">
          {change.explanation}
        </p>
      )}

      {/* Confidence */}
      {change.confidence !== undefined && (
        <div className="flex items-center gap-1 text-xs text-gray-600">
          <Info className="h-3 w-3" />
          <span>{Math.round(change.confidence * 100)}% confidence</span>
        </div>
      )}

      {/* Change details */}
      <div className="text-xs space-y-1 pt-2 border-t border-gray-200 dark:border-gray-700">
        {change.type === "deletion" && (
          <div className="text-red-600">
            <strong>Remove:</strong> "{change.originalText}"
          </div>
        )}
        {change.type === "addition" && (
          <div className="text-green-600">
            <strong>Add:</strong> "{change.suggestedText}"
          </div>
        )}
        {change.type === "modification" && (
          <>
            <div className="text-red-600">
              <strong>From:</strong> "{change.originalText}"
            </div>
            <div className="text-green-600">
              <strong>To:</strong> "{change.suggestedText}"
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Get category badge class
 */
function getCategoryBadgeClass(category: ChangeCategory): string {
  switch (category) {
    case "grammar":
      return "bg-red-100 text-red-700";
    case "style":
      return "bg-blue-100 text-blue-700";
    case "clarity":
      return "bg-purple-100 text-purple-700";
    case "bias":
      return "bg-yellow-100 text-yellow-700";
    case "compliance":
      return "bg-green-100 text-green-700";
  }
}

/**
 * Compact Diff Summary Component
 */
export interface DiffSummaryProps {
  totalChanges: number;
  additionCount: number;
  deletionCount: number;
  modificationCount: number;
  className?: string;
}

export function DiffSummary({
  totalChanges,
  additionCount,
  deletionCount,
  modificationCount,
  className = "",
}: DiffSummaryProps) {
  if (totalChanges === 0) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 text-sm text-gray-600",
          className,
        )}
      >
        <CheckCircle className="h-4 w-4 text-green-600" />
        <span>No changes detected</span>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-3 text-sm", className)}>
      <AlertCircle className="h-4 w-4 text-blue-600" />
      <span className="text-gray-700 dark:text-gray-300">
        {totalChanges} {totalChanges === 1 ? "change" : "changes"}:
      </span>
      {additionCount > 0 && (
        <Badge className="bg-green-100 text-green-700 text-xs">
          +{additionCount}
        </Badge>
      )}
      {deletionCount > 0 && (
        <Badge className="bg-red-100 text-red-700 text-xs">
          -{deletionCount}
        </Badge>
      )}
      {modificationCount > 0 && (
        <Badge className="bg-yellow-100 text-yellow-700 text-xs">
          ~{modificationCount}
        </Badge>
      )}
    </div>
  );
}
