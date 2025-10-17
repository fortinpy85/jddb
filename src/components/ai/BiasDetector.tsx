/**
 * Bias Detector Widget
 * Phase 3: Advanced AI Content Intelligence
 *
 * Inline bias highlighting and correction suggestions
 */

import React, { useState, useMemo } from "react";
import type { BiasIssue, BiasAnalysisResponse } from "@/types/ai";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Filter,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface BiasDetectorProps {
  text: string;
  biasAnalysis: BiasAnalysisResponse | null;
  onReplace?: (original: string, replacement: string) => void;
  onIgnore?: (issue: BiasIssue) => void;
  enabled?: boolean;
  compact?: boolean; // Compact mode for inline display
  className?: string;
}

const SEVERITY_COLORS = {
  critical: "bg-red-600 text-white",
  high: "bg-red-500 text-white",
  medium: "bg-yellow-500 text-white",
  low: "bg-yellow-400 text-gray-900",
};

const SEVERITY_TEXT_COLORS = {
  critical: "text-red-700",
  high: "text-red-600",
  medium: "text-yellow-600",
  low: "text-yellow-500",
};

const SEVERITY_BG_COLORS = {
  critical: "bg-red-100",
  high: "bg-red-50",
  medium: "bg-yellow-100",
  low: "bg-yellow-50",
};

const BIAS_TYPE_LABELS = {
  gender: "Gender",
  age: "Age",
  disability: "Disability",
  cultural: "Cultural",
  gender_coded_masculine: "Masculine-coded",
  gender_coded_feminine: "Feminine-coded",
};

/**
 * Bias Detector - Main Component
 */
