"use client";

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { SearchQuery, SearchResult, JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import {
  getClassificationLevel,
  getLanguageName,
  handleExport,
} from "@/lib/utils";
import {
  Search,
  Filter,
  X,
  Loader2,
  AlertCircle,
  Eye,
  Download,
  FileText,
  Lightbulb,
  TrendingUp,
} from "lucide-react";

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

export function SearchInterface({ onJobSelect }: SearchInterfaceProps) {
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
      setError(err instanceof Error ? err.message : "Search failed");
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
            Advanced Search
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
                    placeholder="Search job descriptions, titles, responsibilities..."
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
                  Search
                </Button>
              </div>
            </div>

            {/* Filters */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Filter className="w-4 h-4 mr-2 text-gray-400" />
                  <span className="text-sm font-medium">Filters</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="text-gray-500"
                >
                  <X className="w-4 h-4 mr-1" />
                  Clear All
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Classification Filter */}
                <div>
                  <label className="text-sm font-medium text-gray-600 mb-2 block">
                    Classification
                  </label>
                  <select
                    aria-label="Classification"
                    title="Classification"
                    value={searchFilters.classification || ""}
                    onChange={(e) =>
                      handleFilterChange("classification", e.target.value)
                    }
                    className="w-full border rounded px-3 py-2 text-sm"
                  >
                    <option value="">All Classifications</option>
                    {facets?.classifications.map((classification) => (
                      <option
                        key={classification.value}
                        value={classification.value}
                      >
                        {classification.value} ({classification.count})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Language Filter */}
                <div>
                  <label className="text-sm font-medium text-gray-600 mb-2 block">
                    Language
                  </label>
                  <select
                    aria-label="Language"
                    title="Language"
                    value={searchFilters.language || ""}
                    onChange={(e) =>
                      handleFilterChange("language", e.target.value)
                    }
                    className="w-full border rounded px-3 py-2 text-sm"
                  >
                    <option value="">All Languages</option>
                    {facets?.languages.map((language) => (
                      <option key={language.value} value={language.value}>
                        {getLanguageName(language.value)} ({language.count})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Department Filter */}
                <div>
                  <label className="text-sm font-medium text-gray-600 mb-2 block">
                    Department
                  </label>
                  <Input
                    placeholder="Filter by department..."
                    value={searchFilters.department || ""}
                    onChange={(e) =>
                      handleFilterChange("department", e.target.value)
                    }
                  />
                </div>
              </div>

              {/* Section Type Filters */}
              {facets?.section_types && facets.section_types.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-600 mb-2 block">
                    Search in Sections
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {facets.section_types.map((sectionType) => (
                      <Badge
                        key={sectionType.value}
                        variant={
                          selectedSectionTypes.includes(sectionType.value)
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer"
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
            </div>
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
                Search Results {totalResults > 0 && `(${totalResults} found)`}
              </span>
              {totalResults > 0 && (
                <Badge variant="secondary" className="flex items-center">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  Sorted by relevance
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Searching...
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
                            <Badge variant="outline">
                              {result.classification}
                            </Badge>
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
                                Matching sections:
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
                            View
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
                            Export
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              !loading && (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <p>No job descriptions found matching your search.</p>
                  <p className="text-sm mt-2">
                    Try adjusting your search terms or filters.
                  </p>
                </div>
              )
            )}
          </CardContent>
        </Card>
      )}

      {/* Initial State */}
      {!hasSearched && !loading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12 text-gray-500">
              <Search className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium mb-2">Advanced Job Search</h3>
              <p className="mb-4">
                Search through job descriptions using keywords, classifications,
                and filters.
              </p>
              <div className="text-sm space-y-1">
                <p>• Full-text search across all job content</p>
                <p>• Filter by classification, language, and department</p>
                <p>• Search within specific sections</p>
                <p>• Smart suggestions as you type</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default React.memo(SearchInterface);
