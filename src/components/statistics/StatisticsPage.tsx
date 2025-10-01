/**
 * Statistics Page Component
 * Detailed metrics and analytics dashboard
 * Displays charts, trends, and comprehensive statistics
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar,
  Users,
  FileText,
  Globe,
  CheckCircle,
  Clock,
  AlertTriangle,
  Download,
  RefreshCw,
  Activity,
  PieChart,
  LineChart,
} from "lucide-react";

interface StatisticsPageProps {
  onBack?: () => void;
  className?: string;
}

export function StatisticsPage({ onBack, className }: StatisticsPageProps) {
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d" | "1y">("30d");

  // Mock data - in production, fetch from API
  const overallStats = {
    totalJobs: 1247,
    completedJobs: 892,
    inProgressJobs: 234,
    failedJobs: 121,
    growthRate: 12.5,
    avgProcessingTime: "4.2 min",
    qualityScore: 87,
  };

  const categoryStats = [
    { category: "EX", count: 342, percentage: 27.4, trend: "up", change: 8.3 },
    { category: "AS", count: 298, percentage: 23.9, trend: "up", change: 5.1 },
    { category: "PM", count: 187, percentage: 15.0, trend: "down", change: -2.4 },
    { category: "CR", count: 165, percentage: 13.2, trend: "up", change: 3.7 },
    { category: "PE", count: 143, percentage: 11.5, trend: "neutral", change: 0.2 },
    { category: "Other", count: 112, percentage: 9.0, trend: "up", change: 1.9 },
  ];

  const languageStats = [
    { language: "English", count: 687, percentage: 55.1 },
    { language: "French", count: 423, percentage: 33.9 },
    { language: "Bilingual", count: 137, percentage: 11.0 },
  ];

  const recentActivity = [
    { date: "2025-09-30", jobs: 45, quality: 89 },
    { date: "2025-09-29", jobs: 52, quality: 86 },
    { date: "2025-09-28", jobs: 38, quality: 91 },
    { date: "2025-09-27", jobs: 41, quality: 88 },
    { date: "2025-09-26", jobs: 47, quality: 85 },
    { date: "2025-09-25", jobs: 39, quality: 90 },
    { date: "2025-09-24", jobs: 44, quality: 87 },
  ];

  const qualityMetrics = {
    accessibility: 84,
    languageBias: 91,
    clarityScore: 79,
    structureScore: 88,
    complianceRate: 94,
  };

  const processingStats = {
    avgUploadTime: "1.8 sec",
    avgParsingTime: "2.4 sec",
    avgAIProcessing: "3.2 sec",
    successRate: 96.8,
    errorRate: 3.2,
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Statistics & Analytics
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Comprehensive metrics and insights for job descriptions
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Time range selector */}
          <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            {(["7d", "30d", "90d", "1y"] as const).map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? "default" : "ghost"}
                size="sm"
                onClick={() => setTimeRange(range)}
                className="h-7 px-3"
              >
                {range === "7d" && "7 Days"}
                {range === "30d" && "30 Days"}
                {range === "90d" && "90 Days"}
                {range === "1y" && "1 Year"}
              </Button>
            ))}
          </div>

          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="default" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={FileText}
          label="Total Jobs"
          value={overallStats.totalJobs.toLocaleString()}
          trend="up"
          trendValue={`+${overallStats.growthRate}%`}
          iconColor="text-blue-600 dark:text-blue-400"
          bgColor="bg-blue-50 dark:bg-blue-900/20"
        />
        <StatCard
          icon={CheckCircle}
          label="Completed"
          value={overallStats.completedJobs.toLocaleString()}
          trend="up"
          trendValue="+8.2%"
          iconColor="text-green-600 dark:text-green-400"
          bgColor="bg-green-50 dark:bg-green-900/20"
        />
        <StatCard
          icon={Clock}
          label="In Progress"
          value={overallStats.inProgressJobs.toLocaleString()}
          trend="neutral"
          trendValue="±0%"
          iconColor="text-yellow-600 dark:text-yellow-400"
          bgColor="bg-yellow-50 dark:bg-yellow-900/20"
        />
        <StatCard
          icon={AlertTriangle}
          label="Failed"
          value={overallStats.failedJobs.toLocaleString()}
          trend="down"
          trendValue="-3.1%"
          iconColor="text-red-600 dark:text-red-400"
          bgColor="bg-red-50 dark:bg-red-900/20"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">
            <Activity className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="categories">
            <PieChart className="w-4 h-4 mr-2" />
            Categories
          </TabsTrigger>
          <TabsTrigger value="quality">
            <BarChart3 className="w-4 h-4 mr-2" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="performance">
            <LineChart className="w-4 h-4 mr-2" />
            Performance
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Activity Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <LineChart className="w-5 h-5" />
                  <span>Recent Activity</span>
                </CardTitle>
                <CardDescription>Jobs processed over the last 7 days</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((day, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-600 dark:text-slate-400">
                          {new Date(day.date).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {day.jobs} jobs
                        </span>
                      </div>
                      <div className="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="absolute inset-y-0 left-0 bg-blue-500 rounded-full"
                          style={{ width: `${(day.jobs / 60) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Language Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Globe className="w-5 h-5" />
                  <span>Language Distribution</span>
                </CardTitle>
                <CardDescription>Jobs by language</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {languageStats.map((lang, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {lang.language}
                        </span>
                        <span className="text-slate-600 dark:text-slate-400">
                          {lang.count} ({lang.percentage}%)
                        </span>
                      </div>
                      <div className="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="absolute inset-y-0 left-0 bg-green-500 rounded-full"
                          style={{ width: `${lang.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              label="Avg Processing Time"
              value={overallStats.avgProcessingTime}
              icon={Clock}
            />
            <MetricCard
              label="Quality Score"
              value={`${overallStats.qualityScore}%`}
              icon={BarChart3}
            />
            <MetricCard
              label="Success Rate"
              value={`${processingStats.successRate}%`}
              icon={CheckCircle}
            />
          </div>
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Categories</CardTitle>
              <CardDescription>Distribution and trends by classification</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {categoryStats.map((cat, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline" className="font-mono">
                          {cat.category}
                        </Badge>
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {cat.count} jobs ({cat.percentage}%)
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {cat.trend === "up" && (
                          <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
                        )}
                        {cat.trend === "down" && (
                          <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />
                        )}
                        <span
                          className={cn(
                            "text-sm font-medium",
                            cat.trend === "up" && "text-green-600 dark:text-green-400",
                            cat.trend === "down" && "text-red-600 dark:text-red-400",
                            cat.trend === "neutral" && "text-slate-600 dark:text-slate-400"
                          )}
                        >
                          {cat.change > 0 ? "+" : ""}
                          {cat.change}%
                        </span>
                      </div>
                    </div>
                    <div className="relative h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="absolute inset-y-0 left-0 bg-blue-500 rounded-full"
                        style={{ width: `${cat.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Quality Metrics</CardTitle>
                <CardDescription>Average scores across all jobs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <QualityMetric label="Accessibility" score={qualityMetrics.accessibility} />
                  <QualityMetric label="Language Bias" score={qualityMetrics.languageBias} />
                  <QualityMetric label="Clarity Score" score={qualityMetrics.clarityScore} />
                  <QualityMetric label="Structure Score" score={qualityMetrics.structureScore} />
                  <QualityMetric label="Compliance Rate" score={qualityMetrics.complianceRate} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quality Trends</CardTitle>
                <CardDescription>Quality improvements over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((day, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {new Date(day.date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500 rounded-full"
                            style={{ width: `${day.quality}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-900 dark:text-slate-100 w-12 text-right">
                          {day.quality}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Processing Performance</CardTitle>
                <CardDescription>Average processing times</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <ProcessingMetric
                    label="Upload Time"
                    value={processingStats.avgUploadTime}
                    percentage={30}
                  />
                  <ProcessingMetric
                    label="Parsing Time"
                    value={processingStats.avgParsingTime}
                    percentage={40}
                  />
                  <ProcessingMetric
                    label="AI Processing"
                    value={processingStats.avgAIProcessing}
                    percentage={53}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Success Rates</CardTitle>
                <CardDescription>Processing outcomes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        Success Rate
                      </span>
                      <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {processingStats.successRate}%
                      </span>
                    </div>
                    <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full"
                        style={{ width: `${processingStats.successRate}%` }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        Error Rate
                      </span>
                      <span className="text-2xl font-bold text-red-600 dark:text-red-400">
                        {processingStats.errorRate}%
                      </span>
                    </div>
                    <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-red-500 rounded-full"
                        style={{ width: `${processingStats.errorRate}%` }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * Stat Card Component
 */
interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  iconColor: string;
  bgColor: string;
}

function StatCard({ icon: Icon, label, value, trend, trendValue, iconColor, bgColor }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">{label}</p>
            <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
            {trend && trendValue && (
              <div className="flex items-center space-x-1">
                {trend === "up" && <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />}
                {trend === "down" && <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />}
                <span
                  className={cn(
                    "text-sm font-medium",
                    trend === "up" && "text-green-600 dark:text-green-400",
                    trend === "down" && "text-red-600 dark:text-red-400",
                    trend === "neutral" && "text-slate-600 dark:text-slate-400"
                  )}
                >
                  {trendValue}
                </span>
              </div>
            )}
          </div>
          <div className={cn("p-3 rounded-lg", bgColor)}>
            <Icon className={cn("w-6 h-6", iconColor)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Metric Card Component
 */
interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
}

function MetricCard({ label, value, icon: Icon }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400">{label}</p>
            <p className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-0.5">{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Quality Metric Component
 */
interface QualityMetricProps {
  label: string;
  score: number;
}

function QualityMetric({ label, score }: QualityMetricProps) {
  const getColor = (score: number) => {
    if (score >= 90) return "bg-green-500";
    if (score >= 75) return "bg-blue-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-900 dark:text-slate-100">{label}</span>
        <span className="text-slate-600 dark:text-slate-400">{score}%</span>
      </div>
      <div className="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div className={cn("absolute inset-y-0 left-0 rounded-full", getColor(score))} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

/**
 * Processing Metric Component
 */
interface ProcessingMetricProps {
  label: string;
  value: string;
  percentage: number;
}

function ProcessingMetric({ label, value, percentage }: ProcessingMetricProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-900 dark:text-slate-100">{label}</span>
        <span className="text-slate-600 dark:text-slate-400">{value}</span>
      </div>
      <div className="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-purple-500 rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
