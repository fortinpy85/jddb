/**
 * React Hook for AI Suggestions
 * Phase 3: Enhanced with bias detection and quality scoring
 *
 * Manages AI-powered text suggestions with:
 * - Suggestion fetching and caching
 * - Accept/reject workflow
 * - Real-time suggestion updates
 * - Bias detection and analysis
 * - Quality scoring
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import type { BiasAnalysisResponse, QualityScoreResponse } from "@/types/ai";
import { logger } from "@/utils/logger";

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
  biasAnalysis: BiasAnalysisResponse | null;
  qualityScore: QualityScoreResponse | null;
  fetchSuggestions: (
    text: string,
    context?: string,
    types?: string[],
  ) => Promise<void>;
  analyzeBias: (text: string, useGPT4?: boolean) => Promise<void>;
  calculateQuality: (sections: Record<string, string>) => Promise<void>;
  acceptSuggestion: (suggestionId: string) => void;
  rejectSuggestion: (suggestionId: string) => void;
  clearSuggestions: () => void;
  clearAll: () => void;
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
  const [biasAnalysis, setBiasAnalysis] = useState<BiasAnalysisResponse | null>(
    null,
  );
  const [qualityScore, setQualityScore] = useState<QualityScoreResponse | null>(
    null,
  );

  const fetchSuggestions = useCallback(
    async (text: string, context?: string, suggestionTypes?: string[]) => {
      if (!text || text.length < 10) {
        setSuggestions([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await api.getSuggestions({
          text,
          context,
          suggestion_types: suggestionTypes || ["grammar", "style", "clarity"],
        });

        setSuggestions(data.suggestions);
        setOverallScore(data.overall_score);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to fetch suggestions";
        setError(errorMessage);
        logger.error("Error fetching AI suggestions:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const analyzeBias = useCallback(
    async (text: string, useGPT4: boolean = true) => {
      if (!text || text.length < 10) {
        setBiasAnalysis(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await api.analyzeBias({
          text,
          use_gpt4: useGPT4,
          analysis_types: ["gender", "age", "disability", "cultural"],
        });

        setBiasAnalysis(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to analyze bias";
        setError(errorMessage);
        logger.error("Error analyzing bias:", err);
        setBiasAnalysis(null);
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const calculateQuality = useCallback(
    async (sections: Record<string, string>) => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await api.calculateQualityScore({ sections });
        setQualityScore(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to calculate quality score";
        setError(errorMessage);
        logger.error("Error calculating quality:", err);
        setQualityScore(null);
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

  const clearAll = useCallback(() => {
    setSuggestions([]);
    setOverallScore(null);
    setBiasAnalysis(null);
    setQualityScore(null);
    setError(null);
  }, []);

  return {
    suggestions,
    isLoading,
    error,
    overallScore,
    biasAnalysis,
    qualityScore,
    fetchSuggestions,
    analyzeBias,
    calculateQuality,
    acceptSuggestion,
    rejectSuggestion,
    clearSuggestions,
    clearAll,
  };
}

/**
 * Hook for debounced AI analysis
 * Useful for real-time analysis as user types
 */
export function useDebouncedAIAnalysis(options: {
  onBiasAnalysis?: (result: BiasAnalysisResponse) => void;
  debounceMs?: number;
  minLength?: number;
  gpt4Enabled?: boolean;
}) {
  const {
    onBiasAnalysis,
    debounceMs = 1000,
    minLength = 50,
    gpt4Enabled = true,
  } = options;

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const analyzeText = useCallback(
    (text: string) => {
      // Clear previous timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Don't analyze if text is too short
      if (text.length < minLength) {
        setIsAnalyzing(false);
        return;
      }

      setIsAnalyzing(true);

      // Set new debounced timer
      debounceTimerRef.current = setTimeout(async () => {
        try {
          // Run bias analysis if callback provided
          if (onBiasAnalysis) {
            const biasResult = await api.analyzeBias({
              text,
              use_gpt4: gpt4Enabled,
            });
            onBiasAnalysis(biasResult);
          }
        } catch (err) {
          logger.error("Debounced analysis failed:", err);
        } finally {
          setIsAnalyzing(false);
        }
      }, debounceMs);
    },
    [onBiasAnalysis, debounceMs, minLength, gpt4Enabled],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    analyzeText,
    isAnalyzing,
  };
}
