"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { CheckCircle, AlertCircle, Clock, Upload } from "lucide-react";

import { cn } from "@/lib/utils";

// Basic Progress Bar Component (Radix UI based)
// WCAG 2.1 Level AA Compliance: All progressbar elements must have accessible names
function Progress({
  className,
  value,
  "aria-label": ariaLabel,
  "aria-labelledby": ariaLabelledBy,
  ...props
}: React.ComponentProps<typeof ProgressPrimitive.Root>) {
  // Ensure accessibility: require either aria-label or aria-labelledby
  const accessibilityProps = {
    "aria-label": ariaLabel || (ariaLabelledBy ? undefined : "Progress"),
    "aria-labelledby": ariaLabelledBy,
  };

  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn(
        "bg-primary/20 relative h-2 w-full overflow-hidden rounded-full",
        className,
      )}
      {...accessibilityProps}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className="bg-primary h-full w-full flex-1 transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  );
}

// Step-based Progress Indicator Component
export interface ProgressStep {
  id: string;
  label: string;
  status: "pending" | "active" | "completed" | "error";
  description?: string;
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
  currentStep?: string;
  className?: string;
  variant?: "horizontal" | "vertical";
}

function ProgressIndicator({
  steps,
  currentStep,
  className = "",
  variant = "vertical",
}: ProgressIndicatorProps) {
  const getStepIcon = (status: ProgressStep["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case "active":
        return (
          <div className="w-5 h-5 rounded-full bg-blue-500 animate-pulse" />
        );
      default:
        return <Clock className="w-5 h-5 text-gray-300" />;
    }
  };

  const getStepStyles = (status: ProgressStep["status"]) => {
    switch (status) {
      case "completed":
        return "text-green-700 border-green-200 bg-green-50";
      case "error":
        return "text-red-700 border-red-200 bg-red-50";
      case "active":
        return "text-blue-700 border-blue-200 bg-blue-50";
      default:
        return "text-gray-500 border-gray-200 bg-gray-50";
    }
  };

  if (variant === "horizontal") {
    return (
      <div className={`flex items-center space-x-4 ${className}`}>
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${getStepStyles(step.status)}`}
            >
              {getStepIcon(step.status)}
              <span className="text-sm font-medium">{step.label}</span>
            </div>
            {index < steps.length - 1 && (
              <div className="w-8 h-0.5 bg-gray-200" />
            )}
          </React.Fragment>
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-start space-x-3">
          <div className="flex flex-col items-center">
            {getStepIcon(step.status)}
            {index < steps.length - 1 && (
              <div className="w-0.5 h-6 bg-gray-200 mt-2" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p
              className={`text-sm font-medium ${
                step.status === "completed"
                  ? "text-green-700"
                  : step.status === "error"
                    ? "text-red-700"
                    : step.status === "active"
                      ? "text-blue-700"
                      : "text-gray-500"
              }`}
            >
              {step.label}
            </p>
            {step.description && (
              <p
                className={`text-xs mt-1 ${
                  step.status === "completed"
                    ? "text-green-600"
                    : step.status === "error"
                      ? "text-red-600"
                      : step.status === "active"
                        ? "text-blue-600"
                        : "text-gray-400"
                }`}
              >
                {step.description}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export { Progress, ProgressIndicator };
