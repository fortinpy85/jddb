/**
 * Visual Job Selection Component
 * Provides an intuitive card-based interface for selecting jobs in comparison workflows
 */

"use client";

import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  Search,
  CheckCircle,
  FileText,
  Calendar,
  Globe,
  Building,
  Filter,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { JobDescription } from "@/lib/types";

interface JobSelectorProps {
  jobs: JobDescription[];
  selectedJob: JobDescription | null;
  onJobSelect: (job: JobDescription | null) => void;
  placeholder?: string;
  title?: string;
  className?: string;
  variant?: "primary" | "secondary" | "comparison";
  showSuggestions?: JobDescription[];
  onClearSelection?: () => void;
  maxHeight?: string;
}

export function JobSelector({
  jobs,
  selectedJob,
  onJobSelect,
  placeholder = "Select a job description",
  title,
  className,
  variant = "primary",
  showSuggestions = [] as JobDescription[],
  onClearSelection,
  maxHeight = "400px"
}: JobSelectorProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [classificationFilter, setClassificationFilter] = useState("");
  const [languageFilter, setLanguageFilter] = useState("");

  // Get variant-specific styles
  const getVariantStyles = () => {
    switch (variant) {
      case "primary":
        return {
          border: "border-blue-200",
          bg: "bg-blue-50",
          accent: "text-blue-700",
          selectedBg: "bg-blue-100",
          selectedBorder: "border-blue-300"
        };
      case "secondary":
        return {
          border: "border-green-200",
          bg: "bg-green-50",
          accent: "text-green-700",
          selectedBg: "bg-green-100",
          selectedBorder: "border-green-300"
        };
      case "comparison":
        return {
          border: "border-purple-200",
          bg: "bg-purple-50",
          accent: "text-purple-700",
          selectedBg: "bg-purple-100",
          selectedBorder: "border-purple-300"
        };
    }
  };

  const styles = getVariantStyles();

  // Filter and search logic
  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const matchesSearch =
        job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.job_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.classification.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesClassification = !classificationFilter ||
        job.classification.toLowerCase().includes(classificationFilter.toLowerCase());

      const matchesLanguage = !languageFilter ||
        job.language.toLowerCase().includes(languageFilter.toLowerCase());

      return matchesSearch && matchesClassification && matchesLanguage;
    });
  }, [jobs, searchTerm, classificationFilter, languageFilter]);

  // Get unique values for filters
  const uniqueClassifications = useMemo(() =>
    [...new Set(jobs.map(job => job.classification))].sort(),
    [jobs]
  );

  const uniqueLanguages = useMemo(() =>
    [...new Set(jobs.map(job => job.language))].sort(),
    [jobs]
  );

  const clearFilters = () => {
    setSearchTerm("");
    setClassificationFilter("");
    setLanguageFilter("");
  };

  const handleJobClick = (job: JobDescription) => {
    if (selectedJob && selectedJob.id === job.id) {
      // Deselect if already selected
      onJobSelect(null);
    } else {
      onJobSelect(job);
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      {title && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h3>
          {selectedJob && onClearSelection && (
            <Button
              variant="outline"
              size="sm"
              onClick={onClearSelection}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          )}
        </div>
      )}

      {/* Selected Job Display */}
      {selectedJob && (
        <Card className={cn("border-2", styles.selectedBorder, styles.selectedBg)}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <CheckCircle className={cn("w-5 h-5", styles.accent)} />
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                    Selected: {selectedJob.title}
                  </h4>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center space-x-1">
                    <FileText className="w-4 h-4" />
                    <span>{selectedJob.job_number}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Building className="w-4 h-4" />
                    <span>{selectedJob.classification}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Globe className="w-4 h-4" />
                    <span>{selectedJob.language}</span>
                  </div>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onJobSelect(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <div className="space-y-3">
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder={placeholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filters Toggle */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="text-gray-600 dark:text-gray-400"
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            {showFilters ? (
              <ChevronUp className="w-4 h-4 ml-2" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-2" />
            )}
          </Button>

          {(searchTerm || classificationFilter || languageFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="text-gray-500 hover:text-gray-700"
            >
              Clear filters
            </Button>
          )}
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">
                Classification
              </label>
              <select
                value={classificationFilter}
                onChange={(e) => setClassificationFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700"
              >
                <option value="">All Classifications</option>
                {uniqueClassifications.map(classification => (
                  <option key={classification} value={classification}>
                    {classification}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">
                Language
              </label>
              <select
                value={languageFilter}
                onChange={(e) => setLanguageFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700"
              >
                <option value="">All Languages</option>
                {uniqueLanguages.map(language => (
                  <option key={language} value={language}>
                    {language}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Suggestions Section */}
      {showSuggestions.length > 0 && !selectedJob && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
            <FileText className="w-4 h-4 mr-2" />
            Suggested Jobs
          </h4>
          <div className="grid grid-cols-1 gap-2">
            {showSuggestions.slice(0, 3).map((job: JobDescription) => (
              <JobCard
                key={job.id}
                job={job}
                onClick={() => handleJobClick(job)}
                isSelected={selectedJob !== null && job.id === selectedJob.id}
                variant={variant}
                size="compact"
              />
            ))}
          </div>
        </div>
      )}

      {/* Jobs List */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {filteredJobs.length === jobs.length
              ? `All Jobs (${jobs.length})`
              : `Filtered Jobs (${filteredJobs.length} of ${jobs.length})`}
          </h4>
          {filteredJobs.length > 10 && (
            <span className="text-xs text-gray-500">
              Showing first 10 results
            </span>
          )}
        </div>

        <ScrollArea style={{ height: maxHeight }}>
          <div className="space-y-2 pr-4">
            {filteredJobs.length > 0 ? (
              filteredJobs.slice(0, 10).map((job: JobDescription) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onClick={() => handleJobClick(job)}
                  isSelected={selectedJob !== null && job.id === selectedJob.id}
                  variant={variant}
                />
              ))
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No jobs match your search criteria</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="mt-2"
                >
                  Clear filters to see all jobs
                </Button>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

interface JobCardProps {
  job: JobDescription;
  onClick: () => void;
  isSelected: boolean;
  variant: "primary" | "secondary" | "comparison";
  size?: "default" | "compact";
}

function JobCard({ job, onClick, isSelected, variant, size = "default" }: JobCardProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case "primary":
        return {
          border: "border-blue-200 hover:border-blue-300",
          selectedBorder: "border-blue-400 bg-blue-50",
          accent: "text-blue-600"
        };
      case "secondary":
        return {
          border: "border-green-200 hover:border-green-300",
          selectedBorder: "border-green-400 bg-green-50",
          accent: "text-green-600"
        };
      case "comparison":
        return {
          border: "border-purple-200 hover:border-purple-300",
          selectedBorder: "border-purple-400 bg-purple-50",
          accent: "text-purple-600"
        };
    }
  };

  const styles = getVariantStyles();
  const isCompact = size === "compact";

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all duration-200 hover:shadow-md",
        isSelected
          ? styles.selectedBorder
          : `border ${styles.border}`,
        "hover:scale-[1.02]"
      )}
      onClick={onClick}
    >
      <CardContent className={cn("p-3", isCompact && "p-2")}>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              {isSelected && (
                <CheckCircle className={cn("w-4 h-4 flex-shrink-0", styles.accent)} />
              )}
              <h4 className={cn(
                "font-semibold text-gray-900 dark:text-gray-100 truncate",
                isCompact ? "text-sm" : "text-base"
              )}>
                {job.title}
              </h4>
            </div>

            <div className={cn(
              "flex items-center space-x-3 text-gray-600 dark:text-gray-400",
              isCompact ? "text-xs" : "text-sm"
            )}>
              <div className="flex items-center space-x-1">
                <FileText className="w-3 h-3" />
                <span className="truncate">{job.job_number}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Building className="w-3 h-3" />
                <span className="truncate">{job.classification}</span>
              </div>
              <Badge variant="outline" className="text-xs">
                {job.language}
              </Badge>
            </div>

            {!isCompact && job.created_at && (
              <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400 mt-1">
                <Calendar className="w-3 h-3" />
                <span>
                  {new Date(job.created_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}