import React from "react";
import { TrendingUp, Upload, FileText, Search, GitCompare } from "lucide-react";
import { ContentSection } from "@/components/layout/JDDBLayout";
import { ActionButton } from "@/components/ui/design-system";

interface QuickActionsGridProps {
  onNavigateToUpload: () => void;
  onNavigateToJobs: () => void;
  onNavigateToSearch: () => void;
  onNavigateToCompare: () => void;
}

export function QuickActionsGrid({
  onNavigateToUpload,
  onNavigateToJobs,
  onNavigateToSearch,
  onNavigateToCompare,
}: QuickActionsGridProps) {
  return (
    <ContentSection
      title="Quick Actions"
      icon={TrendingUp}
      variant="highlighted"
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <ActionButton
          variant="primary"
          onClick={onNavigateToUpload}
          icon={Upload}
          className="flex flex-col items-center justify-center h-20 sm:h-24 px-3 sm:px-4 touch-target"
          aria-label="Upload new job description files"
        >
          <span className="text-sm sm:text-base text-center font-medium mt-2">
            Upload Files
          </span>
        </ActionButton>

        <ActionButton
          variant="outline"
          color="emerald"
          onClick={onNavigateToJobs}
          icon={FileText}
          className="flex flex-col items-center justify-center h-20 sm:h-24 px-3 sm:px-4 touch-target"
          aria-label="Browse all job descriptions"
        >
          <span className="text-sm sm:text-base text-center font-medium mt-2">
            Browse Jobs
          </span>
        </ActionButton>

        <ActionButton
          variant="outline"
          color="blue"
          onClick={onNavigateToSearch}
          icon={Search}
          className="flex flex-col items-center justify-center h-20 sm:h-24 px-3 sm:px-4 touch-target"
          aria-label="Search and filter job descriptions"
        >
          <span className="text-sm sm:text-base text-center font-medium mt-2">
            Search Jobs
          </span>
        </ActionButton>

        <ActionButton
          variant="outline"
          color="amber"
          onClick={onNavigateToCompare}
          icon={GitCompare}
          className="flex flex-col items-center justify-center h-20 sm:h-24 px-3 sm:px-4 touch-target"
          aria-label="Compare multiple job descriptions"
        >
          <span className="text-sm sm:text-base text-center font-medium mt-2">
            Compare Jobs
          </span>
        </ActionButton>
      </div>
    </ContentSection>
  );
}
