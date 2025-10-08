"use client";

import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ClassificationBadge } from "@/components/ui/classification-badge";
import { FilterBar } from "@/components/ui/filter-bar";
import type { SearchQuery, SearchResult, JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import {
  getClassificationLevel,
  getLanguageName,
  handleExport,
} from "@/lib/utils";
import {
  Search,
  Loader2,
  AlertCircle,
  Eye,
  Download,
  FileText,
  Lightbulb,
  TrendingUp,
} from "lucide-react";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import { EmptyState } from "@/components/ui/empty-state";

interface SearchInterfaceProps {
  onJobSelect?: (job: JobDescription) => void;
}

interface SearchFacets {
  classifications: Array<{ value: string; count: number }>;
  languages: Array<{ value: string; count: number }>;
  section_types: Array<{ value: string; count: number }>;
}

interface SearchSuggestions {
  query: string;
  suggestions: string[];
}

function SearchInterface({ onJobSelect }: SearchInterfaceProps) {
  const { t } = useTranslation(["jobs", "common"]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFilters, setSearchFilters] = useState<{
    classification?: string;
    language?: string;
    department?: string;
    section_types?: string[];
  }>({});
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [facets, setFacets] = useState<SearchFacets | null>(null);
  const [suggestions, setSuggestions] = useState<SearchSuggestions | null>(
    null,
  );
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedSectionTypes, setSelectedSectionTypes] = useState<string[]>(
    [],
  );

  const searchInputRef = useRef<HTMLInputElement>(null);
  const suggestionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );

  // Load facets on mount
  useEffect(() => {
    loadFacets();
  }, []);

  // Handle search input changes for suggestions
  useEffect(() => {
    if (suggestionTimeoutRef.current) {
      clearTimeout(suggestionTimeoutRef.current);
    }

    if (searchQuery.length >= 2) {
      suggestionTimeoutRef.current = setTimeout(() => {
        loadSuggestions(searchQuery);
      }, 300);
    } else {
      setSuggestions(null);
      setShowSuggestions(false);
    }

    return () => {
      if (suggestionTimeoutRef.current) {
        clearTimeout(suggestionTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const loadFacets = async () => {
    try {
      const facetData = await apiClient.getSearchFacets();
      setFacets(facetData);
    } catch (err) {
      console.error("Failed to load facets:", err);
    }
  };

  const loadSuggestions = async (query: string) => {
    try {
      const suggestionData = await apiClient.getSearchSuggestions(query, 8);
      setSuggestions(suggestionData);
      setShowSuggestions(true);
    } catch (err) {
      console.error("Failed to load suggestions:", err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setShowSuggestions(false);
    setHasSearched(true);

    try {
      const searchParams: SearchQuery = {
        query: searchQuery.trim(),
        classification: searchFilters.classification,
        language: searchFilters.language,
        department: searchFilters.department,
        section_types:
          selectedSectionTypes.length > 0 ? selectedSectionTypes : undefined,
        limit: 50,
      };

      const response = await apiClient.searchJobs(searchParams);
      setResults(response.results || []);
      setTotalResults(response.total_results || 0);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t("jobs:search.searchFailed"),
      );
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setSearchFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }));
  };

  const handleSectionTypeToggle = (sectionType: string) => {
    setSelectedSectionTypes((prev) =>
      prev.includes(sectionType)
        ? prev.filter((type) => type !== sectionType)
        : [...prev, sectionType],
    );
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    setShowSuggestions(false);
    // Trigger search with the selected suggestion
    setTimeout(() => {
      const input = searchInputRef.current;
      if (input) {
        input.focus();
        handleSearch();
      }
    }, 100);
  };

  const clearFilters = () => {
    setSearchFilters({});
    setSelectedSectionTypes([]);
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="w-5 h-5 mr-2" />
            {t("jobs:search.advancedSearch")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Search Input with Suggestions */}
          <div className="space-y-4">
            <div className="relative">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    ref={searchInputRef}
                    placeholder={t("jobs:search.placeholder")}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleSearch();
                      } else if (e.key === "Escape") {
                        setShowSuggestions(false);
                      }
                    }}
                    onFocus={() => {
                      if (
                        suggestions &&
                        suggestions.suggestions &&
                        suggestions.suggestions.length > 0
                      ) {
                        setShowSuggestions(true);
                      }
                    }}
                    className="pl-10"
                  />

                  {/* Search Suggestions */}
                  {showSuggestions &&
                    suggestions &&
                    suggestions.suggestions &&
                    suggestions.suggestions.length > 0 && (
                      <div className="absolute z-10 w-full bg-white border rounded-md shadow-lg mt-1 max-h-60 overflow-y-auto">
                        {suggestions.suggestions.map((suggestion, index) => (
                          <div
                            key={index}
                            className="px-4 py-2 hover:bg-gray-50 cursor-pointer flex items-center"
                            onClick={() => handleSuggestionClick(suggestion)}
                          >
                            <Lightbulb className="w-4 h-4 mr-2 text-gray-400" />
                            {suggestion}
                          </div>
                        ))}
                      </div>
                    )}
                </div>

                <Button
                  onClick={handleSearch}
                  disabled={loading || !searchQuery.trim()}
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Search className="w-4 h-4 mr-2" />
                  )}
                  {t("jobs:actions.search")}
                </Button>
              </div>
            </div>

            {/* Filters */}
            <FilterBar
              filters={[
                {
                  id: "classification",
                  label: t("jobs:filters.classificationLabel"),
                  placeholder: t("jobs:filters.allClassifications"),
                  value: searchFilters.classification || "",
                  options: [
                    ...(facets?.classifications.map((c) => ({
                      value: c.value,
                      label: c.value,
                      count: c.count,
                    })) || []),
                  ],
                  onChange: (value) =>
                    handleFilterChange("classification", value),
                },
                {
                  id: "language",
                  label: t("jobs:filters.languageLabel"),
                  placeholder: t("jobs:filters.allLanguages"),
                  value: searchFilters.language || "",
                  options: [
                    ...(facets?.languages.map((lang) => ({
                      value: lang.value,
                      label: getLanguageName(lang.value),
                      count: lang.count,
                    })) || []),
                  ],
                  onChange: (value) => handleFilterChange("language", value),
                },
              ]}
              onClearAll={clearFilters}
            >
              {/* Department Filter - Custom Input */}
              <div className="w-full sm:w-64">
                <Input
                  placeholder={t("jobs:filters.departmentPlaceholder")}
                  value={searchFilters.department || ""}
                  onChange={(e) =>
                    handleFilterChange("department", e.target.value)
                  }
                  className="shadow-input"
                />
              </div>

              {/* Section Type Filters */}
              {facets?.section_types && facets.section_types.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-600 mb-2 block">
                    {t("jobs:search.searchInSections")}
                  </label>
                  <div className="flex flex-wrap gap-2 overflow-hidden max-w-full">
                    {facets.section_types.map((sectionType) => (
                      <Badge
                        key={sectionType.value}
                        variant={
                          selectedSectionTypes.includes(sectionType.value)
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer break-words max-w-full"
                        onClick={() =>
                          handleSectionTypeToggle(sectionType.value)
                        }
                      >
                        {sectionType.value
                          .replace(/_/g, " ")
                          .replace(/\b\w/g, (l) => l.toUpperCase())}{" "}
                        ({sectionType.count})
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </FilterBar>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center text-red-600">
              <AlertCircle className="w-5 h-5 mr-2" />
              {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Results */}
      {hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>
                {t("jobs:search.results")}{" "}
                {totalResults > 0 &&
                  `(${totalResults} ${t("jobs:search.found")})`}
              </span>
              {totalResults > 0 && (
                <Badge variant="secondary" className="flex items-center">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  {t("jobs:search.sortedByRelevance")}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                {t("jobs:search.searching")}...
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-4">
                {results.map((result) => (
                  <Card
                    key={result.job_id}
                    className="hover:shadow-md transition-shadow"
                  >
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold">
                              {result.title}
                            </h3>
                            <Badge variant="secondary">
                              {result.job_number}
                            </Badge>
                            <ClassificationBadge
                              code={result.classification}
                              showHelpIcon
                            />
                            <Badge variant="outline">
                              {getLanguageName(result.language)}
                            </Badge>
                            <Badge className="bg-blue-100 text-blue-800">
                              {Math.round(result.relevance_score * 100)}% match
                            </Badge>
                          </div>

                          <p className="text-sm text-gray-600 mb-2">
                            {getClassificationLevel(result.classification)}
                          </p>

                          {/* Search Snippet */}
                          <div className="bg-gray-50 p-3 rounded text-sm mb-2">
                            <p className="text-gray-700">{result.snippet}</p>
                          </div>

                          {/* Matching Sections */}
                          {result.matching_sections.length > 0 && (
                            <div className="space-y-2">
                              <p className="text-sm font-medium text-gray-600">
                                {t("jobs:search.matchingSections")}:
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {result.matching_sections.map(
                                  (section, index) => (
                                    <Badge
                                      key={index}
                                      variant="outline"
                                      className="text-xs"
                                    >
                                      {section.section_type
                                        .replace(/_/g, " ")
                                        .replace(/\b\w/g, (l) =>
                                          l.toUpperCase(),
                                        )}
                                    </Badge>
                                  ),
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              // Convert SearchResult to JobDescription for compatibility
                              if (onJobSelect) {
                                const job: JobDescription = {
                                  id: result.job_id,
                                  job_number: result.job_number,
                                  title: result.title,
                                  classification: result.classification,
                                  language: result.language,
                                  file_path: "",
                                  file_hash: "",
                                  processed_date: new Date().toISOString(),
                                  created_at: new Date().toISOString(),
                                  updated_at: new Date().toISOString(),
                                };
                                onJobSelect(job);
                              }
                            }}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            {t("jobs:actions.view")}
                          </Button>

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const job: JobDescription = {
                                id: result.job_id,
                                job_number: result.job_number,
                                title: result.title,
                                classification: result.classification,
                                language: result.language,
                                file_path: "",
                                file_hash: "",
                                processed_date: new Date().toISOString(),
                                created_at: new Date().toISOString(),
                                updated_at: new Date().toISOString(),
                              };
                              handleExport(job);
                            }}
                          >
                            <Download className="w-4 h-4 mr-1" />
                            {t("jobs:actions.export")}
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              !loading && (
                <EmptyState
                  type="no-search-results"
                  searchQuery={searchQuery}
                />
              )
            )}
          </CardContent>
        </Card>
      )}

      {/* Initial State */}
      {!hasSearched && !loading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12 text-gray-600 dark:text-gray-400">
              <Search className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
              <h3 className="text-lg font-medium mb-2">
                {t("jobs:search.advancedSearch")}
              </h3>
              <p className="mb-4">{t("jobs:search.description")}</p>
              <div className="text-sm space-y-1">
                <p>• {t("jobs:search.features.fullText")}</p>
                <p>• {t("jobs:search.features.filterBy")}</p>
                <p>• {t("jobs:search.features.searchSections")}</p>
                <p>• {t("jobs:search.features.smartSuggestions")}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Wrap with error boundary for reliability
const SearchInterfaceWithErrorBoundary = (props: SearchInterfaceProps) => (
  <ErrorBoundaryWrapper>
    <SearchInterface {...props} />
  </ErrorBoundaryWrapper>
);

export { SearchInterfaceWithErrorBoundary as SearchInterface };
export default React.memo(SearchInterfaceWithErrorBoundary);
