/**
 * React Hook for AI Suggestions
 *
 * Manages AI-powered text suggestions with:
 * - Suggestion fetching and caching
 * - Accept/reject workflow
 * - Real-time suggestion updates
 */

import { useState, useCallback } from "react";
import { api } from "@/lib/api";

export interface AISuggestion {
  id: string;
  type: "grammar" | "style" | "clarity" | "bias" | "compliance";
  original_text: string;
  suggested_text: string;
  explanation: string;
  confidence: number;
  start_index: number;
  end_index: number;
}

export interface SuggestionsResponse {
  suggestions: AISuggestion[];
  overall_score: number;
  processing_time_ms: number;
}

export interface UseAISuggestionsOptions {
  autoFetch?: boolean;
  debounceMs?: number;
}

export interface UseAISuggestionsReturn {
  suggestions: AISuggestion[];
  isLoading: boolean;
  error: string | null;
  overallScore: number | null;
  fetchSuggestions: (
    text: string,
    context?: string,
    types?: string[],
  ) => Promise<void>;
  acceptSuggestion: (suggestionId: string) => void;
  rejectSuggestion: (suggestionId: string) => void;
  clearSuggestions: () => void;
}

/**
 * Hook for managing AI text suggestions
 */
export function useAISuggestions(
  options: UseAISuggestionsOptions = {},
): UseAISuggestionsReturn {
  const { autoFetch = false, debounceMs = 1000 } = options;

  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overallScore, setOverallScore] = useState<number | null>(null);

  const fetchSuggestions = useCallback(
    async (text: string, context?: string, suggestionTypes?: string[]) => {
      if (!text || text.length < 10) {
        setSuggestions([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${api.getBaseUrl()}/ai/suggest-improvements`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              text,
              context,
              suggestion_types: suggestionTypes || [
                "grammar",
                "style",
                "clarity",
              ],
            }),
          },
        );

        if (!response.ok) {
          throw new Error(
            `Failed to fetch suggestions: ${response.statusText}`,
          );
        }

        const data: SuggestionsResponse = await response.json();
        setSuggestions(data.suggestions);
        setOverallScore(data.overall_score);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to fetch suggestions";
        setError(errorMessage);
        console.error("Error fetching AI suggestions:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const acceptSuggestion = useCallback((suggestionId: string) => {
    setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
  }, []);

  const rejectSuggestion = useCallback((suggestionId: string) => {
    setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
  }, []);

  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setOverallScore(null);
    setError(null);
  }, []);

  return {
    suggestions,
    isLoading,
    error,
    overallScore,
    fetchSuggestions,
    acceptSuggestion,
    rejectSuggestion,
    clearSuggestions,
  };
}
