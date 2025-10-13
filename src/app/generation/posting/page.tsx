"use client";

import React, { useState } from "react";
import { JobPostingGenerator } from "@/components/generation/JobPostingGenerator";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { JobDescription } from "@/types/api";

export default function JobPostingGeneratorPage() {
  const [selectedJob, setSelectedJob] = useState<JobDescription | null>(null);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-6 px-4">
        <div className="mb-6 flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (window.location.href = "/")}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Job Posting Generator</h1>
            <p className="text-muted-foreground mt-1">
              Transform job descriptions into optimized public postings
            </p>
          </div>
        </div>
        <JobPostingGenerator selectedJob={selectedJob} />
      </div>
    </div>
  );
}
