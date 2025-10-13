"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { apiClient } from "@/lib/api";
import { logger } from "@/utils/logger";
import {
  Database,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  BarChart3,
  Users,
  FileText,
  Cpu,
  Shield,
  RefreshCw,
  Zap,
  Target,
} from "lucide-react";
import SkeletonLoader from "@/components/ui/skeleton";
import { AnimatedCounter } from "./ui/animated-counter";
import type {
  IngestionStats,
  TaskStats,
  ResilienceStats,
  SkillsStatsResponse,
  TopSkillsResponse,
  SkillTypesResponse,
  SkillsInventoryResponse,
} from "@/lib/types";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function StatsDashboard() {
  const [ingestionStats, setIngestionStats] = useState<IngestionStats | null>(
    null,
  );
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null);
  const [resilienceStats, setResilienceStats] =
    useState<ResilienceStats | null>(null);
  const [skillsStats, setSkillsStats] = useState<SkillsStatsResponse | null>(
    null,
  );
  const [topSkills, setTopSkills] = useState<TopSkillsResponse | null>(null);
  const [skillTypes, setSkillTypes] = useState<SkillTypesResponse | null>(null);
  const [skillsInventory, setSkillsInventory] =
    useState<SkillsInventoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAllStats = async () => {
    try {
      setLoading(true);
      const [
        ingestion,
        tasks,
        resilience,
        skills,
        topSkillsData,
        skillTypesData,
        inventory,
      ] = await Promise.all([
        apiClient.getIngestionStats(),
        apiClient.getTaskStats(),
        apiClient.getResilienceStatus(),
        apiClient.getSkillsStats().catch(() => null),
        apiClient.getTopSkills({ limit: 15 }).catch(() => null),
        apiClient.getSkillTypes().catch(() => null),
        apiClient
          .getSkillsInventory({ limit: 20, offset: 0 })
          .catch(() => null),
      ]);

      setIngestionStats(ingestion);
      setTaskStats(tasks);
      setResilienceStats(resilience);
      setSkillsStats(skills);
      setTopSkills(topSkillsData);
      setSkillTypes(skillTypesData);
      setSkillsInventory(inventory);
      setLastUpdated(new Date());
    } catch (error) {
      logger.error("Failed to fetch statistics:", error);
    } finally {
      setLoading(false);
    }
  };

  const resetCircuitBreakers = async () => {
    try {
      await apiClient.resetCircuitBreakers();
      // Refresh resilience stats after reset
      const resilience = await apiClient.getResilienceStatus();
      setResilienceStats(resilience);
    } catch (error) {
      logger.error("Failed to reset circuit breakers:", error);
    }
  };

  useEffect(() => {
    fetchAllStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchAllStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <SkeletonLoader type="stats-dashboard" />;
  }

  const getHealthStatusColor = (health: string) => {
    switch (health) {
      case "healthy":
        return "text-green-600 bg-green-100";
      case "degraded":
        return "text-orange-600 bg-orange-100";
      case "critical":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getCircuitBreakerStateColor = (state: string) => {
    switch (state) {
      case "closed":
        return "text-green-600 bg-green-100";
      case "half_open":
        return "text-yellow-600 bg-yellow-100";
      case "open":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="w-6 h-6 mr-2" />
            System Statistics Dashboard
          </h2>
          <p className="text-gray-600 mt-1">
            Real-time monitoring of ingestion, processing, and system health
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <Button onClick={fetchAllStats} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5 max-w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="processing">Processing</TabsTrigger>
          <TabsTrigger value="skills">Skills Analytics</TabsTrigger>
          <TabsTrigger value="tasks">Task Queue</TabsTrigger>
          <TabsTrigger value="health">System Health</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Database className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Total Jobs
                  </p>
                  <AnimatedCounter
                    end={ingestionStats?.total_jobs || 0}
                    className="text-2xl font-bold"
                    duration={1500}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Processed</p>
                  <AnimatedCounter
                    end={ingestionStats?.processing_status.completed || 0}
                    className="text-2xl font-bold"
                    duration={1500}
                    delay={100}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Zap className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Embeddings
                  </p>
                  <AnimatedCounter
                    end={
                      ingestionStats?.content_quality.jobs_with_embeddings || 0
                    }
                    className="text-2xl font-bold"
                    duration={1500}
                    delay={200}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Activity className="w-6 h-6 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Last 7 Days
                  </p>
                  <AnimatedCounter
                    end={ingestionStats?.recent_activity.jobs_last_7_days || 0}
                    className="text-2xl font-bold"
                    duration={1500}
                    delay={300}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Content Quality Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  Content Quality Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      Section Coverage
                    </span>
                    <span className="text-sm font-bold">
                      {ingestionStats?.content_quality.section_coverage_rate.toFixed(
                        1,
                      )}
                      %
                    </span>
                  </div>
                  <Progress
                    value={
                      ingestionStats?.content_quality.section_coverage_rate || 0
                    }
                  />

                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      Metadata Coverage
                    </span>
                    <span className="text-sm font-bold">
                      {ingestionStats?.content_quality.metadata_coverage_rate.toFixed(
                        1,
                      )}
                      %
                    </span>
                  </div>
                  <Progress
                    value={
                      ingestionStats?.content_quality.metadata_coverage_rate ||
                      0
                    }
                  />

                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      Embedding Coverage
                    </span>
                    <span className="text-sm font-bold">
                      {ingestionStats?.content_quality.embedding_coverage_rate.toFixed(
                        1,
                      )}
                      %
                    </span>
                  </div>
                  <Progress
                    value={
                      ingestionStats?.content_quality.embedding_coverage_rate ||
                      0
                    }
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Jobs in Last 7 Days
                    </span>
                    <span className="text-lg font-bold">
                      {ingestionStats?.recent_activity.jobs_last_7_days || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Daily Average</span>
                    <span className="text-lg font-bold">
                      {ingestionStats?.recent_activity.daily_average.toFixed(
                        1,
                      ) || 0}
                    </span>
                  </div>
                  {ingestionStats?.last_updated && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        Last Updated
                      </span>
                      <span className="text-sm">
                        {new Date(ingestionStats.last_updated).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Processing Tab */}
        <TabsContent value="processing" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Classification Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Jobs by Classification
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(ingestionStats?.by_classification || {})
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 8)
                    .map(([classification, count]) => (
                      <div
                        key={classification}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm font-medium">
                          {classification}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{
                                width: `${(count / (ingestionStats?.total_jobs || 1)) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-semibold w-8 text-right">
                            {count}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            {/* Section Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Content Sections
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(ingestionStats?.section_distribution || {})
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 8)
                    .map(([section, count]) => (
                      <div
                        key={section}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm font-medium capitalize">
                          {section.replace(/_/g, " ")}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-600 h-2 rounded-full"
                              style={{
                                width: `${(count / (ingestionStats?.total_jobs || 1)) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-semibold w-8 text-right">
                            {count}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Processing Status Details */}
          <Card>
            <CardHeader>
              <CardTitle>Processing Status Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {ingestionStats?.processing_status.completed || 0}
                  </div>
                  <div className="text-sm text-gray-600">Fully Processed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {ingestionStats?.processing_status.needs_embeddings || 0}
                  </div>
                  <div className="text-sm text-gray-600">Need Embeddings</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {ingestionStats?.processing_status.needs_sections || 0}
                  </div>
                  <div className="text-sm text-gray-600">Need Sections</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {ingestionStats?.processing_status.needs_metadata || 0}
                  </div>
                  <div className="text-sm text-gray-600">Need Metadata</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-600">
                    {ingestionStats?.processing_status.partial || 0}
                  </div>
                  <div className="text-sm text-gray-600">
                    Partial Processing
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Skills Analytics Tab */}
        <TabsContent value="skills" className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Target className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Total Skills
                  </p>
                  <AnimatedCounter
                    end={skillsStats?.total_unique_skills || 0}
                    className="text-2xl font-bold"
                    duration={1500}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Coverage</p>
                  <p className="text-2xl font-bold">
                    {skillsStats?.skills_coverage_percentage.toFixed(1) || 0}%
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Avg Confidence
                  </p>
                  <p className="text-2xl font-bold">
                    {skillsStats?.avg_confidence_score.toFixed(1) || 0}%
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Database className="w-6 h-6 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Unique Skills
                  </p>
                  <AnimatedCounter
                    end={skillsStats?.total_unique_skills || 0}
                    className="text-2xl font-bold"
                    duration={1500}
                    delay={100}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Skills Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Top 15 Skills
                </CardTitle>
              </CardHeader>
              <CardContent>
                {topSkills && topSkills.top_skills.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={topSkills.top_skills}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="skill_name" type="category" width={90} />
                      <RechartsTooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                                <p className="font-semibold">
                                  {payload[0].payload.skill_name}
                                </p>
                                <p className="text-sm text-gray-600">
                                  Jobs: {payload[0].payload.job_count}
                                </p>
                                <p className="text-sm text-gray-600">
                                  {payload[0].payload.percentage.toFixed(1)}% of
                                  all jobs
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="job_count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    No skills data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Skill Types Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="w-5 h-5 mr-2" />
                  Skills by Type
                </CardTitle>
              </CardHeader>
              <CardContent>
                {skillTypes && skillTypes.skill_types.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <PieChart>
                      <Pie
                        data={skillTypes.skill_types.map((st) => ({
                          ...st,
                          name: st.type || "Unknown",
                          value: st.skill_count,
                        }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry: any) => {
                          const total = skillTypes.skill_types.reduce(
                            (sum, t) => sum + t.skill_count,
                            0,
                          );
                          const percentage =
                            ((entry.value as number) / total) * 100;
                          return `${entry.name} (${percentage.toFixed(1)}%)`;
                        }}
                        outerRadius={120}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {skillTypes.skill_types.map((entry, index) => {
                          const colors = [
                            "#3b82f6",
                            "#10b981",
                            "#f59e0b",
                            "#ef4444",
                            "#8b5cf6",
                            "#ec4899",
                            "#06b6d4",
                            "#84cc16",
                          ];
                          return (
                            <Cell
                              key={`cell-${index}`}
                              fill={colors[index % colors.length]}
                            />
                          );
                        })}
                      </Pie>
                      <RechartsTooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const total = skillTypes.skill_types.reduce(
                              (sum, t) => sum + t.skill_count,
                              0,
                            );
                            const percentage = (payload[0].value / total) * 100;
                            return (
                              <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                                <p className="font-semibold">
                                  {payload[0].payload.type || "Unknown"}
                                </p>
                                <p className="text-sm text-gray-600">
                                  Count: {payload[0].payload.skill_count}
                                </p>
                                <p className="text-sm text-gray-600">
                                  {percentage.toFixed(1)}% of all skills
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    No skill types data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Skills Inventory Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Skills Inventory
              </CardTitle>
            </CardHeader>
            <CardContent>
              {skillsInventory && skillsInventory.skills.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left p-3 font-medium">
                          Skill Name
                        </th>
                        <th className="text-left p-3 font-medium">Type</th>
                        <th className="text-right p-3 font-medium">Jobs</th>
                        <th className="text-right p-3 font-medium">
                          Avg Confidence
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {skillsInventory.skills.map((skill) => (
                        <tr
                          key={skill.lightcast_id}
                          className="hover:bg-gray-50"
                        >
                          <td className="p-3 font-medium">{skill.name}</td>
                          <td className="p-3">
                            {skill.skill_type ? (
                              <Badge variant="secondary">
                                {skill.skill_type}
                              </Badge>
                            ) : (
                              <span className="text-gray-400 text-xs">
                                Unknown
                              </span>
                            )}
                          </td>
                          <td className="p-3 text-right">{skill.job_count}</td>
                          <td className="p-3 text-right">
                            {skill.avg_confidence ? (
                              <span className="font-medium">
                                {(skill.avg_confidence * 100).toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {skillsInventory.total > skillsInventory.skills.length && (
                    <div className="text-center text-sm text-gray-500 mt-4">
                      Showing {skillsInventory.skills.length} of{" "}
                      {skillsInventory.total} skills
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-12">
                  No skills inventory data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Active Tasks
                  </p>
                  <p className="text-2xl font-bold">
                    {taskStats?.task_stats.active_tasks || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Clock className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Scheduled</p>
                  <p className="text-2xl font-bold">
                    {taskStats?.task_stats.scheduled_tasks || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Users className="w-6 h-6 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Workers</p>
                  <p className="text-2xl font-bold">
                    {taskStats?.task_stats.workers_online || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex items-center p-6">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Cpu className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Reserved</p>
                  <p className="text-2xl font-bold">
                    {taskStats?.task_stats.reserved_tasks || 0}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Queue Stats */}
          {taskStats && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Queue Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(taskStats.task_stats.queue_stats).map(
                      ([queue, stats]) => (
                        <div
                          key={queue}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm font-medium capitalize">
                            {queue}
                          </span>
                          <div className="flex items-center space-x-4">
                            <div className="text-sm">
                              <span className="text-blue-600">
                                {stats.active}
                              </span>{" "}
                              active
                            </div>
                            <div className="text-sm">
                              <span className="text-orange-600">
                                {stats.reserved}
                              </span>{" "}
                              reserved
                            </div>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Task Types</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(taskStats.task_stats.task_types)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 5)
                      .map(([task, count]) => (
                        <div
                          key={task}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm font-medium">
                            {task.split(".").pop()?.replace(/_/g, " ")}
                          </span>
                          <span className="text-sm font-semibold">{count}</span>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Health Tab */}
        <TabsContent value="health" className="space-y-6">
          {/* Overall Health Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  System Health Overview
                </div>
                <Badge
                  className={getHealthStatusColor(
                    resilienceStats?.overall_health || "unknown",
                  )}
                >
                  {resilienceStats?.overall_health || "Unknown"}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {resilienceStats?.degraded_services &&
                  resilienceStats.degraded_services.length > 0 && (
                    <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                      <h4 className="font-medium text-orange-900 mb-2">
                        Degraded Services
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {resilienceStats.degraded_services.map((service) => (
                          <Badge
                            key={service}
                            className="bg-orange-100 text-orange-800"
                          >
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Recommendations */}
                {resilienceStats?.recommendations && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-900">
                      Recommendations
                    </h4>
                    <ul className="space-y-1">
                      {resilienceStats.recommendations.map((rec, index) => (
                        <li
                          key={index}
                          className="text-sm text-gray-700 flex items-start"
                        >
                          <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Circuit Breaker Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Circuit Breaker Status
                <Button
                  onClick={resetCircuitBreakers}
                  variant="outline"
                  size="sm"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reset All
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(resilienceStats?.circuit_breakers || {}).map(
                  ([name, breaker]) => (
                    <div key={name} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h5 className="font-medium">
                          {name.replace(/_/g, " ")}
                        </h5>
                        <Badge
                          className={getCircuitBreakerStateColor(breaker.state)}
                        >
                          {breaker.state}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Requests</span>
                          <div className="font-semibold">
                            {breaker.failure_count || 0}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Failures</span>
                          <div className="font-semibold text-red-600">
                            {breaker.failure_count}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Success Rate</span>
                          <div className="font-semibold">
                            {breaker.failure_threshold > 0
                              ? (
                                  (1 -
                                    breaker.failure_count /
                                      breaker.failure_threshold) *
                                  100
                                ).toFixed(1)
                              : "100.0"}
                            %
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Threshold</span>
                          <div className="font-semibold">
                            {breaker.failure_threshold}
                          </div>
                        </div>
                      </div>

                      {breaker.failure_count > 0 && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span>Failure Rate</span>
                            <span>
                              {breaker.failure_threshold > 0
                                ? (
                                    (breaker.failure_count /
                                      breaker.failure_threshold) *
                                    100
                                  ).toFixed(1)
                                : "0.0"}
                              %
                            </span>
                          </div>
                          <Progress
                            value={
                              breaker.failure_threshold > 0
                                ? (breaker.failure_count /
                                    breaker.failure_threshold) *
                                  100
                                : 0
                            }
                            className="h-2"
                          />
                        </div>
                      )}
                    </div>
                  ),
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default React.memo(StatsDashboard);
