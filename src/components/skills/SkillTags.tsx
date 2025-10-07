/**
 * Skill Tags Component
 * Displays extracted skills as colored tags with confidence indicators
 */

"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip } from "@/components/ui/tooltip";
import type { Skill } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SkillTagsProps {
  skills: Skill[];
  maxDisplay?: number;
  showConfidence?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function SkillTags({
  skills,
  maxDisplay,
  showConfidence = true,
  size = "md",
  className,
}: SkillTagsProps) {
  if (!skills || skills.length === 0) {
    return (
      <div className={cn("text-sm text-muted-foreground italic", className)}>
        No skills extracted yet
      </div>
    );
  }

  // Sort by confidence score (highest first)
  const sortedSkills = [...skills].sort((a, b) => b.confidence - a.confidence);
  const displaySkills = maxDisplay
    ? sortedSkills.slice(0, maxDisplay)
    : sortedSkills;
  const remainingCount = sortedSkills.length - displaySkills.length;

  // Get badge variant based on confidence score
  const getConfidenceVariant = (
    confidence: number,
  ): "default" | "secondary" | "outline" => {
    if (confidence >= 0.8) return "default"; // High confidence - primary color
    if (confidence >= 0.6) return "secondary"; // Medium confidence
    return "outline"; // Low confidence
  };

  // Get confidence label
  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.8) return "High confidence";
    if (confidence >= 0.6) return "Medium confidence";
    return "Low confidence";
  };

  // Size classes
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
    lg: "text-base px-3 py-1.5",
  };

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {displaySkills.map((skill) => {
        const confidencePercent = Math.round(skill.confidence * 100);
        const tooltipContent = (
          <div className="space-y-1">
            <div className="font-medium">{skill.name}</div>
            {skill.skill_type && (
              <div className="text-xs text-muted-foreground">
                Type: {skill.skill_type}
              </div>
            )}
            {skill.category && (
              <div className="text-xs text-muted-foreground">
                Category: {skill.category}
              </div>
            )}
            <div className="text-xs">
              {getConfidenceLabel(skill.confidence)} ({confidencePercent}%)
            </div>
          </div>
        );

        return (
          <Tooltip key={skill.id} content={tooltipContent}>
            <Badge
              variant={getConfidenceVariant(skill.confidence)}
              className={cn(
                sizeClasses[size],
                "cursor-help transition-colors hover:bg-primary/20",
              )}
            >
              {skill.name}
              {showConfidence && (
                <span className="ml-1.5 text-xs opacity-70">
                  {confidencePercent}%
                </span>
              )}
            </Badge>
          </Tooltip>
        );
      })}
      {remainingCount > 0 && (
        <Badge variant="outline" className={cn(sizeClasses[size])}>
          +{remainingCount} more
        </Badge>
      )}
    </div>
  );
}

/**
 * Skill Tags Section - For use in detail views
 */
interface SkillTagsSectionProps {
  skills: Skill[];
  title?: string;
  description?: string;
  showAll?: boolean;
  className?: string;
}

export function SkillTagsSection({
  skills,
  title = "Extracted Skills",
  description = "Skills identified from job description using Lightcast Open Skills taxonomy",
  showAll = false,
  className,
}: SkillTagsSectionProps) {
  const [expanded, setExpanded] = React.useState(showAll);
  const displayLimit = expanded ? undefined : 15;

  return (
    <div className={cn("space-y-3", className)}>
      <div>
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>

      <SkillTags
        skills={skills}
        maxDisplay={displayLimit}
        showConfidence
        size="md"
      />

      {skills && skills.length > 15 && !expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="text-sm text-primary hover:underline"
        >
          Show all {skills.length} skills
        </button>
      )}

      {expanded && skills && skills.length > 15 && (
        <button
          onClick={() => setExpanded(false)}
          className="text-sm text-primary hover:underline"
        >
          Show fewer skills
        </button>
      )}

      <div className="mt-4 p-3 bg-muted/50 rounded-md">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="font-medium">Total Skills:</span>{" "}
            <span className="text-muted-foreground">{skills?.length || 0}</span>
          </div>
          <div>
            <span className="font-medium">Avg Confidence:</span>{" "}
            <span className="text-muted-foreground">
              {skills && skills.length > 0
                ? Math.round(
                    (skills.reduce((sum, s) => sum + s.confidence, 0) /
                      skills.length) *
                      100,
                  )
                : 0}
              %
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
