/**
 * Job Grid View Component
 *
 * Displays jobs in a responsive card grid layout with filtering,
 * sorting, and view options. Alternative to table view for better
 * visual browsing experience.
 */

"use client";

import React, { useState, useMemo } from "react";
import { JobCard } from "./JobCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import {
  Grid3x3,
  List,
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobDescription } from "@/lib/types";

interface JobGridViewProps {
  jobs: JobDescription[];
  onJobSelect: (job: JobDescription) => void;
  onJobEdit?: (job: JobDescription) => void;
  onJobDelete?: (job: JobDescription) => void;
  isLoading?: boolean;
  className?: string;
}

type SortOption = "recent" | "title" | "classification" | "quality";
type SortDirection = "asc" | "desc";

export function JobGridView({
  jobs,
  onJobSelect,
  onJobEdit,
  onJobDelete,
  isLoading = false,
  className,
}: JobGridViewProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("recent");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [filters, setFilters] = useState({
    classifications: [] as string[],
    languages: [] as string[],
    hasSkills: false,
  });

  // Extract unique filter options from jobs
  const filterOptions = useMemo(() => {
    const classifications = new Set<string>();
    const languages = new Set<string>();

    jobs.forEach((job) => {
      if (job.classification) classifications.add(job.classification);
      if (job.language) languages.add(job.language);
    });

    return {
      classifications: Array.from(classifications).sort(),
      languages: Array.from(languages).sort(),
    };
  }, [jobs]);

  // Filter and sort jobs
  const filteredAndSortedJobs = useMemo(() => {
    let filtered = [...jobs];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (job) =>
          job.title?.toLowerCase().includes(query) ||
          job.job_number?.toLowerCase().includes(query) ||
          job.classification?.toLowerCase().includes(query) ||
          job.metadata?.department?.toLowerCase().includes(query),
      );
    }

    // Apply classification filter
    if (filters.classifications.length > 0) {
      filtered = filtered.filter((job) =>
        filters.classifications.includes(job.classification || ""),
      );
    }

    // Apply language filter
    if (filters.languages.length > 0) {
      filtered = filtered.filter((job) =>
        filters.languages.includes(job.language || ""),
      );
    }

    // Apply has skills filter
    if (filters.hasSkills) {
      filtered = filtered.filter((job) => job.skills && job.skills.length > 0);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case "recent":
          comparison =
            new Date(b.created_at || 0).getTime() -
            new Date(a.created_at || 0).getTime();
          break;
        case "title":
          comparison = (a.title || "").localeCompare(b.title || "");
          break;
        case "classification":
          comparison = (a.classification || "").localeCompare(
            b.classification || "",
          );
          break;
        case "quality":
          comparison = (b.quality_score || 0) - (a.quality_score || 0);
          break;
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });

    return filtered;
  }, [jobs, searchQuery, filters, sortBy, sortDirection]);

  // Toggle filter
  const toggleFilter = (
    filterType: "classifications" | "languages",
    value: string,
  ) => {
    setFilters((prev) => {
      const currentValues = prev[filterType];
      const newValues = currentValues.includes(value)
        ? currentValues.filter((v) => v !== value)
        : [...currentValues, value];
      return { ...prev, [filterType]: newValues };
    });
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      classifications: [],
      languages: [],
      hasSkills: false,
    });
    setSearchQuery("");
  };

  // Check if any filters are active
  const hasActiveFilters =
    searchQuery.trim() !== "" ||
    filters.classifications.length > 0 ||
    filters.languages.length > 0 ||
    filters.hasSkills;

  const activeFilterCount =
    (searchQuery.trim() !== "" ? 1 : 0) +
    filters.classifications.length +
    filters.languages.length +
    (filters.hasSkills ? 1 : 0);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search jobs by title, number, classification..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={() => setSearchQuery("")}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>

        {/* Sort */}
        <div className="flex gap-2">
          <Select
            value={sortBy}
            onValueChange={(value) => setSortBy(value as SortOption)}
          >
            <SelectTrigger className="w-[180px]">
              <ArrowUpDown className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">Most Recent</SelectItem>
              <SelectItem value="title">Title (A-Z)</SelectItem>
              <SelectItem value="classification">Classification</SelectItem>
              <SelectItem value="quality">Quality Score</SelectItem>
            </SelectContent>
          </Select>

          {/* Sort Direction Toggle */}
          <Button
            variant="outline"
            size="icon"
            onClick={() =>
              setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"))
            }
            title={sortDirection === "asc" ? "Ascending" : "Descending"}
          >
            <ArrowUpDown
              className={cn(
                "h-4 w-4 transition-transform",
                sortDirection === "desc" && "rotate-180",
              )}
            />
          </Button>
        </div>

        {/* Filters */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="relative">
              <SlidersHorizontal className="mr-2 h-4 w-4" />
              Filters
              {activeFilterCount > 0 && (
                <Badge
                  variant="default"
                  className="ml-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
                >
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel>Filter by Classification</DropdownMenuLabel>
            {filterOptions.classifications.map((classification) => (
              <DropdownMenuCheckboxItem
                key={classification}
                checked={filters.classifications.includes(classification)}
                onCheckedChange={() =>
                  toggleFilter("classifications", classification)
                }
              >
                {classification}
              </DropdownMenuCheckboxItem>
            ))}

            <DropdownMenuSeparator />

            <DropdownMenuLabel>Filter by Language</DropdownMenuLabel>
            {filterOptions.languages.map((language) => (
              <DropdownMenuCheckboxItem
                key={language}
                checked={filters.languages.includes(language)}
                onCheckedChange={() => toggleFilter("languages", language)}
              >
                {language.toUpperCase()}
              </DropdownMenuCheckboxItem>
            ))}

            <DropdownMenuSeparator />

            <DropdownMenuCheckboxItem
              checked={filters.hasSkills}
              onCheckedChange={(checked) =>
                setFilters((prev) => ({ ...prev, hasSkills: checked }))
              }
            >
              Has Skills Data
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* View Mode Toggle */}
        <div className="flex gap-1 border rounded-md">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="sm"
            className="rounded-r-none"
            onClick={() => setViewMode("grid")}
            title="Grid View"
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="sm"
            className="rounded-l-none"
            onClick={() => setViewMode("list")}
            title="List View"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {searchQuery && (
            <Badge variant="secondary" className="gap-1">
              Search: {searchQuery}
              <button
                onClick={() => setSearchQuery("")}
                className="ml-1 hover:text-destructive"
              >
                ×
              </button>
            </Badge>
          )}
          {filters.classifications.map((classification) => (
            <Badge key={classification} variant="secondary" className="gap-1">
              {classification}
              <button
                onClick={() => toggleFilter("classifications", classification)}
                className="ml-1 hover:text-destructive"
              >
                ×
              </button>
            </Badge>
          ))}
          {filters.languages.map((language) => (
            <Badge key={language} variant="secondary" className="gap-1">
              {language.toUpperCase()}
              <button
                onClick={() => toggleFilter("languages", language)}
                className="ml-1 hover:text-destructive"
              >
                ×
              </button>
            </Badge>
          ))}
          {filters.hasSkills && (
            <Badge variant="secondary" className="gap-1">
              Has Skills
              <button
                onClick={() =>
                  setFilters((prev) => ({ ...prev, hasSkills: false }))
                }
                className="ml-1 hover:text-destructive"
              >
                ×
              </button>
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="text-xs h-7"
          >
            Clear all
          </Button>
        </div>
      )}

      {/* Results Count */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Showing {filteredAndSortedJobs.length} of {jobs.length} jobs
        </span>
      </div>

      {/* Grid/List View */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="text-muted-foreground mt-4">Loading jobs...</p>
        </div>
      ) : filteredAndSortedJobs.length === 0 ? (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <p className="text-muted-foreground">
            {hasActiveFilters
              ? "No jobs match your filters"
              : "No jobs available"}
          </p>
          {hasActiveFilters && (
            <Button variant="link" onClick={clearFilters} className="mt-2">
              Clear filters
            </Button>
          )}
        </div>
      ) : (
        <div
          className={cn(
            "transition-all duration-200",
            viewMode === "grid" &&
              "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
            viewMode === "list" && "flex flex-col gap-3",
          )}
        >
          {filteredAndSortedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onSelect={onJobSelect}
              onEdit={onJobEdit}
              onDelete={onJobDelete}
              onView={onJobSelect}
              className={cn(viewMode === "list" && "max-w-full")}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default JobGridView;
