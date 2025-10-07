/**
 * LiveSuggestionsPanel Component
 *
 * Contextual sidebar for live reactive improvements.
 * Inspired by Grammarly's suggestion panel with real-time AI analysis.
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import type { TextChange } from "@/utils/diffAnalysis";
import type { AISuggestion } from "@/hooks/useAISuggestions";
import {
  Sparkles,
  Check,
  X,
  AlertCircle,
  Info,
  TrendingUp,
  Target,
  Zap,
  ChevronRight,
  Loader2,
} from "lucide-react";

export interface LiveSuggestionsPanelProps {
  suggestions: AISuggestion[];
  changes: TextChange[];
  currentSuggestion: AISuggestion | null;
  overallScore: number | null;
  isAnalyzing: boolean;
  onAccept: (suggestion: AISuggestion) => void;
  onReject: (suggestion: AISuggestion) => void;
  onSuggestionClick: (suggestion: AISuggestion) => void;
  className?: string;
}

/**
 * Main LiveSuggestionsPanel Component
 */
export function LiveSuggestionsPanel({
  suggestions,
  changes,
  currentSuggestion,
  overallScore,
  isAnalyzing,
  onAccept,
  onReject,
  onSuggestionClick,
  className = "",
}: LiveSuggestionsPanelProps) {
  const [expandedSuggestions, setExpandedSuggestions] = useState<Set<string>>(
    new Set()
  );

  // Group suggestions by type
  const groupedSuggestions = suggestions.reduce((acc, suggestion) => {
    if (!acc[suggestion.type]) {
      acc[suggestion.type] = [];
    }
    acc[suggestion.type].push(suggestion);
    return acc;
  }, {} as Record<string, AISuggestion[]>);

  const toggleSuggestion = (id: string) => {
    setExpandedSuggestions((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <Card className={cn("flex flex-col h-full", className)}>
      <CardHeader className="pb-3 border-b">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-600" />
              AI Suggestions
              {isAnalyzing && (
                <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
              )}
            </CardTitle>
            {suggestions.length > 0 && (
              <Badge variant="outline" className="text-xs">
                {suggestions.length}
              </Badge>
            )}
          </div>

          {/* Overall Quality Score */}
          {overallScore !== null && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-400">
                  Quality Score
                </span>
                <span className={cn("font-semibold", getScoreColor(overallScore))}>
                  {Math.round(overallScore * 100)}%
                </span>
              </div>
              <Progress value={overallScore * 100} className="h-2" />
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {getScoreMessage(overallScore)}
              </p>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4 space-y-4">
            {isAnalyzing && suggestions.length === 0 ? (
              <AnalyzingState />
            ) : suggestions.length === 0 ? (
              <EmptyState />
            ) : (
              <>
                {/* Current Suggestion (if any) */}
                {currentSuggestion && (
                  <CurrentSuggestionCard
                    suggestion={currentSuggestion}
                    onAccept={onAccept}
                    onReject={onReject}
                  />
                )}

                <Separator />

                {/* All Suggestions by Type */}
                {Object.entries(groupedSuggestions).map(([type, typeSuggestions]) => (
                  <SuggestionTypeGroup
                    key={type}
                    type={type as AISuggestion["type"]}
                    suggestions={typeSuggestions}
                    expandedSuggestions={expandedSuggestions}
                    onToggle={toggleSuggestion}
                    onSuggestionClick={onSuggestionClick}
                    onAccept={onAccept}
                    onReject={onReject}
                  />
                ))}
              </>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

/**
 * Current Suggestion Card (Highlighted)
 */
interface CurrentSuggestionCardProps {
  suggestion: AISuggestion;
  onAccept: (suggestion: AISuggestion) => void;
  onReject: (suggestion: AISuggestion) => void;
}

function CurrentSuggestionCard({
  suggestion,
  onAccept,
  onReject,
}: CurrentSuggestionCardProps) {
  return (
    <div className="space-y-3 p-4 bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-300 dark:border-blue-700 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2">
            <Badge className={getTypeBadgeClass(suggestion.type)}>
              {suggestion.type}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {Math.round(suggestion.confidence * 100)}% confident
            </Badge>
          </div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Current Suggestion
          </h4>
        </div>
      </div>

      {/* Original vs Suggested */}
      <div className="space-y-2">
        <div className="text-xs space-y-1">
          <div className="text-gray-600 dark:text-gray-400">Original:</div>
          <code className="block px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded text-xs">
            {suggestion.original_text}
          </code>
        </div>
        <div className="text-xs space-y-1">
          <div className="text-gray-600 dark:text-gray-400">Suggested:</div>
          <code className="block px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded text-xs">
            {suggestion.suggested_text}
          </code>
        </div>
      </div>

      {/* Explanation */}
      {suggestion.explanation && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription className="text-xs">
            {suggestion.explanation}
          </AlertDescription>
        </Alert>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2">
        <Button
          size="sm"
          onClick={() => onAccept(suggestion)}
          className="flex-1 bg-green-600 hover:bg-green-700"
        >
          <Check className="h-3 w-3 mr-1" />
          Accept
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onReject(suggestion)}
          className="flex-1"
        >
          <X className="h-3 w-3 mr-1" />
          Reject
        </Button>
      </div>
    </div>
  );
}

/**
 * Suggestion Type Group
 */
interface SuggestionTypeGroupProps {
  type: AISuggestion["type"];
  suggestions: AISuggestion[];
  expandedSuggestions: Set<string>;
  onToggle: (id: string) => void;
  onSuggestionClick: (suggestion: AISuggestion) => void;
  onAccept: (suggestion: AISuggestion) => void;
  onReject: (suggestion: AISuggestion) => void;
}

function SuggestionTypeGroup({
  type,
  suggestions,
  expandedSuggestions,
  onToggle,
  onSuggestionClick,
  onAccept,
  onReject,
}: SuggestionTypeGroupProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Badge className={getTypeBadgeClass(type)}>{type}</Badge>
        <span className="text-xs text-gray-500">
          {suggestions.length} {suggestions.length === 1 ? "issue" : "issues"}
        </span>
      </div>

      <div className="space-y-2 pl-2">
        {suggestions.map((suggestion) => (
          <CompactSuggestionCard
            key={suggestion.id}
            suggestion={suggestion}
            isExpanded={expandedSuggestions.has(suggestion.id)}
            onToggle={() => onToggle(suggestion.id)}
            onClick={() => onSuggestionClick(suggestion)}
            onAccept={onAccept}
            onReject={onReject}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Compact Suggestion Card
 */
interface CompactSuggestionCardProps {
  suggestion: AISuggestion;
  isExpanded: boolean;
  onToggle: () => void;
  onClick: () => void;
  onAccept: (suggestion: AISuggestion) => void;
  onReject: (suggestion: AISuggestion) => void;
}

function CompactSuggestionCard({
  suggestion,
  isExpanded,
  onToggle,
  onClick,
  onAccept,
  onReject,
}: CompactSuggestionCardProps) {
  return (
    <div
      className={cn(
        "border rounded-lg p-2 transition-all cursor-pointer hover:border-blue-300 dark:hover:border-blue-700",
        isExpanded && "bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-xs text-gray-700 dark:text-gray-300 truncate">
            "{suggestion.original_text}" → "{suggestion.suggested_text}"
          </div>
          {isExpanded && suggestion.explanation && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {suggestion.explanation}
            </p>
          )}
        </div>
        <ChevronRight
          className={cn(
            "h-4 w-4 text-gray-400 transition-transform flex-shrink-0",
            isExpanded && "rotate-90"
          )}
        />
      </div>

      {isExpanded && (
        <div className="flex items-center gap-1 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              onAccept(suggestion);
            }}
            className="flex-1 h-7 text-xs"
          >
            <Check className="h-3 w-3 mr-1" />
            Accept
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation();
              onReject(suggestion);
            }}
            className="flex-1 h-7 text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            Reject
          </Button>
        </div>
      )}
    </div>
  );
}

/**
 * Analyzing State
 */
function AnalyzingState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-3" />
      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Analyzing your content...
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        AI is reviewing for improvements
      </p>
    </div>
  );
}

/**
 * Empty State
 */
function EmptyState() {
  return (
    <Alert>
      <Sparkles className="h-4 w-4" />
      <AlertDescription className="text-xs">
        <p className="font-medium">No suggestions yet</p>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Start typing to get AI-powered improvement suggestions
        </p>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Helper functions
 */
function getTypeBadgeClass(type: string): string {
  switch (type) {
    case "grammar":
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
    case "style":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
    case "clarity":
      return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400";
    case "bias":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
    case "compliance":
      return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400";
  }
}

function getScoreColor(score: number): string {
  if (score >= 0.9) return "text-green-600 dark:text-green-400";
  if (score >= 0.75) return "text-blue-600 dark:text-blue-400";
  if (score >= 0.6) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
}

function getScoreMessage(score: number): string {
  if (score >= 0.9) return "Excellent quality! Minor improvements suggested.";
  if (score >= 0.75) return "Good quality. Some improvements available.";
  if (score >= 0.6) return "Acceptable. Consider applying suggestions.";
  return "Needs improvement. Review suggestions carefully.";
}
