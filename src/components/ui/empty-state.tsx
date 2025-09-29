"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Upload,
  Search,
  Database,
  AlertCircle,
  CheckCircle,
  Filter,
  Users,
  BarChart3,
  FolderOpen,
  Plus,
  ArrowRight,
  RefreshCw,
} from "lucide-react";

// Simple EmptyState interface (for backward compatibility)
interface SimpleEmptyStateProps {
  icon?: "alert" | "file" | "search" | "upload" | "refresh";
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "secondary";
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "secondary";
  };
  className?: string;
}

// Advanced EmptyState interface (type-based)
export interface EmptyStateProps {
  type:
    | "no-jobs"
    | "no-search-results"
    | "no-uploads"
    | "no-sections"
    | "no-comparisons"
    | "no-statistics"
    | "loading-error"
    | "processing-error"
    | "general";
  title?: string;
  description?: string;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "secondary";
    icon?: React.ComponentType<{ className?: string }>;
  }>;
  searchQuery?: string;
  showIllustration?: boolean;
  className?: string;
}

// Union type for backward compatibility
type CombinedEmptyStateProps = SimpleEmptyStateProps | EmptyStateProps;

const simpleIconMap = {
  alert: AlertCircle,
  file: FileText,
  search: Search,
  upload: Upload,
  refresh: RefreshCw,
};

const emptyStateConfig = {
  "no-jobs": {
    icon: Database,
    title: "No Job Descriptions Yet",
    description:
      "Start by uploading your first job description file to build your database.",
    illustration: "📋",
    bgGradient: "from-blue-50 to-indigo-50",
    iconColor: "text-blue-500",
    suggestions: [
      "Upload .txt, .doc, .docx, or .pdf files",
      "Process government job description formats",
      "View processing statistics once uploaded",
    ],
  },
  "no-search-results": {
    icon: Search,
    title: "No Results Found",
    description:
      "We couldn't find any job descriptions matching your search criteria.",
    illustration: "🔍",
    bgGradient: "from-gray-50 to-slate-50",
    iconColor: "text-gray-500",
    suggestions: [
      "Try different search terms or keywords",
      "Clear filters to broaden your search",
      "Check spelling and try synonyms",
    ],
  },
  "no-uploads": {
    icon: Upload,
    title: "Ready to Upload Files",
    description:
      "Drag and drop your job description files here or click to browse.",
    illustration: "📤",
    bgGradient: "from-green-50 to-emerald-50",
    iconColor: "text-green-500",
    suggestions: [
      "Supports multiple file formats (.txt, .doc, .docx, .pdf)",
      "Bulk upload multiple files at once",
      "Automatic processing and text extraction",
    ],
  },
  "no-sections": {
    icon: FileText,
    title: "No Sections Available",
    description:
      "This job description hasn't been processed into sections yet.",
    illustration: "📄",
    bgGradient: "from-orange-50 to-amber-50",
    iconColor: "text-orange-500",
    suggestions: [
      "File may still be processing",
      "Check processing status on the Jobs tab",
      "Some files may need manual review",
    ],
  },
  "no-comparisons": {
    icon: BarChart3,
    title: "Select Jobs to Compare",
    description:
      "Choose two or more job descriptions to see detailed comparisons and similarities.",
    illustration: "📊",
    bgGradient: "from-purple-50 to-violet-50",
    iconColor: "text-purple-500",
    suggestions: [
      "Compare job requirements and qualifications",
      "Analyze skill overlaps and differences",
      "Find similar positions in your database",
    ],
  },
  "no-statistics": {
    icon: BarChart3,
    title: "No Data Available",
    description:
      "Statistics will appear here once you have job descriptions in your database.",
    illustration: "📈",
    bgGradient: "from-teal-50 to-cyan-50",
    iconColor: "text-teal-500",
    suggestions: [
      "Upload job descriptions to see trends",
      "View processing status breakdowns",
      "Analyze classification distributions",
    ],
  },
  "loading-error": {
    icon: AlertCircle,
    title: "Loading Error",
    description: "There was an issue loading the data. Please try again.",
    illustration: "⚠️",
    bgGradient: "from-red-50 to-pink-50",
    iconColor: "text-red-500",
    suggestions: [
      "Check your internet connection",
      "Refresh the page to try again",
      "Contact support if the issue persists",
    ],
  },
  "processing-error": {
    icon: AlertCircle,
    title: "Processing Error",
    description:
      "This item encountered an error during processing and may need attention.",
    illustration: "🔧",
    bgGradient: "from-yellow-50 to-orange-50",
    iconColor: "text-yellow-600",
    suggestions: [
      "Try reprocessing the item",
      "Check the file format is supported",
      "Review error details in the logs",
    ],
  },
  general: {
    icon: FolderOpen,
    title: "Nothing to Show",
    description: "There's nothing to display at the moment.",
    illustration: "📁",
    bgGradient: "from-gray-50 to-neutral-50",
    iconColor: "text-gray-400",
    suggestions: [],
  },
};

