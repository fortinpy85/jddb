/**
 * Classification Badge with Tooltip
 * Addresses Usability Issue #6.2: Classification Codes Without Descriptions
 * Shows full description on hover to aid recognition over recall
 */

"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ClassificationBadgeProps {
  code: string;
  className?: string;
  showHelpIcon?: boolean;
  variant?: "default" | "secondary" | "outline" | "destructive";
}

// Classification code descriptions
// Reference: Government of Canada classification system
const CLASSIFICATION_DESCRIPTIONS: Record<string, string> = {
  "EX-01": "Executive Level 1 - Director level position",
  "EX-02": "Executive Level 2 - Director General level position",
  "EX-03": "Executive Level 3 - Assistant Deputy Minister level position",
  "EX-04": "Executive Level 4 - Deputy Minister level position",
  "EX-05": "Executive Level 5 - Senior Deputy Minister level position",
  "AS-01": "Administrative Services Level 1 - Entry level administrative",
  "AS-02": "Administrative Services Level 2 - Intermediate administrative",
  "AS-03": "Administrative Services Level 3 - Senior administrative",
  "AS-04": "Administrative Services Level 4 - Team lead administrative",
  "AS-05": "Administrative Services Level 5 - Manager administrative",
  "CS-01": "Computer Systems Level 1 - Junior developer/analyst",
  "CS-02": "Computer Systems Level 2 - Intermediate developer/analyst",
  "CS-03": "Computer Systems Level 3 - Senior developer/analyst",
  "CS-04": "Computer Systems Level 4 - Technical lead/architect",
  "CS-05": "Computer Systems Level 5 - IT Manager",
  "PM-01": "Program Management Level 1 - Junior program officer",
  "PM-02": "Program Management Level 2 - Program officer",
  "PM-03": "Program Management Level 3 - Senior program officer",
  "PM-04": "Program Management Level 4 - Program manager",
  "PM-05": "Program Management Level 5 - Senior program manager",
  "PM-06": "Program Management Level 6 - Director level program management",
  "EC-01": "Economics Level 1 - Junior economist",
  "EC-02": "Economics Level 2 - Economist",
  "EC-03": "Economics Level 3 - Senior economist",
  "EC-04": "Economics Level 4 - Principal economist",
  "EC-05": "Economics Level 5 - Chief economist",
  "EC-06": "Economics Level 6 - Director level economics",
  "FI-01": "Financial Management Level 1 - Junior financial officer",
  "FI-02": "Financial Management Level 2 - Financial officer",
  "FI-03": "Financial Management Level 3 - Senior financial officer",
  "FI-04": "Financial Management Level 4 - Financial manager",
  "PE-01": "Personnel Administration Level 1 - Junior HR officer",
  "PE-02": "Personnel Administration Level 2 - HR officer",
  "PE-03": "Personnel Administration Level 3 - Senior HR officer",
  "PE-04": "Personnel Administration Level 4 - HR manager",
  "PE-05": "Personnel Administration Level 5 - Senior HR manager",
  "PE-06": "Personnel Administration Level 6 - Director level HR",
};

export function ClassificationBadge({
  code,
  className,
  showHelpIcon = false,
  variant = "secondary",
}: ClassificationBadgeProps) {
  const description =
    CLASSIFICATION_DESCRIPTIONS[code] ||
    `${code} - Classification description not available`;

  return (
    <TooltipProvider delayDuration={300}>
      <TooltipTrigger asChild>
        <Badge
          variant={variant}
          className={cn(
            "cursor-help transition-all hover:ring-2 hover:ring-primary/20",
            className,
          )}
        >
          {code}
          {showHelpIcon && <HelpCircle className="ml-1 h-3 w-3 opacity-70" />}
        </Badge>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <p className="font-semibold">{code}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </TooltipContent>
    </TooltipProvider>
  );
}

/**
 * Classification Select with Descriptions
 * For use in filters and forms
 */
interface ClassificationSelectProps {
  value?: string;
  onChange?: (value: string) => void;
  className?: string;
}

export function ClassificationSelect({
  value,
  onChange,
  className,
}: ClassificationSelectProps) {
  const classifications = Object.keys(CLASSIFICATION_DESCRIPTIONS).sort();

  return (
    <select
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    >
      <option value="">All Classifications</option>
      {classifications.map((code) => (
        <option key={code} value={code}>
          {code} - {CLASSIFICATION_DESCRIPTIONS[code]}
        </option>
      ))}
    </select>
  );
}

/**
 * Hook to get classification description
 */
export function useClassificationInfo(code: string) {
  const description = CLASSIFICATION_DESCRIPTIONS[code];
  const level = code.split("-")[1];
  const group = code.split("-")[0];

  return {
    code,
    description,
    level,
    group,
    fullName: description || `${code} - Unknown classification`,
  };
}
