import React from "react";
import { Activity, Upload } from "lucide-react";
import { ContentSection } from "@/components/layout/JDDBLayout";
import { ActionButton } from "@/components/ui/design-system";
import EmptyState from "@/components/ui/empty-state";
import type { JobDescription } from "@/lib/types";

interface RecentJobsListProps {
  jobs: JobDescription[];
  onJobSelect: (job: JobDescription) => void;
  onNavigateToJobs: () => void;
  onNavigateToUpload: () => void;
}

export function RecentJobsList({
  jobs,
  onJobSelect,
  onNavigateToJobs,
  onNavigateToUpload
}: RecentJobsListProps) {
  return (
    <ContentSection
      title="Recent Job Descriptions"
      icon={Activity}
      variant="highlighted"
      headerActions={
        <ActionButton
          variant="outline"
          size="sm"
          color="violet"
          onClick={onNavigateToJobs}
        >
          View All
        </ActionButton>
      }
    >
      {jobs.length > 0 ? (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="group flex items-center justify-between p-4 border border-slate-200/50 rounded-xl hover:bg-gradient-to-r hover:from-violet-50/50 hover:to-purple-50/30 cursor-pointer transition-all duration-300 hover:scale-[1.01] hover:shadow-lg hover:border-violet-200/50"
              onClick={() => onJobSelect(job)}
            >
              <div className="relative z-10">
                <p className="font-semibold text-slate-800 group-hover:text-violet-700 transition-colors duration-200">
                  {job.title}
                </p>
                <p className="text-sm text-slate-500 font-medium group-hover:text-violet-600 transition-colors duration-200">
                  {job.job_number} • {job.classification}
                </p>
              </div>
              <div className="text-right relative z-10">
                <p className="text-sm text-slate-500 bg-slate-100/50 px-2 py-1 rounded-full group-hover:bg-violet-100/50 group-hover:text-violet-600 transition-all duration-200 font-medium">
                  {job.processed_date ? new Date(job.processed_date).toLocaleDateString() : "Not processed"}
                </p>
              </div>
              <div className="absolute inset-0 bg-gradient-to-r from-violet-500/5 to-purple-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          type="no-jobs"
          showIllustration={false}
          actions={[
            {
              label: "Upload Files",
              onClick: onNavigateToUpload,
              icon: Upload,
            },
          ]}
          className="border-0 bg-transparent"
        />
      )}
    </ContentSection>
  );
}