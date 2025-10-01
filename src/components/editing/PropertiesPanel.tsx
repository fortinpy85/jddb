/**
 * Properties Panel Component
 * Displays quality metrics, accessibility scores, and improvement suggestions
 * Shown on the right side of editing workspace
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { PanelSection } from "@/components/layout/TwoPanelLayout";
import {
  FileText,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Lightbulb,
  Users,
  Globe,
  BarChart3,
  Eye,
  Target,
  Shield,
} from "lucide-react";

interface PropertiesPanelProps {
  jobId?: number;
  collapsed?: boolean;
  className?: string;
}

interface QualityMetric {
  label: string;
  score: number;
  status: "excellent" | "good" | "needs-improvement" | "poor";
  description: string;
}

interface Suggestion {
  id: string;
  type: "accessibility" | "bias" | "clarity" | "structure";
  severity: "high" | "medium" | "low";
  title: string;
  description: string;
  section?: string;
}

export function PropertiesPanel({
  jobId,
  collapsed = false,
  className,
}: PropertiesPanelProps) {
  // Mock data - in production, fetch from API based on jobId
  const qualityMetrics: QualityMetric[] = [
    {
      label: "Overall Quality",
      score: 85,
      status: "good",
      description: "Good job description quality with room for improvement",
    },
    {
      label: "Accessibility",
      score: 78,
      status: "good",
      description: "Meets most accessibility standards",
    },
    {
      label: "Language Bias",
      score: 92,
      status: "excellent",
      description: "Minimal language bias detected",
    },
    {
      label: "Clarity Score",
      score: 72,
      status: "needs-improvement",
      description: "Some sections could be more clear",
    },
    {
      label: "Structure",
      score: 88,
      status: "good",
      description: "Well-structured content",
    },
  ];

  const suggestions: Suggestion[] = [
    {
      id: "1",
      type: "accessibility",
      severity: "high",
      title: "Add alternative text descriptions",
      description: "Include descriptions for visual elements to improve accessibility",
      section: "Organization Structure",
    },
    {
      id: "2",
      type: "bias",
      severity: "medium",
      title: "Gender-neutral language",
      description: 'Consider replacing "he/she" with "they" for inclusivity',
      section: "Specific Accountabilities",
    },
    {
      id: "3",
      type: "clarity",
      severity: "medium",
      title: "Simplify complex sentences",
      description: "Break down long sentences for better readability",
      section: "Nature and Scope",
    },
    {
      id: "4",
      type: "structure",
      severity: "low",
      title: "Add subsections",
      description: "Consider breaking this section into smaller subsections",
      section: "Knowledge and Skills",
    },
  ];

  const jobMetadata = {
    classification: "EX-01",
    language: "English",
    wordCount: 1247,
    lastModified: new Date().toLocaleDateString(),
    version: "3.2",
    author: "Alice Johnson",
  };

  if (collapsed) {
    return (
      <div className={cn("flex flex-col items-center space-y-4 py-4", className)}>
        <Button variant="ghost" size="sm" className="w-full p-2" title="Properties">
          <FileText className="w-5 h-5" />
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4 p-4 h-full overflow-y-auto", className)}>
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Properties
          </h2>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Quality metrics and improvement suggestions
        </p>
      </div>

      {/* Job Metadata */}
      <PanelSection title="Document Info" icon={FileText} collapsible defaultCollapsed={false}>
        <div className="space-y-2">
          <InfoRow label="Classification" value={jobMetadata.classification} />
          <InfoRow label="Language" value={jobMetadata.language} />
          <InfoRow label="Word Count" value={jobMetadata.wordCount.toLocaleString()} />
          <InfoRow label="Last Modified" value={jobMetadata.lastModified} />
          <InfoRow label="Version" value={jobMetadata.version} />
          <InfoRow label="Author" value={jobMetadata.author} />
        </div>
      </PanelSection>

      {/* Quality Metrics */}
      <PanelSection
        title="Quality Metrics"
        icon={BarChart3}
        collapsible
        defaultCollapsed={false}
        headerActions={
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
            <Eye className="w-3 h-3" />
          </Button>
        }
      >
        <div className="space-y-4">
          {qualityMetrics.map((metric, index) => (
            <QualityMetricCard key={index} metric={metric} />
          ))}
        </div>
      </PanelSection>

      {/* Improvement Suggestions */}
      <PanelSection
        title="Suggestions"
        icon={Lightbulb}
        collapsible
        defaultCollapsed={false}
        headerActions={
          <Badge variant="secondary" className="text-xs">
            {suggestions.length}
          </Badge>
        }
      >
        <div className="space-y-3">
          {suggestions.map((suggestion) => (
            <SuggestionCard key={suggestion.id} suggestion={suggestion} />
          ))}
        </div>
      </PanelSection>

      {/* Actions */}
      <div className="space-y-2 pt-2">
        <Button variant="outline" size="sm" className="w-full">
          <Target className="w-4 h-4 mr-2" />
          Run Quality Check
        </Button>
        <Button variant="outline" size="sm" className="w-full">
          <Shield className="w-4 h-4 mr-2" />
          Check Compliance
        </Button>
      </div>
    </div>
  );
}

