"use client";

import React from "react";
import { AIJobWriter } from "@/components/generation/AIJobWriter";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AIJobWriterPage() {
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
            <h1 className="text-3xl font-bold">AI Job Description Writer</h1>
            <p className="text-muted-foreground mt-1">
              Create comprehensive job descriptions with AI assistance
            </p>
          </div>
        </div>
        <AIJobWriter />
      </div>
    </div>
  );
}
