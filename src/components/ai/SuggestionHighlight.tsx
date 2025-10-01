/**
 * AI Suggestion Highlight Component
 *
 * Displays inline text highlights for AI suggestions with:
 * - Color-coded highlighting by suggestion type
 * - Hover interactions
 * - Click to view details
 */

"use client";

import React from "react";
import { AISuggestion } from "@/hooks/useAISuggestions";

interface SuggestionHighlightProps {
  suggestion: AISuggestion;
  text: string;
  onHover?: (suggestion: AISuggestion | null) => void;
  onClick?: (suggestion: AISuggestion) => void;
}

const SUGGESTION_COLORS = {
  grammar: "bg-red-100 border-red-300 text-red-900",
  style: "bg-blue-100 border-blue-300 text-blue-900",
  clarity: "bg-yellow-100 border-yellow-300 text-yellow-900",
  bias: "bg-purple-100 border-purple-300 text-purple-900",
  compliance: "bg-orange-100 border-orange-300 text-orange-900",
};

const SUGGESTION_UNDERLINES = {
  grammar: "decoration-red-400 decoration-wavy",
  style: "decoration-blue-400 decoration-wavy",
  clarity: "decoration-yellow-400 decoration-wavy",
  bias: "decoration-purple-400 decoration-wavy",
  compliance: "decoration-orange-400 decoration-wavy",
};

export const SuggestionHighlight: React.FC<SuggestionHighlightProps> = ({
  suggestion,
  text,
  onHover,
  onClick,
}) => {
  const colorClass =
    SUGGESTION_COLORS[suggestion.type] || SUGGESTION_COLORS.grammar;
  const underlineClass =
    SUGGESTION_UNDERLINES[suggestion.type] || SUGGESTION_UNDERLINES.grammar;

  const highlightedText = text.substring(
    suggestion.start_index,
    suggestion.end_index,
  );

  return (
    <span
      className={`relative inline cursor-pointer underline ${underlineClass} hover:${colorClass} transition-colors rounded px-0.5`}
      onMouseEnter={() => onHover?.(suggestion)}
      onMouseLeave={() => onHover?.(null)}
      onClick={() => onClick?.(suggestion)}
      title={suggestion.explanation}
    >
      {highlightedText}
    </span>
  );
};

interface TextWithSuggestionsProps {
  text: string;
  suggestions: AISuggestion[];
  onSuggestionHover?: (suggestion: AISuggestion | null) => void;
  onSuggestionClick?: (suggestion: AISuggestion) => void;
}

/**
 * Renders text with inline suggestion highlights
 */
export const TextWithSuggestions: React.FC<TextWithSuggestionsProps> = ({
  text,
  suggestions,
  onSuggestionHover,
  onSuggestionClick,
}) => {
  if (!suggestions || suggestions.length === 0) {
    return <span>{text}</span>;
  }

  // Sort suggestions by start index
  const sortedSuggestions = [...suggestions].sort(
    (a, b) => a.start_index - b.start_index,
  );

  const elements: React.ReactNode[] = [];
  let currentIndex = 0;

  sortedSuggestions.forEach((suggestion, idx) => {
    // Add text before suggestion
    if (currentIndex < suggestion.start_index) {
      elements.push(
        <span key={`text-${idx}`}>
          {text.substring(currentIndex, suggestion.start_index)}
        </span>,
      );
    }

    // Add highlighted suggestion
    elements.push(
      <SuggestionHighlight
        key={`suggestion-${suggestion.id}`}
        suggestion={suggestion}
        text={text}
        onHover={onSuggestionHover}
        onClick={onSuggestionClick}
      />,
    );

    currentIndex = suggestion.end_index;
  });

  // Add remaining text
  if (currentIndex < text.length) {
    elements.push(<span key="text-end">{text.substring(currentIndex)}</span>);
  }

  return <>{elements}</>;
};
