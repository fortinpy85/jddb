"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import JobList from "@/components/JobList";
import BulkUpload from "@/components/BulkUpload";
import JobDetails from "@/components/JobDetails";
import SearchInterface from "@/components/SearchInterface";
import JobComparison from "@/components/JobComparison";
import StatsDashboard from "@/components/StatsDashboard";
import type { JobDescription } from "@/lib/types";
import { getClassificationLevel } from "@/lib/utils";
import { useStore } from "@/lib/store";
import {
  Database,
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  FileText,
  Upload,
  Search,
  Users,
  TrendingUp,
  Activity,
  GitCompare,
} from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import { ToastProvider } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import ThemeToggle from "@/components/ui/theme-toggle";
import { ThemeProvider } from "@/components/ui/theme-provider";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const { stats, jobs, selectedJob, fetchJobs, fetchStats, selectJob } =
    useStore();

  const recentJobs = jobs.slice(0, 5);

  // Tab navigation order
  const tabOrder = [
    "dashboard",
    "jobs",
    "upload",
    "search",
    "compare",
    "statistics",
  ];
  const currentTabIndex = tabOrder.indexOf(activeTab);

  // Keyboard navigation
  useKeyboardNavigation({
    onArrowLeft: () => {
      if (currentTabIndex > 0) {
        setActiveTab(tabOrder[currentTabIndex - 1]);
      }
    },
    onArrowRight: () => {
      if (currentTabIndex < tabOrder.length - 1) {
        setActiveTab(tabOrder[currentTabIndex + 1]);
      }
    },
    onCtrlF: () => {
      setActiveTab("search");
      // Focus search input after navigation
      setTimeout(() => {
        const searchInput = document.querySelector(
          'input[type="search"]',
        ) as HTMLInputElement;
        if (searchInput) searchInput.focus();
      }, 100);
    },
    onCtrlK: () => {
      setActiveTab("search");
    },
    onEscape: () => {
      if (selectedJob) {
        handleBackFromDetails();
      }
    },
  });

  // Load dashboard data
  useEffect(() => {
    fetchJobs(true);
    fetchStats();
  }, [fetchJobs, fetchStats]);

  // Handle job selection
  const handleJobSelect = (job: JobDescription) => {
    selectJob(job);
    setActiveTab("job-details");
  };

  // Handle back from job details
  const handleBackFromDetails = () => {
    selectJob(null);
    setActiveTab("jobs");
  };

  // Handle upload completion
  const handleUploadComplete = () => {
    // Refresh stats after upload
    fetchStats();
    setActiveTab("jobs"); // Navigate to jobs list
  };

  // Stats cards data
  const statsCards = [
    {
      title: "Total Jobs",
      value: stats?.total_jobs || 0,
      icon: Database,
      color: "text-indigo-600",
      bgColor: "bg-gradient-to-br from-indigo-50 to-blue-50",
      tooltip: "Total number of job descriptions in the database",
    },
    {
      title: "Completed",
      value: stats?.processing_status?.completed || 0,
      icon: CheckCircle,
      color: "text-emerald-600",
      bgColor: "bg-gradient-to-br from-emerald-50 to-green-50",
      tooltip: "Jobs that have been fully processed and are ready for use",
    },
    {
      title: "Need Review",
      value: stats?.processing_status?.needs_review || 0,
      icon: AlertCircle,
      color: "text-amber-600",
      bgColor: "bg-gradient-to-br from-amber-50 to-orange-50",
      tooltip: "Jobs that require manual review due to processing issues",
    },
    {
      title: "Processing",
      value:
        (stats?.processing_status?.processing || 0) +
        (stats?.processing_status?.pending || 0),
      icon: Clock,
      color: "text-violet-600",
      bgColor: "bg-gradient-to-br from-violet-50 to-purple-50",
      tooltip: "Jobs currently being processed or pending processing",
    },
  ];

  return (
    <ThemeProvider defaultTheme="system" enableSystem>
      <ErrorBoundaryWrapper showDetails={process.env.NODE_ENV === "development"}>
        <ToastProvider>
          <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-900 dark:via-slate-800/30 dark:to-slate-900/20 transition-colors duration-300">
          {/* Header - Mobile Optimized */}
          <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm shadow-lg border-b border-white/20 dark:border-slate-700/20 sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between min-h-[4rem] sm:h-16 py-2 sm:py-0">
                {/* Logo and Title - Mobile Responsive */}
                <div className="flex items-center group flex-shrink-0">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg blur opacity-20 group-hover:opacity-30 transition-opacity duration-300"></div>
                    <Database className="relative w-6 h-6 sm:w-8 sm:h-8 text-blue-600 mr-2 sm:mr-3 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <h1 className="text-sm sm:text-lg lg:text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 transition-all duration-300">
                    <span className="hidden sm:inline">Job Description Database</span>
                    <span className="sm:hidden">JDDB</span>
                    <span className="hidden lg:inline"> (JDDB)</span>
                  </h1>
                </div>

                {/* Stats and Theme Toggle - Mobile Responsive */}
                <div className="flex items-center space-x-2 sm:space-x-4 min-w-0">
                  {/* Theme Toggle */}
                  <ThemeToggle size="sm" className="flex-shrink-0" />

                  {/* Stats */}
                  <div className="text-xs sm:text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100/50 dark:bg-slate-800/50 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 truncate">
                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                      {stats.total_jobs}
                    </span>
                    <span className="hidden xs:inline"> jobs</span>
                    <span className="hidden sm:inline"> • Last updated:</span>
                    <span className="hidden md:inline text-slate-500 dark:text-slate-400">
                      {" "}
                      {stats.last_updated
                        ? new Date(stats.last_updated).toLocaleDateString()
                        : "Never"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              {/* Tab Navigation - Mobile First Design */}
              <div className="mb-6 sm:mb-8">
                {/* Mobile: Horizontal scroll tabs */}
                <div className="sm:hidden">
                  <div className="overflow-x-auto scrollbar-hide">
                    <TabsList className="flex w-max min-w-full gap-2 p-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-white/30 dark:border-slate-700/30 shadow-lg rounded-xl">
                      <TabsTrigger
                        value="dashboard"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        <BarChart3 className="w-4 h-4" />
                        Dashboard
                      </TabsTrigger>
                      <TabsTrigger
                        value="jobs"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        <FileText className="w-4 h-4" />
                        Jobs
                      </TabsTrigger>
                      <TabsTrigger
                        value="upload"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        <Upload className="w-4 h-4" />
                        Upload
                      </TabsTrigger>
                      <TabsTrigger
                        value="search"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        <Search className="w-4 h-4" />
                        Search
                      </TabsTrigger>
                      <TabsTrigger
                        value="compare"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        <GitCompare className="w-4 h-4" />
                        Compare
                      </TabsTrigger>
                      <TabsTrigger
                        value="statistics"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        <Activity className="w-4 h-4" />
                        Statistics
                      </TabsTrigger>
                    </TabsList>
                  </div>
                </div>

                {/* Desktop/Tablet: Grid layout */}
                <TabsList className="hidden sm:grid w-full grid-cols-3 lg:grid-cols-6 gap-1 bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm border border-white/20 dark:border-slate-700/20 shadow-lg rounded-xl p-1">
                  <TabsTrigger
                    value="dashboard"
                    className="flex items-center justify-center lg:justify-start gap-2 p-3 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    <BarChart3 className="w-4 h-4" />
                    <span className="hidden lg:inline">Dashboard</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="jobs"
                    className="flex items-center justify-center lg:justify-start gap-2 p-3 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    <FileText className="w-4 h-4" />
                    <span className="hidden lg:inline">Jobs</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="upload"
                    className="flex items-center justify-center lg:justify-start gap-2 p-3 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    <Upload className="w-4 h-4" />
                    <span className="hidden lg:inline">Upload</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="search"
                    className="flex items-center justify-center lg:justify-start gap-2 p-3 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    <Search className="w-4 h-4" />
                    <span className="hidden lg:inline">Search</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="compare"
                    className="flex items-center justify-center lg:justify-start gap-2 p-3 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    <GitCompare className="w-4 h-4" />
                    <span className="hidden lg:inline">Compare</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="statistics"
                    className="flex items-center justify-center lg:justify-start gap-2 p-3 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    <Activity className="w-4 h-4" />
                    <span className="hidden lg:inline">Statistics</span>
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* Dashboard Tab */}
              <TabsContent value="dashboard" className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {statsCards.map((card, index) => (
                    <Card
                      key={index}
                      className="group hover-lift stagger-item cursor-pointer border border-white/20 dark:border-slate-700/20 hover:border-blue-200/50 dark:hover:border-blue-400/50 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm hover:bg-white/90 dark:hover:bg-slate-800/90 transition-all duration-300 enhanced-hover glow-on-hover magnetic-hover"
                      title={card.tooltip}
                    >
                      <CardContent className="pt-6 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-50/40 to-indigo-50/20 rounded-full -mr-16 -mt-16 group-hover:scale-110 transition-transform duration-500"></div>
                        <div className="relative z-10 flex items-center justify-between">
                          <div>
                            <p className="text-sm font-semibold text-slate-600 group-hover:text-blue-700 transition-colors duration-300 tracking-wide">
                              {card.title}
                            </p>
                            <AnimatedCounter
                              end={card.value}
                              duration={1500}
                              delay={index * 200}
                              className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-blue-900 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 transition-all duration-300"
                            />
                          </div>
                          <div
                            className={`${card.bgColor} p-4 rounded-xl group-hover:scale-110 transition-all duration-300 shadow-lg group-hover:shadow-xl relative float-animation sparkle-icon`}
                          >
                            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-xl"></div>
                            <card.icon
                              className={`relative w-6 h-6 ${card.color} group-hover:rotate-12 transition-transform duration-500 bounce-in`}
                              style={{ animationDelay: `${index * 300}ms` }}
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Classification Distribution */}
                  <Card className="hover-lift bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-white/20 dark:border-slate-700/20 hover:bg-white/90 dark:hover:bg-slate-800/90">
                    <CardHeader className="relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-50/30 to-indigo-50/20 rounded-full -mr-12 -mt-12"></div>
                      <CardTitle className="flex items-center relative z-10 text-slate-800 font-bold tracking-wide">
                        <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-2 rounded-lg mr-3 shadow-lg pulse-on-hover">
                          <Users className="w-5 h-5 text-white" />
                        </div>
                        Jobs by Classification
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(stats.by_classification).map(
                          ([classification, count]) => (
                            <div
                              key={classification}
                              className="flex items-center justify-between group hover:bg-blue-50/50 p-2 -m-2 rounded-lg transition-all duration-200"
                            >
                              <div className="flex items-center">
                                <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full mr-3 group-hover:scale-110 transition-transform duration-200 shadow-sm"></div>
                                <span className="text-sm font-semibold text-slate-700 group-hover:text-blue-700 transition-colors duration-200">
                                  {classification}
                                </span>
                                <span className="text-xs text-slate-500 ml-2 font-medium">
                                  ({getClassificationLevel(classification)})
                                </span>
                              </div>
                              <span className="text-sm font-bold text-slate-800 bg-slate-100/50 px-2 py-1 rounded-full group-hover:bg-blue-100/50 group-hover:text-blue-700 transition-all duration-200">
                                {count}
                              </span>
                            </div>
                          ),
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Language Distribution */}
                  <Card className="hover-lift bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-white/20 dark:border-slate-700/20 hover:bg-white/90 dark:hover:bg-slate-800/90">
                    <CardHeader className="relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-emerald-50/30 to-green-50/20 rounded-full -mr-12 -mt-12"></div>
                      <CardTitle className="flex items-center relative z-10 text-slate-800 font-bold tracking-wide">
                        <div className="bg-gradient-to-r from-emerald-500 to-green-500 p-2 rounded-lg mr-3 shadow-lg pulse-on-hover">
                          <TrendingUp className="w-5 h-5 text-white" />
                        </div>
                        Jobs by Language
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(stats.by_language).map(
                          ([language, count]) => (
                            <div
                              key={language}
                              className="flex items-center justify-between group hover:bg-emerald-50/50 p-2 -m-2 rounded-lg transition-all duration-200"
                            >
                              <div className="flex items-center">
                                <div className="w-3 h-3 bg-gradient-to-r from-emerald-500 to-green-500 rounded-full mr-3 group-hover:scale-110 transition-transform duration-200 shadow-sm"></div>
                                <span className="text-sm font-semibold text-slate-700 group-hover:text-emerald-700 transition-colors duration-200">
                                  {language === "en"
                                    ? "English"
                                    : language === "fr"
                                      ? "French"
                                      : language}
                                </span>
                              </div>
                              <span className="text-sm font-bold text-slate-800 bg-slate-100/50 px-2 py-1 rounded-full group-hover:bg-emerald-100/50 group-hover:text-emerald-700 transition-all duration-200">
                                {count}
                              </span>
                            </div>
                          ),
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Jobs */}
                <Card className="bg-white/70 backdrop-blur-sm border border-white/20 hover:bg-white/90 transition-all duration-300 hover:shadow-xl">
                  <CardHeader className="relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-violet-50/30 to-purple-50/20 rounded-full -mr-12 -mt-12"></div>
                    <CardTitle className="flex items-center justify-between relative z-10">
                      <div className="flex items-center text-slate-800 font-bold tracking-wide">
                        <div className="bg-gradient-to-r from-violet-500 to-purple-500 p-2 rounded-lg mr-3 shadow-lg">
                          <Activity className="w-5 h-5 text-white" />
                        </div>
                        Recent Job Descriptions
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab("jobs")}
                        className="hover:bg-violet-50 hover:border-violet-300 hover:text-violet-700 transition-all duration-200 hover:scale-105"
                      >
                        View All
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {recentJobs.length > 0 ? (
                      <div className="space-y-3">
                        {recentJobs.map((job) => (
                          <div
                            key={job.id}
                            className="group flex items-center justify-between p-4 border border-slate-200/50 rounded-xl hover:bg-gradient-to-r hover:from-violet-50/50 hover:to-purple-50/30 cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:border-violet-200/50 card-interactive"
                            onClick={() => handleJobSelect(job)}
                          >
                            <div className="relative z-10">
                              <p className="font-semibold text-slate-800 group-hover:text-violet-700 transition-colors duration-200">
                                {job.title}
                              </p>
                              <p className="text-sm text-slate-500 font-medium group-hover:text-violet-600 transition-colors duration-200">
                                {job.job_number} • {job.classification}
                              </p>
                            </div>
                            <div className="text-right relative z-10">
                              <p className="text-sm text-slate-500 bg-slate-100/50 px-2 py-1 rounded-full group-hover:bg-violet-100/50 group-hover:text-violet-600 transition-all duration-200 font-medium">
                                {job.processed_date
                                  ? new Date(
                                      job.processed_date,
                                    ).toLocaleDateString()
                                  : "Not processed"}
                              </p>
                            </div>
                            <div className="absolute inset-0 bg-gradient-to-r from-violet-500/5 to-purple-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        type="no-jobs"
                        showIllustration={false}
                        actions={[
                          {
                            label: "Upload Files",
                            onClick: () => setActiveTab("upload"),
                            icon: Upload,
                          },
                        ]}
                        className="border-0 bg-transparent"
                      />
                    )}
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card className="bg-white/70 backdrop-blur-sm border border-white/20 hover:bg-white/90 transition-all duration-300 hover:shadow-xl">
                  <CardHeader className="relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-indigo-50/30 to-blue-50/20 rounded-full -mr-12 -mt-12"></div>
                    <CardTitle className="flex items-center relative z-10 text-slate-800 font-bold tracking-wide">
                      <div className="bg-gradient-to-r from-indigo-500 to-blue-500 p-2 rounded-lg mr-3 shadow-lg">
                        <TrendingUp className="w-5 h-5 text-white" />
                      </div>
                      Quick Actions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Mobile: 2x2 Grid, Tablet/Desktop: 1x4 Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                      <Button
                        onClick={() => setActiveTab("upload")}
                        className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium transition-all duration-300 hover:scale-105 hover:shadow-lg group ripple-effect enhanced-hover px-2 sm:px-4"
                      >
                        <Upload className="w-5 h-5 sm:w-6 sm:h-6 mb-1 sm:mb-0 sm:mr-2 group-hover:scale-110 transition-transform duration-300 sparkle-icon" />
                        <span className="text-xs sm:text-sm text-center">Upload Files</span>
                      </Button>

                      <Button
                        variant="outline"
                        onClick={() => setActiveTab("jobs")}
                        className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:border-emerald-300 transition-all duration-300 hover:scale-105 hover:shadow-md group ripple-effect enhanced-hover px-2 sm:px-4"
                      >
                        <FileText className="w-5 h-5 sm:w-6 sm:h-6 mb-1 sm:mb-0 sm:mr-2 group-hover:scale-110 transition-transform duration-300 sparkle-icon" />
                        <span className="text-xs sm:text-sm text-center">Browse Jobs</span>
                      </Button>

                      <Button
                        variant="outline"
                        onClick={() => setActiveTab("search")}
                        className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300 transition-all duration-300 hover:scale-105 hover:shadow-md group ripple-effect enhanced-hover px-2 sm:px-4"
                      >
                        <Search className="w-5 h-5 sm:w-6 sm:h-6 mb-1 sm:mb-0 sm:mr-2 group-hover:scale-110 transition-transform duration-300 sparkle-icon" />
                        <span className="text-xs sm:text-sm text-center">Search Jobs</span>
                      </Button>

                      <Button
                        variant="outline"
                        onClick={() => setActiveTab("compare")}
                        className="flex flex-col sm:flex-row items-center justify-center h-16 sm:h-20 border-amber-200 text-amber-700 hover:bg-amber-50 hover:border-amber-300 transition-all duration-300 hover:scale-105 hover:shadow-md group ripple-effect enhanced-hover px-2 sm:px-4"
                      >
                        <GitCompare className="w-5 h-5 sm:w-6 sm:h-6 mb-1 sm:mb-0 sm:mr-2 group-hover:scale-110 transition-transform duration-300 sparkle-icon" />
                        <span className="text-xs sm:text-sm text-center">Compare Jobs</span>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Jobs Tab */}
              <TabsContent value="jobs">
                <JobList onJobSelect={handleJobSelect} showFilters={true} />
              </TabsContent>

              {/* Upload Tab */}
              <TabsContent value="upload">
                <BulkUpload
                  onUploadComplete={handleUploadComplete}
                  maxFileSize={50}
                  acceptedFileTypes={[".txt", ".doc", ".docx", ".pdf"]}
                />
              </TabsContent>

              {/* Search Tab */}
              <TabsContent value="search">
                <SearchInterface onJobSelect={handleJobSelect} />
              </TabsContent>

              {/* Compare Tab */}
              <TabsContent value="compare">
                <JobComparison />
              </TabsContent>

              {/* Statistics Tab */}
              <TabsContent value="statistics">
                <StatsDashboard />
              </TabsContent>

              {/* Job Details Tab (Hidden) */}
              <TabsContent value="job-details">
                {selectedJob && (
                  <JobDetails
                    jobId={selectedJob.id}
                    onBack={handleBackFromDetails}
                  />
                )}
              </TabsContent>
            </Tabs>
          </div>
          </div>
        </ToastProvider>
      </ErrorBoundaryWrapper>
    </ThemeProvider>
  );
}