export function BiasDetector({
  text,
  biasAnalysis,
  onReplace,
  onIgnore,
  enabled = true,
  compact = false,
  className = "",
}: BiasDetectorProps) {
  const [selectedTypes, setSelectedTypes] = useState<string[]>([
    "gender",
    "age",
    "disability",
    "cultural",
  ]);
  const [showFilters, setShowFilters] = useState(false);

  // Filter issues by selected types
  const filteredIssues = useMemo(() => {
    if (!biasAnalysis?.issues) return [];
    return biasAnalysis.issues.filter((issue) =>
      selectedTypes.includes(issue.type),
    );
  }, [biasAnalysis, selectedTypes]);

  // Highlight text with bias issues
  const highlightedText = useMemo(() => {
    if (!enabled || filteredIssues.length === 0) {
      return <span>{text}</span>;
    }

    return (
      <HighlightedText
        text={text}
        issues={filteredIssues}
        onReplace={onReplace}
      />
    );
  }, [text, filteredIssues, enabled, onReplace]);

  if (!enabled) {
    return <div className={className}>{text}</div>;
  }

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with Filter Toggle */}
      <div className="flex items-center justify-between">
        <BiasStatusBadge
          biasAnalysis={biasAnalysis}
          filteredCount={filteredIssues.length}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className="gap-2"
        >
          <Filter className="h-4 w-4" />
          Filters
          {showFilters ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Type Filters */}
      {showFilters && (
        <Card className="p-3">
          <div className="flex flex-wrap gap-2">
            {Object.entries(BIAS_TYPE_LABELS).map(([type, label]) => (
              <Badge
                key={type}
                variant={selectedTypes.includes(type) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleType(type)}
              >
                {label}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* Highlighted Text */}
      <Card className="p-4">
        <div className="prose max-w-none">{highlightedText}</div>
      </Card>

      {/* Issues List */}
      {filteredIssues.length > 0 && (
        <BiasIssuesList
          issues={filteredIssues}
          onReplace={onReplace}
          onIgnore={onIgnore}
        />
      )}
    </div>
  );
}

/**
 * Bias Status Badge - Shows overall bias status
 */
function BiasStatusBadge({
  biasAnalysis,
  filteredCount,
}: {
  biasAnalysis: BiasAnalysisResponse | null;
  filteredCount: number;
}) {
  if (!biasAnalysis) {
    return (
      <Badge variant="outline" className="gap-2">
        <AlertCircle className="h-3 w-3" />
        No analysis
      </Badge>
    );
  }

  if (biasAnalysis.bias_free) {
    return (
      <Badge className="gap-2 bg-green-100 text-green-700 hover:bg-green-200">
        <CheckCircle2 className="h-3 w-3" />
        Bias-Free
      </Badge>
    );
  }

  const score = Math.round(biasAnalysis.inclusivity_score * 100);
  const scoreColor =
    score >= 80
      ? "bg-green-100 text-green-700"
      : score >= 60
        ? "bg-yellow-100 text-yellow-700"
        : "bg-red-100 text-red-700";

  return (
    <div className="flex items-center gap-2">
      <Badge className={`gap-2 ${scoreColor}`}>
        <AlertTriangle className="h-3 w-3" />
        {filteredCount} {filteredCount === 1 ? "Issue" : "Issues"}
      </Badge>
      <span className="text-sm text-gray-600">Inclusivity: {score}%</span>
    </div>
  );
}

/**
 * Highlighted Text - Text with bias issues highlighted
 */
function HighlightedText({
  text,
  issues,
  onReplace,
}: {
  text: string;
  issues: BiasIssue[];
  onReplace?: (original: string, replacement: string) => void;
}) {
  // Sort issues by start index
  const sortedIssues = [...issues].sort(
    (a, b) => a.start_index - b.start_index,
  );

  const segments: React.ReactNode[] = [];
  let currentIndex = 0;

  sortedIssues.forEach((issue, idx) => {
    // Add text before this issue
    if (currentIndex < issue.start_index) {
      segments.push(
        <span key={`text-${idx}`}>
          {text.substring(currentIndex, issue.start_index)}
        </span>,
      );
    }

    // Add highlighted issue
    segments.push(
      <BiasHighlight
        key={`issue-${idx}`}
        issue={issue}
        text={text.substring(issue.start_index, issue.end_index)}
        onReplace={onReplace}
      />,
    );

    currentIndex = issue.end_index;
  });

  // Add remaining text
  if (currentIndex < text.length) {
    segments.push(<span key="text-end">{text.substring(currentIndex)}</span>);
  }

  return <>{segments}</>;
}

/**
 * Bias Highlight - Single highlighted bias issue with tooltip
 */
function BiasHighlight({
  issue,
  text,
  onReplace,
}: {
  issue: BiasIssue;
  text: string;
  onReplace?: (original: string, replacement: string) => void;
}) {
  const bgColor =
    SEVERITY_BG_COLORS[issue.severity as keyof typeof SEVERITY_BG_COLORS];
  const textColor =
    SEVERITY_TEXT_COLORS[issue.severity as keyof typeof SEVERITY_TEXT_COLORS];

  return (
    <TooltipProvider delayDuration={200}>
      <TooltipTrigger asChild>
        <mark className={`${bgColor} ${textColor} cursor-help px-0.5 rounded`}>
          {text}
        </mark>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-sm">
        <BiasTooltip issue={issue} onReplace={onReplace} />
      </TooltipContent>
    </TooltipProvider>
  );
}

/**
 * Bias Tooltip - Tooltip content for bias issue
 */
function BiasTooltip({
  issue,
  onReplace,
}: {
  issue: BiasIssue;
  onReplace?: (original: string, replacement: string) => void;
}) {
  return (
    <div className="space-y-2 p-1">
      <div className="flex items-center gap-2">
        <Badge
          className={
            SEVERITY_COLORS[issue.severity as keyof typeof SEVERITY_COLORS]
          }
        >
          {issue.severity}
        </Badge>
        <Badge variant="outline">
          {BIAS_TYPE_LABELS[issue.type as keyof typeof BIAS_TYPE_LABELS]}
        </Badge>
      </div>

      <p className="text-sm">{issue.description}</p>

      {issue.suggested_alternatives.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-gray-500">Alternatives:</p>
          <div className="flex flex-wrap gap-1">
            {issue.suggested_alternatives.map((alt, idx) => (
              <Button
                key={idx}
                size="sm"
                variant="outline"
                onClick={() => onReplace?.(issue.problematic_text, alt)}
                className="h-7 text-xs"
              >
                "{alt}"
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Bias Issues List - List of all bias issues with actions
 */
function BiasIssuesList({
  issues,
  onReplace,
  onIgnore,
}: {
  issues: BiasIssue[];
  onReplace?: (original: string, replacement: string) => void;
  onIgnore?: (issue: BiasIssue) => void;
}) {
  // Group issues by type
  const groupedIssues = useMemo(() => {
    const groups: Record<string, BiasIssue[]> = {};
    issues.forEach((issue) => {
      if (!groups[issue.type]) {
        groups[issue.type] = [];
      }
      groups[issue.type].push(issue);
    });
    return groups;
  }, [issues]);

  return (
    <Card className="p-4">
      <h4 className="font-medium mb-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        Bias Issues ({issues.length})
      </h4>
      <div className="space-y-4">
        {Object.entries(groupedIssues).map(([type, typeIssues]) => (
          <div key={type} className="space-y-2">
            <h5 className="text-sm font-medium text-gray-700">
              {BIAS_TYPE_LABELS[type as keyof typeof BIAS_TYPE_LABELS]} (
              {typeIssues.length})
            </h5>
            <div className="space-y-2">
              {typeIssues.map((issue, idx) => (
                <BiasIssueCard
                  key={idx}
                  issue={issue}
                  onReplace={onReplace}
                  onIgnore={onIgnore}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/**
 * Bias Issue Card - Individual issue with action buttons
 */
function BiasIssueCard({
  issue,
  onReplace,
  onIgnore,
}: {
  issue: BiasIssue;
  onReplace?: (original: string, replacement: string) => void;
  onIgnore?: (issue: BiasIssue) => void;
}) {
  const bgColor =
    SEVERITY_BG_COLORS[issue.severity as keyof typeof SEVERITY_BG_COLORS];

  return (
    <div className={`p-3 rounded border ${bgColor}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <code className="text-sm font-mono bg-white px-2 py-0.5 rounded">
              "{issue.problematic_text}"
            </code>
            <Badge variant="outline" className="text-xs">
              {issue.severity}
            </Badge>
          </div>
          <p className="text-sm text-gray-700">{issue.description}</p>
        </div>
        {onIgnore && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onIgnore(issue)}
            className="shrink-0"
          >
            <XCircle className="h-4 w-4" />
          </Button>
        )}
      </div>

      {issue.suggested_alternatives.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {issue.suggested_alternatives.map((alt, idx) => (
            <Button
              key={idx}
              size="sm"
              variant="outline"
              onClick={() => onReplace?.(issue.problematic_text, alt)}
              className="text-xs"
            >
              Replace with "{alt}"
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Compact Bias Badge - Minimal display for headers/sidebars
 */
export function CompactBiasBadge({
  biasAnalysis,
}: {
  biasAnalysis: BiasAnalysisResponse | null;
}) {
  if (!biasAnalysis) return null;

  if (biasAnalysis.bias_free) {
    return (
      <Badge className="gap-1 bg-green-100 text-green-700">
        <CheckCircle2 className="h-3 w-3" />
        Bias-Free
      </Badge>
    );
  }

  const criticalCount = biasAnalysis.issues.filter(
    (i) => i.severity === "critical" || i.severity === "high",
  ).length;

  return (
    <Badge className="gap-1 bg-yellow-100 text-yellow-700">
      <AlertTriangle className="h-3 w-3" />
      {biasAnalysis.issues.length}{" "}
      {criticalCount > 0 && `(${criticalCount} critical)`}
    </Badge>
  );
}
