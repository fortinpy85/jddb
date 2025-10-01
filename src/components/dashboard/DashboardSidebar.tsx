/**
 * Dashboard Sidebar Component
 * Persistent left panel showing statistics and system health
 * Displayed on landing page, can be hidden in focused views
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ProcessingStats } from "@/lib/types";
import {
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  TrendingUp,
  Activity,
  Database,
  Users,
  Zap,
  HardDrive,
  Cpu,
  Network,
  ChevronRight,
  ExternalLink,
  BarChart3,
} from "lucide-react";
import { PanelSection } from "@/components/layout/TwoPanelLayout";
import { CardSkeleton } from "@/components/ui/states";

interface DashboardSidebarProps {
  stats: ProcessingStats | null;
  onNavigateToStatistics?: () => void;
  onNavigateToSystemHealth?: () => void;
  collapsed?: boolean;
  className?: string;
}

export function DashboardSidebar({
  stats,
  onNavigateToStatistics,
  onNavigateToSystemHealth,
  collapsed = false,
  className,
}: DashboardSidebarProps) {
  // If collapsed, show minimal version
  if (collapsed) {
    return (
      <div
        className={cn("flex flex-col items-center space-y-4 py-4", className)}
      >
        <Button
          variant="ghost"
          size="sm"
          className="w-full p-2 shadow-button"
          onClick={onNavigateToStatistics}
          title="Statistics"
        >
          <BarChart3 className="w-5 h-5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="w-full p-2 shadow-button"
          onClick={onNavigateToSystemHealth}
          title="System Health"
        >
          <Activity className="w-5 h-5" />
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6 p-4", className)}>
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Dashboard
          </h2>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Quick overview of your job database
        </p>
      </div>

      {/* Statistics Section */}
      <PanelSection
        title="Statistics"
        icon={BarChart3}
        collapsible
        defaultCollapsed={false}
      >
        <StatisticsCards
          stats={stats}
          onNavigateToStatistics={onNavigateToStatistics}
        />
      </PanelSection>

      {/* System Health Section */}
      <PanelSection
        title="System Health"
        icon={Activity}
        collapsible
        defaultCollapsed={false}
      >
        <SystemHealthCards
          onNavigateToSystemHealth={onNavigateToSystemHealth}
        />
      </PanelSection>

      {/* Recent Activity Section */}
      <PanelSection
        title="Recent Activity"
        icon={Clock}
        collapsible
        defaultCollapsed={true}
      >
        <RecentActivityList />
      </PanelSection>
    </div>
  );
}

/**
 * Statistics Cards Component
 * Shows job counts by category with click-to-drill-down
 */
interface StatisticsCardsProps {
  stats: ProcessingStats | null;
  onNavigateToStatistics?: () => void;
}

