/**
 * React Hook for Translation Memory
 *
 * Manages translation memory operations with:
 * - Concordance search
 * - Translation suggestions
 * - Match scoring and filtering
 * - Usage tracking
 */

import { useState, useCallback } from "react";
import { API_BASE_URL } from "@/lib/api";

export interface TranslationMatch {
  id: number;
  source_text: string;
  target_text: string;
  similarity_score: number;
  quality_score?: number;
  confidence_score?: number;
  usage_count: number;
  domain?: string;
  subdomain?: string;
  match_type: "exact" | "fuzzy";
  confidence: number;
  last_used?: string;
  created_at: string;
}

export interface TranslationSearchParams {
  source_text: string;
  source_language: string;
  target_language: string;
  min_similarity?: number;
  domain?: string;
  limit?: number;
}

export interface UseTranslationMemoryOptions {
  sourceLanguage?: string;
  targetLanguage?: string;
  minSimilarity?: number;
  autoSearch?: boolean;
}

export interface UseTranslationMemoryReturn {
  matches: TranslationMatch[];
  isLoading: boolean;
  error: string | null;
  searchTranslations: (params: TranslationSearchParams) => Promise<void>;
  addTranslation: (sourceText: string, targetText: string) => Promise<void>;
  updateTranslation: (id: number, targetText: string) => Promise<void>;
  rateTranslation: (id: number, rating: number) => Promise<void>;
  clearMatches: () => void;
}

/**
 * Hook for managing translation memory operations
 */
export function useTranslationMemory(
  options: UseTranslationMemoryOptions = {},
): UseTranslationMemoryReturn {
  const {
    sourceLanguage = "en",
    targetLanguage = "fr",
    minSimilarity = 0.7,
    autoSearch = false,
  } = options;

  const [matches, setMatches] = useState<TranslationMatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchTranslations = useCallback(
    async (params: TranslationSearchParams) => {
      if (!params.source_text || params.source_text.length < 3) {
        setMatches([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Build query parameters for POST /search endpoint
        const queryParams = new URLSearchParams({
          query_text: params.source_text,
          source_language: params.source_language || sourceLanguage,
          target_language: params.target_language || targetLanguage,
          similarity_threshold: (
            params.min_similarity || minSimilarity
          ).toString(),
          limit: (params.limit || 10).toString(),
        });

        if (params.domain) {
          // Note: API doesn't have domain parameter, but we include it for future use
        }

        const response = await fetch(
          `${API_BASE_URL}/translation-memory/search?${queryParams.toString()}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          },
        );

        if (!response.ok) {
          throw new Error(`Search failed: ${response.statusText}`);
        }

        const data = await response.json();
        setMatches(data.matches || []);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to search translations";
        setError(errorMessage);
        console.error("Error searching translation memory:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [sourceLanguage, targetLanguage, minSimilarity],
  );

  const addTranslation = useCallback(
    async (sourceText: string, targetText: string, projectId: number = 1) => {
      setIsLoading(true);
      setError(null);

      try {
        // Use project-based endpoint: POST /projects/{project_id}/translations
        const response = await fetch(
          `${API_BASE_URL}/translation-memory/projects/${projectId}/translations`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              source_text: sourceText,
              target_text: targetText,
              source_language: sourceLanguage,
              target_language: targetLanguage,
              domain: "job_descriptions",
            }),
          },
        );

        if (!response.ok) {
          throw new Error(`Failed to add translation: ${response.statusText}`);
        }

        // Optionally refresh matches after adding
        // await searchTranslations({ source_text: sourceText });
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to add translation";
        setError(errorMessage);
        console.error("Error adding translation:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [sourceLanguage, targetLanguage],
  );

  const updateTranslation = useCallback(
    async (id: number, targetText: string) => {
      setIsLoading(true);
      setError(null);

      try {
        // Note: Update endpoint not implemented in backend yet
        // This is a placeholder for future implementation
        console.warn("Update translation endpoint not yet implemented");

        // Update local match optimistically
        setMatches((prev) =>
          prev.map((match) =>
            match.id === id ? { ...match, target_text: targetText } : match,
          ),
        );
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to update translation";
        setError(errorMessage);
        console.error("Error updating translation:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const rateTranslation = useCallback(async (id: number, rating: number) => {
    setIsLoading(true);
    setError(null);

    try {
      // Use usage tracking endpoint: PUT /translations/{tm_id}/usage
      const response = await fetch(
        `${API_BASE_URL}/translation-memory/translations/${id}/usage`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            used_translation: rating >= 3,
            user_feedback: {
              rating,
              timestamp: new Date().toISOString(),
            },
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to rate translation: ${response.statusText}`);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to rate translation";
      setError(errorMessage);
      console.error("Error rating translation:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMatches = useCallback(() => {
    setMatches([]);
    setError(null);
  }, []);

  return {
    matches,
    isLoading,
    error,
    searchTranslations,
    addTranslation,
    updateTranslation,
    rateTranslation,
    clearMatches,
  };
}
