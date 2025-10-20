/**
 * Job Card Component
 *
 * Visual card representation of a job description with key information,
 * skills, and actions. Used in grid view for better visual hierarchy.
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FileText,
  MoreVertical,
  Calendar,
  MapPin,
  Briefcase,
  Languages,
  Edit,
  Trash2,
  ExternalLink,
  Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobDescription } from "@/lib/types";

interface JobCardProps {
  job: JobDescription;
  onSelect?: (job: JobDescription) => void;
  onEdit?: (job: JobDescription) => void;
  onDelete?: (job: JobDescription) => void;
  onView?: (job: JobDescription) => void;
  className?: string;
  showActions?: boolean;
}

export function JobCard({
  job,
  onSelect,
  onEdit,
  onDelete,
  onView,
  className,
  showActions = true,
}: JobCardProps) {
  const formattedDate = job.created_at
    ? new Date(job.created_at).toLocaleDateString("en-CA", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "N/A";

  const skillCount = job.skills?.length || 0;
  const topSkills = job.skills?.slice(0, 3) || [];

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(job);
    }
  };

  return (
    <Card
      className={cn(
        "group relative overflow-hidden transition-all duration-300",
        "hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-700",
        "hover:-translate-y-1 cursor-pointer",
        "focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2",
        className,
      )}
      onClick={handleCardClick}
      role="article"
      aria-label={`Job: ${job.title || `Job ${job.id}`}`}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleCardClick();
        }
      }}
    >
      {/* Quality Score Badge (if available) */}
      {job.quality_score !== undefined && (
        <div className="absolute top-2 right-2 sm:top-3 sm:right-3 z-10">
          <Badge
            variant={job.quality_score >= 80 ? "default" : "secondary"}
            className={cn(
              "text-xs font-semibold shadow-sm",
              job.quality_score >= 80 && "bg-green-500 hover:bg-green-600",
              job.quality_score >= 60 &&
                job.quality_score < 80 &&
                "bg-yellow-500 hover:bg-yellow-600",
              job.quality_score < 60 && "bg-red-500 hover:bg-red-600",
            )}
            aria-label={`Quality score: ${job.quality_score} percent`}
          >
            {job.quality_score}%
          </Badge>
        </div>
      )}

      <CardHeader className="space-y-2 sm:space-y-3 pb-3 sm:pb-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base sm:text-lg font-bold leading-tight line-clamp-2">
              {job.title || `Job ${job.id}`}
            </CardTitle>
            <p className="text-xs sm:text-sm text-muted-foreground mt-1 truncate">
              {job.job_number || "No job number"}
            </p>
          </div>

          {/* Actions Dropdown */}
          {showActions && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreVertical className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {onView && (
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      onView(job);
                    }}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    View Details
                  </DropdownMenuItem>
                )}
                {onEdit && (
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(job);
                    }}
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                )}
                {onDelete && (
                  <DropdownMenuItem
                    className="text-red-600 dark:text-red-400"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(job);
                    }}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        {/* Metadata Row - Enhanced mobile layout */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-muted-foreground">
          {job.classification && (
            <div className="flex items-center gap-1" title="Classification">
              <Briefcase className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
              <span className="font-medium truncate">{job.classification}</span>
            </div>
          )}
          {job.metadata?.location && (
            <div className="flex items-center gap-1" title="Location">
              <MapPin className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
              <span className="truncate">{job.metadata.location}</span>
            </div>
          )}
          {job.language && (
            <div className="flex items-center gap-1" title="Language">
              <Languages className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
              <span className="uppercase">{job.language}</span>
            </div>
          )}
          <div className="flex items-center gap-1 ml-auto" title="Created date">
            <Calendar className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
            <span className="whitespace-nowrap">{formattedDate}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 sm:space-y-4">
        {/* Department/Reports To */}
        {(job.metadata?.department || job.metadata?.reports_to) && (
          <div className="text-sm space-y-1">
            {job.metadata.department && (
              <p className="text-muted-foreground">
                <span className="font-medium">Department:</span>{" "}
                {job.metadata.department}
              </p>
            )}
            {job.metadata.reports_to && (
              <p className="text-muted-foreground">
                <span className="font-medium">Reports to:</span>{" "}
                {job.metadata.reports_to}
              </p>
            )}
          </div>
        )}

        {/* Skills Section - Improved mobile display */}
        {skillCount > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">
                Key Skills
              </span>
              <Badge
                variant="outline"
                className="text-xs"
                aria-label={`${skillCount} total skills`}
              >
                {skillCount} total
              </Badge>
            </div>
            <div className="flex flex-wrap gap-1 sm:gap-1.5">
              {topSkills.map((skill) => (
                <Badge
                  key={skill.id}
                  variant="secondary"
                  className="text-xs whitespace-nowrap"
                  title={`${skill.name} (${Math.round(skill.confidence * 100)}% confidence)`}
                >
                  {skill.name}
                </Badge>
              ))}
              {skillCount > 3 && (
                <Badge variant="outline" className="text-xs whitespace-nowrap">
                  +{skillCount - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Sections Summary */}
        {job.sections && job.sections.length > 0 && (
          <div className="text-xs text-muted-foreground">
            <FileText className="h-3 w-3 inline mr-1" />
            {job.sections.length} section{job.sections.length !== 1 ? "s" : ""}
          </div>
        )}

        {/* Action Button - Enhanced mobile styling */}
        <Button
          variant="outline"
          size="sm"
          className="w-full mt-2 group-hover:bg-blue-50 group-hover:text-blue-700 dark:group-hover:bg-blue-900/20 dark:group-hover:text-blue-400 transition-colors touch-target"
          onClick={(e) => {
            e.stopPropagation();
            if (onView) onView(job);
            else if (onSelect) onSelect(job);
          }}
          aria-label={`View details for ${job.title || `Job ${job.id}`}`}
        >
          <span className="text-xs sm:text-sm">View Details</span>
          <ExternalLink
            className="ml-2 h-3 w-3 flex-shrink-0"
            aria-hidden="true"
          />
        </Button>
      </CardContent>
    </Card>
  );
}

export default JobCard;
