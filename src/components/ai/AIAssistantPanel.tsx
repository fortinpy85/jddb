/**
 * AI Assistant Panel Component
 *
 * Displays AI suggestions and controls in a side panel with:
 * - Suggestion list grouped by type
 * - Quality score indicator
 * - Bulk accept/reject actions
 * - Filter controls
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import {
  Sparkles,
  Check,
  X,
  AlertCircle,
  Lightbulb,
  Filter,
  RefreshCw,
} from "lucide-react";
import { AISuggestion } from "@/hooks/useAISuggestions";

interface AIAssistantPanelProps {
  suggestions: AISuggestion[];
  overallScore: number | null;
  isLoading?: boolean;
  onAcceptSuggestion?: (suggestion: AISuggestion) => void;
  onRejectSuggestion?: (suggestion: AISuggestion) => void;
  onAcceptAll?: () => void;
  onRejectAll?: () => void;
  onRefresh?: () => void;
}

const SUGGESTION_TYPE_LABELS = {
  grammar: {
    label: "Grammar",
    icon: AlertCircle,
    color: "text-red-600",
    bg: "bg-red-100",
  },
  style: {
    label: "Style",
    icon: Lightbulb,
    color: "text-blue-600",
    bg: "bg-blue-100",
  },
  clarity: {
    label: "Clarity",
    icon: Lightbulb,
    color: "text-yellow-600",
    bg: "bg-yellow-100",
  },
  bias: {
    label: "Inclusivity",
    icon: AlertCircle,
    color: "text-purple-600",
    bg: "bg-purple-100",
  },
  compliance: {
    label: "Compliance",
    icon: AlertCircle,
    color: "text-orange-600",
    bg: "bg-orange-100",
  },
};

export const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({
  suggestions,
  overallScore,
  isLoading = false,
  onAcceptSuggestion,
  onRejectSuggestion,
  onAcceptAll,
  onRejectAll,
  onRefresh,
}) => {
  const [enabledTypes, setEnabledTypes] = useState<Record<string, boolean>>({
    grammar: true,
    style: true,
    clarity: true,
    bias: true,
    compliance: true,
  });

  // Group suggestions by type
  const groupedSuggestions = suggestions.reduce(
    (acc, suggestion) => {
      if (!acc[suggestion.type]) {
        acc[suggestion.type] = [];
      }
      acc[suggestion.type].push(suggestion);
      return acc;
    },
    {} as Record<string, AISuggestion[]>,
  );

  // Filter suggestions by enabled types
  const filteredSuggestions = suggestions.filter((s) => enabledTypes[s.type]);

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return "text-green-600";
    if (score >= 0.7) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.9) return "Excellent";
    if (score >= 0.7) return "Good";
    if (score >= 0.5) return "Fair";
    return "Needs Improvement";
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <span>AI Assistant</span>
          </CardTitle>
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
            >
              <RefreshCw
                className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
              />
            </Button>
          )}
        </div>

        {/* Overall Score */}
        {overallScore !== null && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Quality Score</span>
              <span
                className={`text-sm font-bold ${getScoreColor(overallScore)}`}
              >
                {Math.round(overallScore * 100)}% -{" "}
                {getScoreLabel(overallScore)}
              </span>
            </div>
            <Progress value={overallScore * 100} className="h-2" />
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto">
        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin text-purple-600" />
            <span className="ml-2 text-sm text-gray-600">
              Analyzing text...
            </span>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && suggestions.length === 0 && (
          <div className="text-center py-8">
            <Sparkles className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p className="text-sm text-gray-500">
              No suggestions available. Start typing to get AI-powered
              recommendations.
            </p>
          </div>
        )}

        {/* Suggestions List */}
        {!isLoading && filteredSuggestions.length > 0 && (
          <div className="space-y-4">
            {/* Filter Controls */}
            <div className="bg-gray-50 rounded p-3">
              <div className="flex items-center space-x-2 mb-2">
                <Filter className="w-4 h-4 text-gray-600" />
                <span className="text-xs font-medium text-gray-700">
                  Filter by Type
                </span>
              </div>
              <div className="space-y-2">
                {Object.entries(SUGGESTION_TYPE_LABELS).map(
                  ([type, config]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between"
                    >
                      <span className="text-xs text-gray-600">
                        {config.label}
                      </span>
                      <Switch
                        checked={enabledTypes[type]}
                        onCheckedChange={(checked) =>
                          setEnabledTypes((prev) => ({
                            ...prev,
                            [type]: checked,
                          }))
                        }
                      />
                    </div>
                  ),
                )}
              </div>
            </div>

            {/* Bulk Actions */}
            <div className="flex space-x-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={onAcceptAll}
              >
                <Check className="w-4 h-4 mr-1" />
                Accept All ({filteredSuggestions.length})
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={onRejectAll}
              >
                <X className="w-4 h-4 mr-1" />
                Reject All
              </Button>
            </div>

            {/* Grouped Suggestions */}
            {Object.entries(groupedSuggestions).map(
              ([type, typeSuggestions]) => {
                if (!enabledTypes[type]) return null;

                const config =
                  SUGGESTION_TYPE_LABELS[
                    type as keyof typeof SUGGESTION_TYPE_LABELS
                  ];
                const Icon = config.icon;

                return (
                  <div key={type} className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Icon className={`w-4 h-4 ${config.color}`} />
                      <span className="text-sm font-medium text-gray-900">
                        {config.label}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {typeSuggestions.length}
                      </Badge>
                    </div>

                    {typeSuggestions.map((suggestion) => (
                      <Card
                        key={suggestion.id}
                        className="border-l-4"
                        style={{ borderLeftColor: config.color }}
                      >
                        <CardContent className="p-3">
                          <p className="text-xs text-gray-700 mb-2">
                            {suggestion.explanation}
                          </p>
                          <div className="space-y-1 mb-3">
                            <div className="text-xs">
                              <span className="text-gray-500">From: </span>
                              <span className="line-through">
                                {suggestion.original_text}
                              </span>
                            </div>
                            <div className="text-xs">
                              <span className="text-gray-500">To: </span>
                              <span className="font-medium text-green-700">
                                {suggestion.suggested_text}
                              </span>
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              onClick={() => onAcceptSuggestion?.(suggestion)}
                              className="flex-1 h-7 text-xs"
                            >
                              <Check className="w-3 h-3 mr-1" />
                              Accept
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => onRejectSuggestion?.(suggestion)}
                              className="flex-1 h-7 text-xs"
                            >
                              <X className="w-3 h-3 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                );
              },
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
