/**
 * AI Suggestions Panel
 * Phase 3: Advanced AI Content Intelligence
 *
 * Real-time AI suggestions display with accept/reject actions
 */

import React, { useState, useMemo } from 'react';
import type { AISuggestion } from '@/hooks/useAISuggestions';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sparkles,
  Check,
  X,
  AlertCircle,
  FileText,
  PenTool,
  Target,
  Shield,
  Filter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface AISuggestionsPanelProps {
  suggestions: AISuggestion[];
  loading?: boolean;
  overallScore?: number | null;
  onAccept?: (suggestion: AISuggestion) => void;
  onReject?: (suggestion: AISuggestion) => void;
  onClear?: () => void;
  className?: string;
}

const SUGGESTION_TYPE_LABELS = {
  grammar: 'Grammar',
  style: 'Style',
  clarity: 'Clarity',
  bias: 'Bias',
  compliance: 'Compliance',
};

const SUGGESTION_TYPE_ICONS = {
  grammar: FileText,
  style: PenTool,
  clarity: Target,
  bias: AlertCircle,
  compliance: Shield,
};

const SUGGESTION_TYPE_COLORS = {
  grammar: 'text-red-600 bg-red-50',
  style: 'text-blue-600 bg-blue-50',
  clarity: 'text-purple-600 bg-purple-50',
  bias: 'text-yellow-600 bg-yellow-50',
  compliance: 'text-green-600 bg-green-50',
};

/**
 * AI Suggestions Panel - Main Component
 */
