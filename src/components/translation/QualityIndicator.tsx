/**
 * QualityIndicator Component
 *
 * Visual indicator for translation quality with detailed breakdown.
 * Displays quality score (0-100) with color-coded status and detailed metrics.
 */

import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, CheckCircle2, Info, TrendingUp } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";

export interface QualityAssessment {
  overall_score: number;
  completeness_score: number;
  length_ratio_score: number;
  terminology_score: number;
  formatting_score: number;
  issues: string[];
  warnings: string[];
  suggestions: string[];
  timestamp: string;
}

export interface QualityIndicatorProps {
  assessment: QualityAssessment | null;
  loading?: boolean;
  onRefresh?: () => void;
  compact?: boolean;
}

/**
 * Get quality status based on score
 */
const getQualityStatus = (
  score: number,
): { label: string; color: string; icon: React.ReactNode } => {
  if (score >= 90) {
    return {
      label: "Excellent",
      color: "bg-green-500",
      icon: <CheckCircle2 className="h-4 w-4" />,
    };
  } else if (score >= 80) {
    return {
      label: "Good",
      color: "bg-blue-500",
      icon: <CheckCircle2 className="h-4 w-4" />,
    };
  } else if (score >= 70) {
    return {
      label: "Acceptable",
      color: "bg-yellow-500",
      icon: <Info className="h-4 w-4" />,
    };
  } else if (score >= 60) {
    return {
      label: "Needs Improvement",
      color: "bg-orange-500",
      icon: <AlertCircle className="h-4 w-4" />,
    };
  } else {
    return {
      label: "Poor",
      color: "bg-red-500",
      icon: <AlertCircle className="h-4 w-4" />,
    };
  }
};

/**
 * Get color class for score
 */
const getScoreColor = (score: number): string => {
  if (score >= 90) return "text-green-600";
  if (score >= 80) return "text-blue-600";
  if (score >= 70) return "text-yellow-600";
  if (score >= 60) return "text-orange-600";
  return "text-red-600";
};

/**
 * QualityIndicator Component
 */
export const QualityIndicator: React.FC<QualityIndicatorProps> = ({
  assessment,
  loading = false,
  onRefresh,
  compact = false,
}) => {
  const [showDetails, setShowDetails] = useState(false);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quality Assessment</CardTitle>
          <CardDescription>Loading quality metrics...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!assessment) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quality Assessment</CardTitle>
          <CardDescription>No quality data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground p-4">
            Assess translation quality to see metrics
          </div>
        </CardContent>
      </Card>
    );
  }

  const status = getQualityStatus(assessment.overall_score);

  // Compact view for inline display
  if (compact) {
    return (
      <>
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80"
          onClick={() => setShowDetails(true)}
        >
          <div className={`w-2 h-2 rounded-full ${status.color}`} />
          <span
            className={`font-semibold ${getScoreColor(assessment.overall_score)}`}
          >
            {assessment.overall_score}%
          </span>
          <Badge variant="outline" className="text-xs">
            {status.label}
          </Badge>
        </div>
        <Dialog open={showDetails} onOpenChange={setShowDetails}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Quality Assessment Details</DialogTitle>
              <DialogDescription>
                Comprehensive translation quality breakdown
              </DialogDescription>
            </DialogHeader>
            <QualityDetailsContent assessment={assessment} />
          </DialogContent>
        </Dialog>
      </>
    );
  }

  // Full view
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Quality Assessment</CardTitle>
            <CardDescription>
              Translation quality score and breakdown
            </CardDescription>
          </div>
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <TrendingUp className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Overall Score */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
              {status.icon}
              <span
                className={`text-4xl font-bold ${getScoreColor(assessment.overall_score)}`}
              >
                {assessment.overall_score}
              </span>
              <span className="text-2xl text-muted-foreground">/100</span>
            </div>
            <Badge className={status.color}>{status.label}</Badge>
          </div>

          <Separator />

          {/* Score Breakdown */}
          <QualityDetailsContent assessment={assessment} />
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Quality Details Content (shared between full and compact views)
 */
const QualityDetailsContent: React.FC<{ assessment: QualityAssessment }> = ({
  assessment,
}) => {
  const metrics = [
    {
      label: "Completeness",
      score: assessment.completeness_score,
      description: "Translation coverage and placeholder handling",
    },
    {
      label: "Terminology",
      score: assessment.terminology_score,
      description: "Consistency with government glossary",
    },
    {
      label: "Length Ratio",
      score: assessment.length_ratio_score,
      description: "Appropriate translation length",
    },
    {
      label: "Formatting",
      score: assessment.formatting_score,
      description: "Structure consistency (bullets, line breaks)",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Metric Breakdown */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Score Breakdown</h4>
        {metrics.map((metric) => (
          <div key={metric.label} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{metric.label}</span>
              <span className={`font-semibold ${getScoreColor(metric.score)}`}>
                {metric.score}%
              </span>
            </div>
            <Progress value={metric.score} className="h-2" />
            <p className="text-xs text-muted-foreground">
              {metric.description}
            </p>
          </div>
        ))}
      </div>

      {/* Issues */}
      {assessment.issues.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Issues Found ({assessment.issues.length})</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 space-y-1 list-disc list-inside">
              {assessment.issues.map((issue, idx) => (
                <li key={idx} className="text-sm">
                  {issue}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Warnings */}
      {assessment.warnings.length > 0 && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Warnings ({assessment.warnings.length})</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 space-y-1 list-disc list-inside">
              {assessment.warnings.map((warning, idx) => (
                <li key={idx} className="text-sm">
                  {warning}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Suggestions */}
      {assessment.suggestions.length > 0 && (
        <Alert>
          <TrendingUp className="h-4 w-4" />
          <AlertTitle>Suggestions ({assessment.suggestions.length})</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 space-y-1 list-disc list-inside">
              {assessment.suggestions.map((suggestion, idx) => (
                <li key={idx} className="text-sm">
                  {suggestion}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Timestamp */}
      <p className="text-xs text-muted-foreground text-right">
        Last assessed: {new Date(assessment.timestamp).toLocaleString()}
      </p>
    </div>
  );
};