function StatisticsCards({
  stats,
  onNavigateToStatistics,
}: StatisticsCardsProps) {
  // Show skeleton loader when stats are loading
  if (!stats) {
    return <CardSkeleton count={4} variant="stat" />;
  }

  const categories = [
    {
      label: "Total Jobs",
      value: stats?.total_jobs ?? 0,
      icon: FileText,
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      trend: "+12%",
    },
    {
      label: "Completed",
      value: stats?.jobs_completed ?? 0,
      icon: CheckCircle,
      color: "text-green-600 dark:text-green-400",
      bgColor: "bg-green-50 dark:bg-green-900/20",
      trend: "+5%",
    },
    {
      label: "In Progress",
      value: stats?.jobs_in_progress ?? 0,
      icon: Clock,
      color: "text-yellow-600 dark:text-yellow-400",
      bgColor: "bg-yellow-50 dark:bg-yellow-900/20",
      trend: "+18%",
    },
    {
      label: "Failed",
      value: stats?.jobs_failed ?? 0,
      icon: AlertCircle,
      color: "text-red-600 dark:text-red-400",
      bgColor: "bg-red-50 dark:bg-red-900/20",
      trend: "-3%",
    },
  ];

  return (
    <div className="space-y-3">
      {categories.map((category, index) => (
        <button
          key={index}
          onClick={onNavigateToStatistics}
          className="w-full text-left group"
        >
          <Card className="elevation-1 shadow-hover border-slate-200/50 dark:border-slate-700/50">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={cn("p-2 rounded-lg", category.bgColor)}>
                    <category.icon className={cn("w-4 h-4", category.color)} />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                      {category.label}
                    </p>
                    <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                      {category.value.toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end space-y-1">
                  <Badge
                    variant="secondary"
                    className={cn(
                      "text-xs",
                      category.trend.startsWith("+")
                        ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                        : "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
                    )}
                  >
                    {category.trend}
                  </Badge>
                  <ChevronRight className="w-4 h-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </CardContent>
          </Card>
        </button>
      ))}

      {/* View All Statistics Button */}
      <Button
        variant="outline"
        size="sm"
        className="w-full mt-2 shadow-button"
        onClick={onNavigateToStatistics}
      >
        <BarChart3 className="w-4 h-4 mr-2" />
        View All Statistics
        <ExternalLink className="w-3 h-3 ml-auto" />
      </Button>
    </div>
  );
}

/**
 * System Health Cards Component
 * Shows system performance indicators with click-to-drill-down
 */
interface SystemHealthCardsProps {
  onNavigateToSystemHealth?: () => void;
}

function SystemHealthCards({
  onNavigateToSystemHealth,
}: SystemHealthCardsProps) {
  const healthMetrics = [
    {
      label: "API Performance",
      value: "98.5%",
      status: "good",
      icon: Zap,
      subtitle: "Avg response: 124ms",
    },
    {
      label: "Database",
      value: "Healthy",
      status: "good",
      icon: HardDrive,
      subtitle: "23% used",
    },
    {
      label: "AI Services",
      value: "Active",
      status: "good",
      icon: Cpu,
      subtitle: "1.2K requests today",
    },
    {
      label: "Network",
      value: "Stable",
      status: "warning",
      icon: Network,
      subtitle: "Latency: 45ms",
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "good":
        return "text-green-600 dark:text-green-400";
      case "warning":
        return "text-yellow-600 dark:text-yellow-400";
      case "error":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-slate-600 dark:text-slate-400";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "good":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400";
      case "warning":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400";
      case "error":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-900/20 dark:text-slate-400";
    }
  };

  return (
    <div className="space-y-3">
      {healthMetrics.map((metric, index) => (
        <button
          key={index}
          onClick={onNavigateToSystemHealth}
          className="w-full text-left group"
        >
          <Card className="elevation-1 shadow-hover border-slate-200/50 dark:border-slate-700/50">
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <metric.icon
                    className={cn("w-4 h-4", getStatusColor(metric.status))}
                  />
                  <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    {metric.label}
                  </p>
                </div>
                <Badge
                  variant="secondary"
                  className={cn("text-xs", getStatusBadge(metric.status))}
                >
                  {metric.value}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-500 ml-6">
                {metric.subtitle}
              </p>
            </CardContent>
          </Card>
        </button>
      ))}

      {/* View System Health Button */}
      <Button
        variant="outline"
        size="sm"
        className="w-full mt-2 shadow-button"
        onClick={onNavigateToSystemHealth}
      >
        <Activity className="w-4 h-4 mr-2" />
        System Dashboard
        <ExternalLink className="w-3 h-3 ml-auto" />
      </Button>
    </div>
  );
}

/**
 * Recent Activity List Component
 * Shows recent actions in the system
 */
function RecentActivityList() {
  const activities = [
    {
      action: "Job created",
      job: "EX-01 Director",
      user: "Alice J.",
      time: "5 min ago",
      icon: FileText,
    },
    {
      action: "Job approved",
      job: "AS-06 Analyst",
      user: "Bob S.",
      time: "12 min ago",
      icon: CheckCircle,
    },
    {
      action: "Translation completed",
      job: "PM-05 Manager",
      user: "AI Service",
      time: "25 min ago",
      icon: Users,
    },
  ];

  return (
    <div className="space-y-2">
      {activities.map((activity, index) => (
        <div
          key={index}
          className="flex items-start space-x-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        >
          <activity.icon className="w-4 h-4 text-slate-400 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate">
              {activity.action}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-500 truncate">
              {activity.job} • {activity.user}
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-600">
              {activity.time}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
