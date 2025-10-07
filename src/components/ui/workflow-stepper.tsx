/**
 * Workflow Progress Stepper
 * Visual indicator showing user's progress through the job improvement workflow
 * Addresses Critical Usability Issue #3: Unclear User Flow
 */

"use client";

import React from "react";
import { Check, Upload, FileSearch, Wand2, Download } from "lucide-react";
import { cn } from "@/lib/utils";

export type WorkflowStep = "upload" | "review" | "improve" | "export";

interface WorkflowStepperProps {
  currentStep: WorkflowStep;
  completedSteps?: WorkflowStep[];
  className?: string;
}

interface Step {
  id: WorkflowStep;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const steps: Step[] = [
  {
    id: "upload",
    label: "Upload",
    icon: Upload,
    description: "Ingest job description",
  },
  {
    id: "review",
    label: "Review",
    icon: FileSearch,
    description: "Check quality score",
  },
  {
    id: "improve",
    label: "Improve",
    icon: Wand2,
    description: "Apply AI suggestions",
  },
  {
    id: "export",
    label: "Export",
    icon: Download,
    description: "Download improved version",
  },
];

export function WorkflowStepper({
  currentStep,
  completedSteps = [],
  className,
}: WorkflowStepperProps) {
  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);

  const getStepStatus = (stepIndex: number, stepId: WorkflowStep) => {
    if (completedSteps.includes(stepId)) return "completed";
    if (stepIndex === currentStepIndex) return "current";
    if (stepIndex < currentStepIndex) return "completed";
    return "upcoming";
  };

  return (
    <div className={cn("w-full", className)}>
      <nav aria-label="Workflow progress">
        <ol className="flex items-center justify-between">
          {steps.map((step, index) => {
            const status = getStepStatus(index, step.id);
            const Icon = step.icon;
            const isCompleted = status === "completed";
            const isCurrent = status === "current";
            const isUpcoming = status === "upcoming";

            return (
              <li
                key={step.id}
                className={cn(
                  "flex flex-col items-center relative",
                  index !== steps.length - 1 && "flex-1",
                )}
              >
                {/* Connector line */}
                {index !== steps.length - 1 && (
                  <div
                    className={cn(
                      "absolute top-5 left-1/2 w-full h-0.5 -z-10",
                      isCompleted ? "bg-primary" : "bg-muted",
                    )}
                  />
                )}

                {/* Step indicator */}
                <div className="flex flex-col items-center gap-2">
                  <div
                    className={cn(
                      "flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all",
                      isCompleted &&
                        "bg-primary border-primary text-primary-foreground",
                      isCurrent &&
                        "bg-primary/10 border-primary text-primary ring-4 ring-primary/20",
                      isUpcoming &&
                        "bg-background border-muted text-muted-foreground",
                    )}
                    aria-current={isCurrent ? "step" : undefined}
                  >
                    {isCompleted ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <Icon className="w-5 h-5" />
                    )}
                  </div>

                  {/* Step label */}
                  <div className="text-center min-w-[80px]">
                    <div
                      className={cn(
                        "text-sm font-medium",
                        isCurrent && "text-primary",
                        isCompleted && "text-foreground",
                        isUpcoming && "text-muted-foreground",
                      )}
                    >
                      {step.label}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5 hidden sm:block">
                      {step.description}
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Current step description for mobile */}
      <div className="mt-4 text-center sm:hidden">
        <p className="text-sm text-muted-foreground">
          {steps[currentStepIndex].description}
        </p>
      </div>
    </div>
  );
}

/**
 * Hook to manage workflow progress state
 */
export function useWorkflowProgress() {
  const [currentStep, setCurrentStep] = React.useState<WorkflowStep>("upload");
  const [completedSteps, setCompletedSteps] = React.useState<WorkflowStep[]>(
    [],
  );

  const completeStep = (step: WorkflowStep) => {
    setCompletedSteps((prev) => {
      if (prev.includes(step)) return prev;
      return [...prev, step];
    });
  };

  const goToStep = (step: WorkflowStep) => {
    setCurrentStep(step);
  };

  const nextStep = () => {
    const currentIndex = steps.findIndex((s) => s.id === currentStep);
    if (currentIndex < steps.length - 1) {
      completeStep(currentStep);
      setCurrentStep(steps[currentIndex + 1].id);
    }
  };

  const previousStep = () => {
    const currentIndex = steps.findIndex((s) => s.id === currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1].id);
    }
  };

  const reset = () => {
    setCurrentStep("upload");
    setCompletedSteps([]);
  };

  return {
    currentStep,
    completedSteps,
    completeStep,
    goToStep,
    nextStep,
    previousStep,
    reset,
  };
}
