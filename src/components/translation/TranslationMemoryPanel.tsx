import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Search,
  BookOpen,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Star,
  TrendingUp,
  Languages,
  Zap,
  Clock,
  AlertCircle,
} from "lucide-react";
import {
  useTranslationMemory,
  TranslationMatch,
} from "@/hooks/useTranslationMemory";

interface TranslationMemoryPanelProps {
  sourceLanguage: string;
  targetLanguage: string;
  onMatchSelect?: (match: TranslationMatch) => void;
  className?: string;
  autoSearch?: boolean;
  initialSearchText?: string;
}

export const TranslationMemoryPanel: React.FC<TranslationMemoryPanelProps> = ({
  sourceLanguage,
  targetLanguage,
  onMatchSelect,
  className,
  autoSearch = false,
  initialSearchText = "",
}) => {
  const [searchQuery, setSearchQuery] = useState(initialSearchText);
  const [selectedMatch, setSelectedMatch] = useState<number | null>(null);
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(
    null,
  );

  // Use the real translation memory hook
  const {
    matches,
    isLoading,
    error,
    searchTranslations,
    rateTranslation,
    clearMatches,
  } = useTranslationMemory({
    sourceLanguage,
    targetLanguage,
    minSimilarity: 0.7,
    autoSearch,
  });

  // Debounced search function
  const performSearch = useCallback(
    (query: string) => {
      if (query.trim().length < 3) {
        clearMatches();
        return;
      }

      searchTranslations({
        source_text: query,
        source_language: sourceLanguage,
        target_language: targetLanguage,
        min_similarity: 0.7,
        domain: "job_descriptions",
        limit: 20,
      });
    },
    [searchTranslations, clearMatches, sourceLanguage, targetLanguage],
  );

  // Handle search query changes with debouncing
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);

    // Clear previous timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Set new timer for debounced search
    const timer = setTimeout(() => {
      performSearch(value);
    }, 500); // 500ms debounce

    setDebounceTimer(timer);
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [debounceTimer]);

  // Perform initial search if autoSearch is enabled
  useEffect(() => {
    if (autoSearch && initialSearchText.length >= 3) {
      performSearch(initialSearchText);
    }
  }, [autoSearch, initialSearchText, performSearch]);

  const handleMatchSelect = (match: TranslationMatch) => {
    setSelectedMatch(match.id);
    onMatchSelect?.(match);
  };

  const handleApproval = async (matchId: number, approved: boolean) => {
    try {
      // Rate translation: 5 stars for approved, 1 star for rejected
      await rateTranslation(matchId, approved ? 5 : 1);
      console.log(`Match ${matchId} ${approved ? "approved" : "rejected"}`);
    } catch (err) {
      console.error("Error rating translation:", err);
    }
  };

  const handleCopyTranslation = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleRefresh = () => {
    if (searchQuery.trim().length >= 3) {
      performSearch(searchQuery);
    }
  };

  const formatLastUsed = (dateString?: string) => {
    if (!dateString) return "Never used";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getMatchTypeColor = (matchType: string, confidence: number) => {
    if (matchType === "exact") return "bg-green-500";
    if (confidence > 0.9) return "bg-blue-500";
    if (confidence > 0.8) return "bg-yellow-500";
    return "bg-gray-500";
  };

  const getQualityStars = (score?: number) => {
    if (!score) return null;
    const stars = Math.round(score * 5);
    return (
      <div className="flex items-center gap-1">
        {Array.from({ length: 5 }, (_, i) => (
          <Star
            key={i}
            className={`w-3 h-3 ${
              i < stars ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <Card className={`flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          Translation Memory
          <Badge variant="outline" className="ml-auto">
            {sourceLanguage.toUpperCase()} → {targetLanguage.toUpperCase()}
          </Badge>
        </CardTitle>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search translations (min 3 chars)..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10 h-8"
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 p-2 rounded">
            <AlertCircle className="w-3 h-3" />
            <span>{error}</span>
          </div>
        )}

        {/* Statistics */}
        {matches.length > 0 && (
          <div className="flex items-center gap-4 text-xs text-gray-600">
            <div className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {matches.length} entries
            </div>
            <div className="flex items-center gap-1">
              <Languages className="w-3 h-3" />
              {matches.filter((m) => m.match_type === "exact").length} exact
            </div>
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {matches.length > 0
                ? Math.round(
                    (matches.reduce(
                      (sum, m) => sum + (m.quality_score || 0),
                      0,
                    ) /
                      matches.length) *
                      100,
                  )
                : 0}
              % avg
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0 flex-1 flex flex-col">
        <ScrollArea className="flex-1">
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50 animate-pulse" />
              <p className="text-sm">Searching translation memory...</p>
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">
                {searchQuery.trim().length < 3
                  ? "Enter at least 3 characters to search"
                  : "No translation matches found"}
              </p>
              {searchQuery.trim().length >= 3 && (
                <p className="text-xs mt-1">Try different search terms</p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {matches.map((match) => (
                <TranslationMatchCard
                  key={match.id}
                  match={match}
                  isSelected={selectedMatch === match.id}
                  onSelect={() => handleMatchSelect(match)}
                  onApproval={(approved) => handleApproval(match.id, approved)}
                  onCopy={() => handleCopyTranslation(match.target_text)}
                  formatLastUsed={formatLastUsed}
                  getMatchTypeColor={getMatchTypeColor}
                  getQualityStars={getQualityStars}
                />
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Quick actions */}
        <Separator className="my-3" />
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {matches.length > 0 && matches[0]?.last_used
              ? `Last updated: ${formatLastUsed(matches[0].last_used)}`
              : "No recent activity"}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={handleRefresh}
            disabled={isLoading || searchQuery.trim().length < 3}
          >
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const TranslationMatchCard: React.FC<{
  match: TranslationMatch;
  isSelected: boolean;
  onSelect: () => void;
  onApproval: (approved: boolean) => void;
  onCopy: () => void;
  formatLastUsed: (date?: string) => string;
  getMatchTypeColor: (type: string, confidence: number) => string;
  getQualityStars: (score?: number) => React.ReactNode;
}> = ({
  match,
  isSelected,
  onSelect,
  onApproval,
  onCopy,
  formatLastUsed,
  getMatchTypeColor,
  getQualityStars,
}) => (
  <div
    className={`border rounded-lg p-3 space-y-2 cursor-pointer transition-all hover:shadow-md ${
      isSelected ? "ring-2 ring-blue-500 bg-blue-50" : "hover:bg-gray-50"
    }`}
    onClick={onSelect}
  >
    {/* Header */}
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${getMatchTypeColor(match.match_type, match.confidence)}`}
        />
        <Badge
          variant={match.match_type === "exact" ? "default" : "secondary"}
          className="text-xs"
        >
          {match.match_type === "exact"
            ? "Exact"
            : `${Math.round(match.confidence * 100)}%`}
        </Badge>
        {match.domain && (
          <Badge variant="outline" className="text-xs">
            {match.domain}
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-1">
        {getQualityStars(match.quality_score)}
      </div>
    </div>

    {/* Source Text */}
    <div className="space-y-1">
      <div className="text-xs text-gray-500">Source:</div>
      <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
        {match.source_text}
      </div>
    </div>

    {/* Target Text */}
    <div className="space-y-1">
      <div className="text-xs text-gray-500">Translation:</div>
      <div className="text-sm text-gray-900 bg-blue-50 p-2 rounded">
        {match.target_text}
      </div>
    </div>

    {/* Metadata */}
    <div className="flex items-center justify-between text-xs text-gray-500">
      <div className="flex items-center gap-3">
        <span>Used {match.usage_count} times</span>
        <span>Last: {formatLastUsed(match.last_used)}</span>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={(e) => {
            e.stopPropagation();
            onCopy();
          }}
        >
          <Copy className="w-3 h-3" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-green-600 hover:text-green-700"
          onClick={(e) => {
            e.stopPropagation();
            onApproval(true);
          }}
        >
          <ThumbsUp className="w-3 h-3" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
          onClick={(e) => {
            e.stopPropagation();
            onApproval(false);
          }}
        >
          <ThumbsDown className="w-3 h-3" />
        </Button>
      </div>
    </div>
  </div>
);