/**
 * Info Row Component
 */
interface InfoRowProps {
  label: string;
  value: string | number;
}

function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-slate-600 dark:text-slate-400">{label}</span>
      <span className="font-medium text-slate-900 dark:text-slate-100">{value}</span>
    </div>
  );
}

/**
 * Quality Metric Card Component
 */
interface QualityMetricCardProps {
  metric: QualityMetric;
}

function QualityMetricCard({ metric }: QualityMetricCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "excellent":
        return "text-green-600 dark:text-green-400";
      case "good":
        return "text-blue-600 dark:text-blue-400";
      case "needs-improvement":
        return "text-yellow-600 dark:text-yellow-400";
      case "poor":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-slate-600 dark:text-slate-400";
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case "excellent":
        return "bg-green-500";
      case "good":
        return "bg-blue-500";
      case "needs-improvement":
        return "bg-yellow-500";
      case "poor":
        return "bg-red-500";
      default:
        return "bg-slate-500";
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
          {metric.label}
        </span>
        <span className={cn("text-xs font-bold", getStatusColor(metric.status))}>
          {metric.score}%
        </span>
      </div>
      <div className="relative">
        <Progress value={metric.score} className="h-2" />
        <div
          className={cn("absolute inset-0 h-2 rounded-full transition-all", getProgressColor(metric.status))}
          style={{ width: `${metric.score}%` }}
        />
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-500">
        {metric.description}
      </p>
    </div>
  );
}

/**
 * Suggestion Card Component
 */
interface SuggestionCardProps {
  suggestion: Suggestion;
}

function SuggestionCard({ suggestion }: SuggestionCardProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400";
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400";
      case "low":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-900/20 dark:text-slate-400";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "accessibility":
        return Eye;
      case "bias":
        return Users;
      case "clarity":
        return Globe;
      case "structure":
        return FileText;
      default:
        return Lightbulb;
    }
  };

  const Icon = getTypeIcon(suggestion.type);

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer border-slate-200 dark:border-slate-700">
      <CardContent className="p-3">
        <div className="flex items-start space-x-2">
          <div className="p-1 bg-slate-100 dark:bg-slate-800 rounded">
            <Icon className="w-3 h-3 text-slate-600 dark:text-slate-400" />
          </div>
          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate">
                {suggestion.title}
              </span>
              <Badge variant="secondary" className={cn("text-xs ml-2", getSeverityColor(suggestion.severity))}>
                {suggestion.severity}
              </Badge>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
              {suggestion.description}
            </p>
            {suggestion.section && (
              <div className="flex items-center space-x-1 mt-1">
                <FileText className="w-3 h-3 text-slate-400" />
                <span className="text-xs text-slate-500 dark:text-slate-500">
                  {suggestion.section}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
