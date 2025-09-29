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
  onNavigateToCompare
}: QuickActionsGridProps) {
  return (
    <ContentSection
      title="Quick Actions"
      icon={TrendingUp}
      variant="highlighted"
    >
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <ActionButton
          variant="primary"
          onClick={onNavigateToUpload}
          icon={Upload}
          className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 px-4"
        >
          <span className="text-sm text-center">Upload Files</span>
        </ActionButton>

        <ActionButton
          variant="outline"
          color="emerald"
          onClick={onNavigateToJobs}
          icon={FileText}
          className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 px-4"
        >
          <span className="text-sm text-center">Browse Jobs</span>
        </ActionButton>

        <ActionButton
          variant="outline"
          color="blue"
          onClick={onNavigateToSearch}
          icon={Search}
          className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 px-4"
        >
          <span className="text-sm text-center">Search Jobs</span>
        </ActionButton>

        <ActionButton
          variant="outline"
          color="amber"
          onClick={onNavigateToCompare}
          icon={GitCompare}
          className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 px-4"
        >
          <span className="text-sm text-center">Compare Jobs</span>
        </ActionButton>
      </div>
    </ContentSection>
  );
}