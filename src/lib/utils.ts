import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const formatFileSize = (bytes: number): string => {
  const sizes = ["B", "KB", "MB", "GB"];
  if (bytes === 0) return "0 B";
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + " " + sizes[i];
};

export const getClassificationLevel = (classification: string): string => {
  const levels = {
    "EX-01": "Director",
    "EX-02": "Executive Director",
    "EX-03": "Director General",
    "EX-04": "Assistant Deputy Minister",
    "EX-05": "Senior ADM/Deputy Minister",
  };
  return levels[classification as keyof typeof levels] || classification;
};

export const getLanguageName = (code: string): string => {
  const languageMap: Record<string, string> = {
    en: "English",
    fr: "French",
  };
  return languageMap[code] || code;
};

export const getStatusColor = (status: string): string => {
  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    needs_review: "bg-orange-100 text-orange-800",
  };
  return statusColors[status] || "bg-gray-100 text-gray-800";
};
export const handleExport = async (job: JobDescription) => {
  try {
    // Fetch full job details with content, sections, and metadata
    const fullJob = await apiClient.getJob(job.id);
    const jobData = fullJob as JobDescription;

    // Create a formatted text export
    const exportData = `
JOB DESCRIPTION EXPORT
=====================

Job Number: ${jobData.job_number}
Title: ${jobData.title}
Classification: ${jobData.classification} (${getClassificationLevel(jobData.classification)})
Language: ${getLanguageName(jobData.language)}
Processed Date: ${jobData.processed_date ? new Date(jobData.processed_date).toLocaleDateString() : "N/A"}

${
  jobData.metadata
    ? `
METADATA
--------
Reports To: ${jobData.metadata.reports_to || "N/A"}
Department: ${jobData.metadata.department || "N/A"}
Location: ${jobData.metadata.location || "N/A"}
FTE Count: ${jobData.metadata.fte_count || "N/A"}
Salary Budget: ${jobData.metadata.salary_budget ? `${jobData.metadata.salary_budget.toLocaleString()}` : "N/A"}
`
    : ""
}

${
  jobData.sections?.length
    ? `
SECTIONS
--------
${jobData.sections
  .map(
    (section: any) => `
${section.section_type.replace("_", " ").toUpperCase()}:
${section.section_content}
`,
  )
  .join("\n")}
`
    : ""
}

${
  jobData.raw_content
    ? `
RAW CONTENT
-----------
${jobData.raw_content}
`
    : ""
}
      `;

    // Create and download file
    const blob = new Blob([exportData], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = `job_${jobData.job_number}_${jobData.title?.replace(/[^a-z0-9]/gi, "_")}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (err) {
    alert(
      "Export failed: " +
        (err instanceof Error ? err.message : "Unknown error"),
    );
  }
};
