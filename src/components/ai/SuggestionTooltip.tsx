/**
 * AI Suggestion Tooltip Component
 *
 * Displays detailed suggestion information with:
 * - Explanation and confidence score
 * - Accept/Reject actions
 * - Original and suggested text comparison
 */

"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Check, X, Lightbulb, AlertCircle } from "lucide-react";
import { AISuggestion } from "@/hooks/useAISuggestions";

interface SuggestionTooltipProps {
  suggestion: AISuggestion;
  position?: { top: number; left: number };
  onAccept?: (suggestion: AISuggestion) => void;
  onReject?: (suggestion: AISuggestion) => void;
}

const SUGGESTION_TYPES = {
  grammar: { label: "Grammar", icon: AlertCircle, color: "text-red-600" },
  style: { label: "Style", icon: Lightbulb, color: "text-blue-600" },
  clarity: { label: "Clarity", icon: Lightbulb, color: "text-yellow-600" },
  bias: { label: "Inclusivity", icon: AlertCircle, color: "text-purple-600" },
  compliance: { label: "Compliance", icon: AlertCircle, color: "text-orange-600" },
};

export const SuggestionTooltip: React.FC<SuggestionTooltipProps> = ({
  suggestion,
  position,
  onAccept,
  onReject,
}) => {
  const suggestionType = SUGGESTION_TYPES[suggestion.type] || SUGGESTION_TYPES.grammar;
  const Icon = suggestionType.icon;

  return (
    <Card
      className="absolute z-50 w-80 shadow-lg border-2"
      style={{
        top: position ? `${position.top}px` : 'auto',
        left: position ? `${position.left}px` : 'auto',
      }}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Icon className={`w-4 h-4 ${suggestionType.color}`} />
            <span className="font-medium text-sm text-gray-900">
              {suggestionType.label}
            </span>
          </div>
          <Badge
            variant="outline"
            className="text-xs"
          >
            {Math.round(suggestion.confidence * 100)}% confidence
          </Badge>
        </div>

        {/* Explanation */}
        <p className="text-sm text-gray-700 mb-3">
          {suggestion.explanation}
        </p>

        {/* Text Comparison */}
        <div className="space-y-2 mb-4">
          {/* Original Text */}
          <div className="bg-red-50 border border-red-200 rounded p-2">
            <div className="text-xs text-red-600 font-medium mb-1">Original:</div>
            <div className="text-sm text-gray-900 line-through">
              {suggestion.original_text}
            </div>
          </div>

          {/* Suggested Text */}
          <div className="bg-green-50 border border-green-200 rounded p-2">
            <div className="text-xs text-green-600 font-medium mb-1">Suggested:</div>
            <div className="text-sm text-gray-900 font-medium">
              {suggestion.suggested_text}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-2">
          <Button
            onClick={() => onAccept?.(suggestion)}
            size="sm"
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            <Check className="w-4 h-4 mr-1" />
            Accept
          </Button>
          <Button
            onClick={() => onReject?.(suggestion)}
            size="sm"
            variant="outline"
            className="flex-1"
          >
            <X className="w-4 h-4 mr-1" />
            Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

interface SuggestionTooltipPortalProps extends SuggestionTooltipProps {
  isOpen: boolean;
}

/**
 * Tooltip with portal support for better positioning
 */
export const SuggestionTooltipPortal: React.FC<SuggestionTooltipPortalProps> = ({
  isOpen,
  ...props
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 pointer-events-none">
      <div className="pointer-events-auto">
        <SuggestionTooltip {...props} />
      </div>
    </div>
  );
};