"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle, Circle, Clock } from "lucide-react";

export interface WorkflowStep {
  id: string;
  title: string;
  description?: string;
  status: "completed" | "current" | "upcoming";
}

interface WorkflowStepsProps {
  steps: WorkflowStep[];
  className?: string;
}

export function WorkflowSteps({ steps, className }: WorkflowStepsProps) {
  return (
    <div className={cn("flex items-center justify-between w-full", className)}>
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div className="flex flex-col items-center text-center">
            {/* Step Circle */}
            <div
              className={cn(
                "flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-200",
                {
                  "bg-green-500 border-green-500 text-white": step.status === "completed",
                  "bg-blue-500 border-blue-500 text-white": step.status === "current",
                  "bg-gray-100 border-gray-300 text-gray-400": step.status === "upcoming",
                }
              )}
            >
              {step.status === "completed" ? (
                <CheckCircle className="w-5 h-5" />
              ) : step.status === "current" ? (
                <Clock className="w-5 h-5" />
              ) : (
                <span className="text-sm font-medium">{index + 1}</span>
              )}
            </div>

            {/* Step Title */}
            <div className="mt-2 max-w-24">
              <p
                className={cn(
                  "text-xs font-medium leading-tight",
                  {
                    "text-green-600": step.status === "completed",
                    "text-blue-600": step.status === "current",
                    "text-gray-500": step.status === "upcoming",
                  }
                )}
              >
                {step.title}
              </p>
              {step.description && (
                <p className="text-xs text-gray-400 mt-1">{step.description}</p>
              )}
            </div>
          </div>

          {/* Connector Line */}
          {index < steps.length - 1 && (
            <div className="flex-1 mx-4">
              <div
                className={cn(
                  "h-0.5 bg-gray-200 transition-all duration-200",
                  {
                    "bg-green-400": steps[index + 1].status === "completed",
                    "bg-blue-300": steps[index + 1].status === "current",
                  }
                )}
              />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// Preset workflow configurations
export const JOB_PROCESSING_WORKFLOW: WorkflowStep[] = [
  {
    id: "creation",
    title: "Creation",
    description: "Job uploaded",
    status: "completed",
  },
  {
    id: "processing",
    title: "Processing",
    description: "AI analysis",
    status: "current",
  },
  {
    id: "review",
    title: "Review",
    description: "Quality check",
    status: "upcoming",
  },
  {
    id: "approval",
    title: "Approval",
    description: "Final sign-off",
    status: "upcoming",
  },
  {
    id: "published",
    title: "Published",
    description: "Live in system",
    status: "upcoming",
  },
];

export const TRANSLATION_WORKFLOW: WorkflowStep[] = [
  {
    id: "source",
    title: "Source",
    description: "Original text",
    status: "completed",
  },
  {
    id: "translate",
    title: "Translate",
    description: "AI translation",
    status: "current",
  },
  {
    id: "review",
    title: "Review",
    description: "Human review",
    status: "upcoming",
  },
  {
    id: "approve",
    title: "Approve",
    description: "Final approval",
    status: "upcoming",
  },
];