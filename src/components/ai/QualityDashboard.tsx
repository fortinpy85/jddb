/**
 * Quality Dashboard Component
 * Phase 3: Advanced AI Content Intelligence
 *
 * Displays comprehensive quality metrics with visual breakdown
 */

import React from 'react';
import type { QualityScoreResponse } from '@/types/ai';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  FileText,
  Target,
  Users,
  Shield,
} from 'lucide-react';

interface QualityDashboardProps {
  qualityScore: QualityScoreResponse | null;
  loading?: boolean;
  compact?: boolean;
  className?: string;
}

const QualityColorMap = {
  green: 'bg-green-500',
  blue: 'bg-blue-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
};

const QualityTextColorMap = {
  green: 'text-green-700',
  blue: 'text-blue-700',
  yellow: 'text-yellow-700',
  red: 'text-red-700',
};

const QualityBgColorMap = {
  green: 'bg-green-50',
  blue: 'bg-blue-50',
  yellow: 'bg-yellow-50',
  red: 'bg-red-50',
};

const DimensionIcons = {
  readability: FileText,
  completeness: CheckCircle2,
  clarity: Target,
  inclusivity: Users,
  compliance: Shield,
};

/**
 * Quality Dashboard - Main Component
 */
export function QualityDashboard({
  qualityScore,
  loading = false,
  compact = false,
  className = '',
}: QualityDashboardProps) {
  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (!qualityScore) {
    return (
      <Card className={`p-6 ${className}`}>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No quality data available. Analyze content to see quality metrics.
          </AlertDescription>
        </Alert>
      </Card>
    );
  }

  if (compact) {
    return <CompactQualityView qualityScore={qualityScore} className={className} />;
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div className="space-y-6">
        {/* Header with Overall Score */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Quality Score</h3>
            <p className="text-sm text-gray-600">
              Comprehensive content quality assessment
            </p>
          </div>
          <QualityScoreBadge
            score={qualityScore.overall_score}
            level={qualityScore.quality_level}
            color={qualityScore.quality_color}
            size="lg"
          />
        </div>

        {/* Dimension Scores */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Dimension Breakdown</h4>
          {Object.entries(qualityScore.dimension_scores).map(([key, dimension]) => (
            <DimensionScore
              key={key}
              name={key}
              dimension={dimension}
            />
          ))}
        </div>

        {/* Top Recommendations */}
        {qualityScore.top_recommendations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Top Recommendations
            </h4>
            <ul className="space-y-1.5">
              {qualityScore.top_recommendations.slice(0, 5).map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Improvement Priority */}
        {qualityScore.improvement_priority.length > 0 && (
          <div className="pt-4 border-t">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <h4 className="text-sm font-medium text-gray-700">Priority Areas</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {qualityScore.improvement_priority.map((area, idx) => (
                <Badge key={idx} variant="outline" className="text-yellow-700 border-yellow-300">
                  {area}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

/**
 * Quality Score Badge - Visual score indicator
 */
export function QualityScoreBadge({
  score,
  level,
  color,
  size = 'md',
  showLabel = true,
}: {
  score: number;
  level: string;
  color: 'green' | 'blue' | 'yellow' | 'red';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}) {
  const sizeClasses = {
    sm: 'w-12 h-12 text-lg',
    md: 'w-16 h-16 text-2xl',
    lg: 'w-24 h-24 text-3xl',
  };

  const labelSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center font-bold ${QualityBgColorMap[color]} ${QualityTextColorMap[color]} border-4 ${QualityColorMap[color].replace('bg-', 'border-')}`}
      >
        {Math.round(score)}
      </div>
      {showLabel && (
        <Badge
          variant="outline"
          className={`${labelSizeClasses[size]} ${QualityTextColorMap[color]} ${QualityBgColorMap[color]} border-${color}-300`}
        >
          {level}
        </Badge>
      )}
    </div>
  );
}

/**
 * Dimension Score - Individual quality dimension
 */
function DimensionScore({
  name,
  dimension,
}: {
  name: string;
  dimension: { score: number; weight: string };
}) {
  const Icon = DimensionIcons[name as keyof typeof DimensionIcons] || FileText;
  const displayName = name.charAt(0).toUpperCase() + name.slice(1).replace('_', ' ');

  // Determine color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressColor = (score: number): string => {
    if (score >= 90) return 'bg-green-500';
    if (score >= 75) return 'bg-blue-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">{displayName}</span>
          <Badge variant="outline" className="text-xs">
            {dimension.weight}
          </Badge>
        </div>
        <span className={`text-sm font-semibold ${getScoreColor(dimension.score)}`}>
          {Math.round(dimension.score)}%
        </span>
      </div>
      <div className="relative">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getProgressColor(dimension.score)} transition-all duration-500`}
            style={{ width: `${dimension.score}%` }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Compact Quality View - Minimal display for sidebars
 */
function CompactQualityView({
  qualityScore,
  className = '',
}: {
  qualityScore: QualityScoreResponse;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${QualityBgColorMap[qualityScore.quality_color]} ${className}`}>
      <QualityScoreBadge
        score={qualityScore.overall_score}
        level={qualityScore.quality_level}
        color={qualityScore.quality_color}
        size="sm"
        showLabel={false}
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-900">
          {qualityScore.quality_level} Quality
        </div>
        <div className="text-xs text-gray-600 truncate">
          {qualityScore.improvement_priority.length > 0
            ? `Focus on: ${qualityScore.improvement_priority[0]}`
            : 'All dimensions meeting standards'}
        </div>
      </div>
    </div>
  );
}

/**
 * Quality Trend Chart - Optional visualization (requires recharts)
 * TODO: Implement once historical data is available
 */
export function QualityTrendChart({
  historicalScores,
}: {
  historicalScores: Array<{ date: string; score: number }>;
}) {
  // Placeholder for Phase 4
  return (
    <div className="text-sm text-gray-500 text-center p-4">
      Quality trend visualization coming in Phase 4
    </div>
  );
}