// Type guard to check if props have 'type' property (advanced mode)
function isAdvancedEmptyState(
  props: CombinedEmptyStateProps,
): props is EmptyStateProps {
  return "type" in props;
}

export function EmptyState(props: CombinedEmptyStateProps) {
  // Handle advanced type-based EmptyState
  if (isAdvancedEmptyState(props)) {
    const {
      type,
      title,
      description,
      actions = [],
      searchQuery,
      showIllustration = true,
      className = "",
    } = props;

    // Get configuration with fallback
    const config =
      emptyStateConfig[type as keyof typeof emptyStateConfig] ||
      emptyStateConfig.general;

    // Additional safety check - ensure we always have a valid config
    const finalConfig =
      config && typeof config.icon === "function"
        ? config
        : {
            icon: FolderOpen,
            title: "Nothing to Show",
            description: "There's nothing to display at the moment.",
            illustration: "📁",
            bgGradient: "from-gray-50 to-neutral-50",
            iconColor: "text-gray-400",
            suggestions: [],
          };

    const IconComponent = finalConfig.icon;

    const displayTitle = title || finalConfig.title;
    const displayDescription =
      description ||
      (type === "no-search-results" && searchQuery
        ? `No job descriptions found for "${searchQuery}".`
        : finalConfig.description);

    return (
      <Card className={`border-dashed border-2 ${className}`}>
        <CardContent className="pt-8 pb-8">
          <div
            className={`bg-gradient-to-br ${finalConfig.bgGradient} rounded-lg p-8`}
          >
            <div className="text-center space-y-4">
              {/* Illustration and Icon */}
              <div className="flex flex-col items-center space-y-3">
                {showIllustration && (
                  <div className="text-4xl opacity-50 mb-2">
                    {finalConfig.illustration}
                  </div>
                )}
                <div className={`p-3 rounded-full bg-white shadow-sm`}>
                  <IconComponent
                    className={`w-8 h-8 ${finalConfig.iconColor}`}
                  />
                </div>
              </div>

              {/* Title and Description */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  {displayTitle}
                </h3>
                <p className="text-gray-600 max-w-md mx-auto">
                  {displayDescription}
                </p>
              </div>

              {/* Suggestions */}
              {finalConfig.suggestions.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Helpful Tips:
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {finalConfig.suggestions.map((suggestion, index) => (
                      <li
                        key={index}
                        className="flex items-center justify-center"
                      >
                        <CheckCircle className="w-3 h-3 text-green-500 mr-2 flex-shrink-0" />
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons */}
              {actions.length > 0 && (
                <div className="flex flex-wrap gap-2 justify-center pt-4">
                  {actions.map((action, index) => {
                    const IconComp = action.icon;
                    return (
                      <Button
                        key={index}
                        variant={action.variant || "default"}
                        onClick={action.onClick}
                        className="flex items-center gap-2"
                      >
                        {IconComp && <IconComp className="w-4 h-4" />}
                        {action.label}
                      </Button>
                    );
                  })}
                </div>
              )}

              {/* Quick Actions for specific types */}
              {type === "no-jobs" && actions.length === 0 && (
                <div className="flex flex-col sm:flex-row gap-2 justify-center pt-4">
                  <Button className="flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    Upload Files
                  </Button>
                  <Button variant="outline" className="flex items-center gap-2">
                    <Plus className="w-4 h-4" />
                    Learn More
                  </Button>
                </div>
              )}

              {type === "no-search-results" && actions.length === 0 && (
                <div className="flex flex-col sm:flex-row gap-2 justify-center pt-4">
                  <Button variant="outline" className="flex items-center gap-2">
                    <Filter className="w-4 h-4" />
                    Clear Filters
                  </Button>
                  <Button variant="outline" className="flex items-center gap-2">
                    <Search className="w-4 h-4" />
                    Browse All Jobs
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle simple icon-based EmptyState (backward compatibility)
  const {
    icon = "alert",
    title,
    description,
    action,
    secondaryAction,
    className = "",
  } = props;

  const IconComponent = simpleIconMap[icon];

  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <div className="text-center py-8">
          <div className="mx-auto w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <IconComponent className="h-8 w-8 text-gray-400" />
          </div>

          <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>

          <p className="text-gray-500 mb-6 max-w-sm mx-auto">{description}</p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {action && (
              <Button
                onClick={action.onClick}
                variant={action.variant || "default"}
                className="min-w-[120px]"
              >
                {action.label}
              </Button>
            )}

            {secondaryAction && (
              <Button
                onClick={secondaryAction.onClick}
                variant={secondaryAction.variant || "outline"}
                className="min-w-[120px]"
              >
                {secondaryAction.label}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default EmptyState;