export function AISuggestionsPanel({
  suggestions,
  loading = false,
  overallScore = null,
  onAccept,
  onReject,
  onClear,
  className = '',
}: AISuggestionsPanelProps) {
  const [selectedTypes, setSelectedTypes] = useState<string[]>([
    'grammar',
    'style',
    'clarity',
    'bias',
    'compliance',
  ]);
  const [showFilters, setShowFilters] = useState(false);

  // Filter suggestions by selected types
  const filteredSuggestions = useMemo(() => {
    return suggestions.filter((s) => selectedTypes.includes(s.type));
  }, [suggestions, selectedTypes]);

  // Group suggestions by type
  const groupedSuggestions = useMemo(() => {
    const groups: Record<string, AISuggestion[]> = {};
    filteredSuggestions.forEach((suggestion) => {
      if (!groups[suggestion.type]) {
        groups[suggestion.type] = [];
      }
      groups[suggestion.type].push(suggestion);
    });
    return groups;
  }, [filteredSuggestions]);

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  return (
    <Card className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold">AI Suggestions</h3>
            {filteredSuggestions.length > 0 && (
              <Badge variant="outline">{filteredSuggestions.length}</Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4" />
              {showFilters ? (
                <ChevronUp className="h-4 w-4 ml-1" />
              ) : (
                <ChevronDown className="h-4 w-4 ml-1" />
              )}
            </Button>
            {onClear && suggestions.length > 0 && (
              <Button variant="ghost" size="sm" onClick={onClear}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Overall Score */}
        {overallScore !== null && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Overall Score:</span>
            <Badge className={getScoreBadgeColor(overallScore)}>
              {Math.round(overallScore * 100)}%
            </Badge>
          </div>
        )}

        {/* Type Filters */}
        {showFilters && (
          <div className="flex flex-wrap gap-2 pt-2">
            {Object.entries(SUGGESTION_TYPE_LABELS).map(([type, label]) => {
              const count = suggestions.filter((s) => s.type === type).length;
              return (
                <Badge
                  key={type}
                  variant={selectedTypes.includes(type) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => toggleType(type)}
                >
                  {label} {count > 0 && `(${count})`}
                </Badge>
              );
            })}
          </div>
        )}
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        {loading ? (
          <LoadingSkeleton />
        ) : filteredSuggestions.length === 0 ? (
          <EmptyState hasFilters={selectedTypes.length < 5} />
        ) : (
          <div className="space-y-4">
            {Object.entries(groupedSuggestions).map(([type, typeSuggestions]) => (
              <SuggestionTypeGroup
                key={type}
                type={type as AISuggestion['type']}
                suggestions={typeSuggestions}
                onAccept={onAccept}
                onReject={onReject}
              />
            ))}
          </div>
        )}
      </ScrollArea>
    </Card>
  );
}

/**
 * Suggestion Type Group - Group of suggestions by type
 */
function SuggestionTypeGroup({
  type,
  suggestions,
  onAccept,
  onReject,
}: {
  type: AISuggestion['type'];
  suggestions: AISuggestion[];
  onAccept?: (suggestion: AISuggestion) => void;
  onReject?: (suggestion: AISuggestion) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const Icon = SUGGESTION_TYPE_ICONS[type];
  const label = SUGGESTION_TYPE_LABELS[type];

  return (
    <div className="space-y-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full text-left"
      >
        <Icon className="h-4 w-4 text-gray-600" />
        <h4 className="text-sm font-medium text-gray-700">{label}</h4>
        <Badge variant="outline" className="text-xs">
          {suggestions.length}
        </Badge>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 ml-auto text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 ml-auto text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="space-y-2 pl-6">
          {suggestions.map((suggestion) => (
            <SuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              onAccept={onAccept}
              onReject={onReject}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Suggestion Card - Individual suggestion with actions
 */
function SuggestionCard({
  suggestion,
  onAccept,
  onReject,
}: {
  suggestion: AISuggestion;
  onAccept?: (suggestion: AISuggestion) => void;
  onReject?: (suggestion: AISuggestion) => void;
}) {
  const colorClass = SUGGESTION_TYPE_COLORS[suggestion.type];

  return (
    <Card className={`p-3 ${colorClass}`}>
      <div className="space-y-2">
        {/* Original vs Suggested */}
        <div className="space-y-1">
          <div className="flex items-start gap-2">
            <span className="text-xs text-gray-500 mt-0.5 shrink-0">Original:</span>
            <code className="text-xs font-mono text-gray-700 bg-white px-2 py-0.5 rounded flex-1">
              {suggestion.original_text}
            </code>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-xs text-gray-500 mt-0.5 shrink-0">Suggested:</span>
            <code className="text-xs font-mono text-green-700 bg-green-50 px-2 py-0.5 rounded flex-1 border border-green-200">
              {suggestion.suggested_text}
            </code>
          </div>
        </div>

        {/* Explanation */}
        <p className="text-xs text-gray-700">{suggestion.explanation}</p>

        {/* Confidence & Actions */}
        <div className="flex items-center justify-between pt-2">
          <Badge variant="outline" className="text-xs">
            {Math.round(suggestion.confidence * 100)}% confidence
          </Badge>
          <div className="flex items-center gap-1">
            {onAccept && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onAccept(suggestion)}
                className="h-7 gap-1 text-xs"
              >
                <Check className="h-3 w-3" />
                Accept
              </Button>
            )}
            {onReject && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onReject(suggestion)}
                className="h-7 gap-1 text-xs"
              >
                <X className="h-3 w-3" />
                Ignore
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

/**
 * Loading Skeleton
 */
function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      ))}
    </div>
  );
}

/**
 * Empty State
 */
function EmptyState({ hasFilters }: { hasFilters: boolean }) {
  return (
    <Alert>
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>
        {hasFilters
          ? 'No suggestions match your filters. Try adjusting your filter selection.'
          : 'No suggestions available. AI will analyze your content and provide improvement suggestions.'}
      </AlertDescription>
    </Alert>
  );
}

/**
 * Get badge color based on score
 */
function getScoreBadgeColor(score: number): string {
  if (score >= 0.9) return 'bg-green-100 text-green-700';
  if (score >= 0.75) return 'bg-blue-100 text-blue-700';
  if (score >= 0.6) return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

/**
 * Compact Suggestions Badge - For headers/toolbars
 */
export function CompactSuggestionsBadge({
  count,
  score,
}: {
  count: number;
  score?: number | null;
}) {
  if (count === 0) return null;

  return (
    <Badge className="gap-1 bg-blue-100 text-blue-700">
      <Sparkles className="h-3 w-3" />
      {count} {count === 1 ? 'suggestion' : 'suggestions'}
      {score !== null && score !== undefined && ` (${Math.round(score * 100)}%)`}
    </Badge>
  );
}
