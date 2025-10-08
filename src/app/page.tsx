/**
 * JDDB Main Application Page
 * Modernized with Two-Panel layout architecture
 * Dashboard sidebar (left) + Main content (center) + Optional panels (right)
 */

"use client";

import React, { useState, useEffect, lazy, Suspense } from "react";
import { ThreeColumnLayout } from "@/components/layout/ThreeColumnLayout";
import { ProfileHeader } from "@/components/layout/ProfileHeader";
import { AIAssistantPanel } from "@/components/ai/AIAssistantPanel";
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { AppHeader, type AppView } from "@/components/layout/AppHeader";
import { JobsTable } from "@/components/jobs/JobsTable";
import { JobDetailView } from "@/components/jobs/JobDetailView";
import { CreateJobModal } from "@/components/jobs/CreateJobModal";
import type { JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { useStore } from "@/lib/store";
import { ToastProvider } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { LoadingProvider } from "@/contexts/LoadingContext";
import { useJDDBKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import {
  KeyboardShortcutsModal,
  useKeyboardShortcutsModal,
} from "@/components/ui/keyboard-shortcuts-modal";
import { LoadingState, ErrorState } from "@/components/ui/states";
import { PageTransition } from "@/components/ui/transitions";
import { AlertBanner } from "@/components/ui/alert-banner";
import { LanguageSync } from "@/components/wet/LanguageSync";
import { SkipLinks } from "@/components/wet/SkipLinks";

// Lazy load route-level components for better performance
const BulkUpload = lazy(() => import("@/components/BulkUpload"));
const SearchInterface = lazy(() => import("@/components/SearchInterface"));
const JobComparison = lazy(() => import("@/components/JobComparison"));
const StatsDashboard = lazy(() => import("@/components/StatsDashboard"));
const BasicEditingView = lazy(() =>
  import("@/components/editing/BasicEditingView").then((m) => ({
    default: m.BasicEditingView,
  })),
);
const ImprovementView = lazy(() =>
  import("@/components/improvement/ImprovementView").then((m) => ({
    default: m.ImprovementView,
  })),
);
const SystemHealthPage = lazy(() =>
  import("@/components/system/SystemHealthPage").then((m) => ({
    default: m.SystemHealthPage,
  })),
);
const UserPreferencesPage = lazy(() =>
  import("@/components/preferences/UserPreferencesPage").then((m) => ({
    default: m.UserPreferencesPage,
  })),
);
const BilingualEditor = lazy(() =>
  import("@/components/translation/BilingualEditor").then((m) => ({
    default: m.BilingualEditor,
  })),
);
const AIDemo = lazy(() => import("@/app/ai-demo/page"));
const AIJobWriter = lazy(() =>
  import("@/components/generation/AIJobWriter").then((m) => ({
    default: m.AIJobWriter,
  })),
);
const JobPostingGenerator = lazy(() =>
  import("@/components/generation/JobPostingGenerator").then((m) => ({
    default: m.JobPostingGenerator,
  })),
);
const PredictiveAnalytics = lazy(() =>
  import("@/components/analytics/PredictiveAnalytics").then((m) => ({
    default: m.PredictiveAnalytics,
  })),
);

// View types for routing
type ViewType =
  | "dashboard"
  | "home"
  | "job-details"
  | "upload"
  | "search"
  | "editing"
  | "improvement"
  | "writer"
  | "posting"
  | "analytics"
  | "translate"
  | "compare"
  | "statistics"
  | "system-health"
  | "preferences"
  | "ai-demo";

export default function HomePage() {
  const [activeView, setActiveView] = useState<ViewType>("dashboard");
  const [previousView, setPreviousView] = useState<ViewType | undefined>(
    undefined,
  );
  const [showAlertBanner, setShowAlertBanner] = useState(true);
  const [showCreateJobModal, setShowCreateJobModal] = useState(false);
  const { stats, selectedJob, fetchJobs, fetchStats, selectJob, error } =
    useStore();

  // Track view changes for transitions
  const handleViewChange = (newView: ViewType) => {
    setPreviousView(activeView);
    setActiveView(newView);
  };

  // Keyboard shortcuts modal
  const {
    isOpen: shortcutsModalOpen,
    openModal: openShortcutsModal,
    closeModal: closeShortcutsModal,
  } = useKeyboardShortcutsModal();

  // Keyboard shortcuts handlers
  const { shortcuts } = useJDDBKeyboardShortcuts({
    onNavigateToJobs: () => handleViewChange("home"),
    onNavigateToUpload: () => handleViewChange("upload"),
    onNavigateToSearch: () => handleViewChange("search"),
    onNavigateToCompare: () => handleViewChange("compare"),
    onNavigateToStats: () => handleViewChange("dashboard"),
    onFocusSearch: () => {
      handleViewChange("search");
    },
    onNewUpload: () => handleViewChange("upload"),
    onShowShortcuts: openShortcutsModal,
  });

  // Initialize API client and load data
  useEffect(() => {
    apiClient.setApiKey("your_api_key");
    fetchJobs(true);
    fetchStats();
  }, [fetchJobs, fetchStats]);

  // Handle job selection
  const handleJobSelect = (job: JobDescription) => {
    selectJob(job);
    handleViewChange("job-details");
  };

  // Handle back from job details
  const handleBackFromDetails = () => {
    selectJob(null);
    handleViewChange("home");
  };

  // Handle upload completion
  const handleUploadComplete = () => {
    fetchStats();
    handleViewChange("home");
  };

  // Map internal ViewType to AppHeader's AppView type
  const getHeaderView = (): AppView => {
    switch (activeView) {
      case "dashboard":
        return "dashboard";
      case "home":
        return "jobs";
      case "job-details":
        return "jobs";
      case "improvement":
        return "improve";
      case "editing":
        return "translate";
      case "writer":
        return "writer";
      case "posting":
        return "posting";
      case "analytics":
        return "analytics";
      default:
        return activeView as AppView;
    }
  };

  // Handle navigation from AppHeader
  const handleHeaderNavigation = (view: AppView) => {
    switch (view) {
      case "dashboard":
        selectJob(null); // Clear selection when navigating away from job details
        handleViewChange("dashboard");
        break;
      case "jobs":
        selectJob(null); // Clear selection when navigating to jobs list
        handleViewChange("home");
        break;
      case "upload":
        selectJob(null); // Clear selection when navigating to upload
        handleViewChange("upload");
        break;
      case "search":
        selectJob(null); // Clear selection when navigating to search
        handleViewChange("search");
        break;
      case "compare":
        handleViewChange("compare");
        break;
      case "improve":
        if (selectedJob) {
          handleViewChange("improvement");
        } else {
          // If no job selected, go to jobs list and show message
          handleViewChange("home");
        }
        break;
      case "writer":
        selectJob(null); // Clear selection when navigating to AI writer
        handleViewChange("writer");
        break;
      case "posting":
        selectJob(null); // Clear selection when navigating to posting generator
        handleViewChange("posting");
        break;
      case "analytics":
        selectJob(null); // Clear selection when navigating to analytics
        handleViewChange("analytics");
        break;
      case "translate":
        if (selectedJob) {
          handleViewChange("translate");
        } else {
          handleViewChange("home");
        }
        break;
      case "ai-demo":
        selectJob(null); // Clear selection when navigating to AI demo
        handleViewChange("ai-demo");
        break;
      case "statistics":
        selectJob(null); // Clear selection when navigating to statistics
        handleViewChange("statistics");
        break;
      default:
        handleViewChange(view as ViewType);
    }
  };

  // Determine if dashboard sidebar should be shown - ONLY on dashboard view
  // This is critical for usability: dashboard stats should not clutter other views
  const showDashboardSidebar = activeView === "dashboard";

  // Determine if we should show left panel collapsed
  const leftPanelCollapsed = !showDashboardSidebar;

  // Helper to wrap content with proper panel ID for ARIA controls
  const wrapWithPanelId = (content: React.ReactNode, viewId: string) => {
    return (
      <div
        id={`${viewId}-panel`}
        role="tabpanel"
        aria-labelledby={`${viewId}-tab`}
      >
        {content}
      </div>
    );
  };

  // Main content renderer based on active view
  const renderContent = () => {
    switch (activeView) {
      case "dashboard":
        return wrapWithPanelId(
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold">Dashboard</h2>
                <p className="text-muted-foreground mt-2">
                  Overview of your job description database
                </p>
              </div>
            </div>
            <Suspense
              fallback={<LoadingState message="Loading dashboard..." />}
            >
              <StatsDashboard />
            </Suspense>
          </div>,
          "dashboard",
        );
      case "home":
        return wrapWithPanelId(
          <JobsTable
            onJobSelect={handleJobSelect}
            onNavigateToUpload={() => handleViewChange("upload")}
            onNavigateToSearch={() => handleViewChange("search")}
            onCreateNew={() => {
              setShowCreateJobModal(true);
            }}
          />,
          "jobs",
        );
      case "job-details":
        return wrapWithPanelId(
          selectedJob ? (
            <JobDetailView
              jobId={selectedJob.id}
              onBack={handleBackFromDetails}
              onEdit={() => handleViewChange("improvement")}
              onTranslate={() => {
                handleViewChange("translate");
              }}
              onCompare={() => handleViewChange("compare")}
            />
          ) : (
            <ErrorState
              title="No job selected"
              message="Please select a job from the list"
              onAction={handleBackFromDetails}
              actionLabel="Back to Jobs"
            />
          ),
          "jobs",
        );
      case "upload":
        return wrapWithPanelId(
          <Suspense
            fallback={<LoadingState message="Loading upload interface..." />}
          >
            <BulkUpload
              onUploadComplete={handleUploadComplete}
              maxFileSize={50}
              acceptedFileTypes={[".txt", ".doc", ".docx", ".pdf"]}
            />
          </Suspense>,
          "upload",
        );
      case "search":
        return wrapWithPanelId(
          <Suspense fallback={<LoadingState message="Loading search..." />}>
            <SearchInterface onJobSelect={handleJobSelect} />
          </Suspense>,
          "search",
        );
      case "editing":
        return wrapWithPanelId(
          <Suspense fallback={<LoadingState message="Loading editor..." />}>
            <BasicEditingView
              jobId={selectedJob?.id}
              onBack={() =>
                handleViewChange(selectedJob ? "job-details" : "home")
              }
              onAdvancedEdit={() => {
                // TODO: Add lock warning modal
              }}
            />
          </Suspense>,
          "improve",
        );
      case "improvement":
        return wrapWithPanelId(
          <Suspense
            fallback={<LoadingState message="Loading improvement tools..." />}
          >
            <ImprovementView
              jobId={selectedJob?.id}
              initialOriginalText={
                selectedJob?.sections?.find(
                  (s) => s.section_type === "general_accountability",
                )?.section_content || ""
              }
              onBack={() =>
                handleViewChange(selectedJob ? "job-details" : "home")
              }
              onSave={(finalText) => {
                handleViewChange(selectedJob ? "job-details" : "home");
              }}
            />
          </Suspense>,
          "improve",
        );
      case "translate":
        return wrapWithPanelId(
          selectedJob ? (
            <Suspense
              fallback={<LoadingState message="Loading translator..." />}
            >
              <BilingualEditor
                jobId={selectedJob.id}
                sourceLanguage={selectedJob.language === "fr" ? "fr" : "en"}
                targetLanguage={selectedJob.language === "fr" ? "en" : "fr"}
                onBack={() => handleViewChange("job-details")}
              />
            </Suspense>
          ) : (
            <ErrorState
              title="No Job Selected"
              message="Please select a job description to translate"
              onAction={() => handleViewChange("home")}
            />
          ),
          "translate",
        );
      case "compare":
        return wrapWithPanelId(
          <Suspense fallback={<LoadingState message="Loading comparison..." />}>
            <JobComparison />
          </Suspense>,
          "compare",
        );
      case "statistics":
        return wrapWithPanelId(
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold">Statistics</h2>
                <p className="text-muted-foreground mt-2">
                  In-depth analysis of your job description data
                </p>
              </div>
            </div>
            <Suspense
              fallback={<LoadingState message="Loading statistics..." />}
            >
              <StatsDashboard />
            </Suspense>
          </div>,
          "statistics",
        );
      case "system-health":
        return wrapWithPanelId(
          <Suspense
            fallback={<LoadingState message="Loading system health..." />}
          >
            <SystemHealthPage />
          </Suspense>,
          "system-health",
        );
      case "preferences":
        return wrapWithPanelId(
          <Suspense
            fallback={<LoadingState message="Loading preferences..." />}
          >
            <UserPreferencesPage />
          </Suspense>,
          "preferences",
        );
      case "writer":
        return wrapWithPanelId(
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold">
                  AI Job Description Writer
                </h2>
                <p className="text-muted-foreground mt-2">
                  Create comprehensive job descriptions with AI assistance
                </p>
              </div>
            </div>
            <Suspense
              fallback={<LoadingState message="Loading AI writer..." />}
            >
              <AIJobWriter />
            </Suspense>
          </div>,
          "writer",
        );
      case "posting":
        return wrapWithPanelId(
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold">Job Posting Generator</h2>
                <p className="text-muted-foreground mt-2">
                  Transform job descriptions into optimized public postings
                </p>
              </div>
            </div>
            <Suspense
              fallback={<LoadingState message="Loading posting generator..." />}
            >
              <JobPostingGenerator />
            </Suspense>
          </div>,
          "posting",
        );
      case "analytics":
        return wrapWithPanelId(
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold">
                  Predictive Content Analytics
                </h2>
                <p className="text-muted-foreground mt-2">
                  AI-powered predictions for application volume, time-to-fill,
                  and content effectiveness
                </p>
              </div>
            </div>
            <Suspense
              fallback={<LoadingState message="Loading analytics..." />}
            >
              <PredictiveAnalytics />
            </Suspense>
          </div>,
          "analytics",
        );
      case "ai-demo":
        return wrapWithPanelId(
          <Suspense fallback={<LoadingState message="Loading AI demo..." />}>
            <AIDemo />
          </Suspense>,
          "ai-demo",
        );
      default:
        return wrapWithPanelId(
          <JobsTable
            onJobSelect={handleJobSelect}
            onNavigateToUpload={() => handleViewChange("upload")}
            onNavigateToSearch={() => handleViewChange("search")}
          />,
          "jobs",
        );
    }
  };

  // Render modern AppHeader
  const renderHeader = () => (
    <AppHeader
      currentView={getHeaderView()}
      onNavigate={handleHeaderNavigation}
      userName="Admin User"
      notificationCount={0}
      hasSelectedJob={!!selectedJob}
    />
  );

  return (
    <ThemeProvider defaultTheme="system" enableSystem>
      <SkipLinks />
      <LanguageSync />
      <ErrorBoundaryWrapper
        showDetails={process.env.NODE_ENV === "development"}
      >
        <LoadingProvider initialContext="generic">
          {" "}
          <ToastProvider>
            <ThreeColumnLayout
              header={renderHeader()}
              profileHeader={
                <ProfileHeader
                  breadcrumbs={[
                    {
                      label: "Home",
                      onClick: () => handleViewChange("home"),
                    },
                    {
                      label:
                        activeView === "dashboard"
                          ? "Dashboard"
                          : activeView === "statistics"
                            ? "Statistics"
                            : activeView === "system-health"
                              ? "System Health"
                              : activeView === "preferences"
                                ? "Preferences"
                                : activeView.charAt(0).toUpperCase() +
                                  activeView.slice(1),
                    },
                  ]}
                  openTabs={[
                    { id: "tab1", title: "Job 1", active: true },
                    { id: "tab2", title: "Job 2", active: false },
                  ]}
                />
              }
              alertBanner={
                showAlertBanner ? (
                  <AlertBanner
                    variant="info"
                    title="Phase 5: Skills Intelligence Now Available"
                    message="Automated skills extraction powered by Lightcast API is now live! Upload job descriptions to see extracted skills, explore the Skills Analytics dashboard, and filter jobs by required skills."
                    dismissible={true}
                    onDismiss={() => setShowAlertBanner(false)}
                    relative={true}
                  />
                ) : null
              }
              leftPanel={
                <DashboardSidebar
                  stats={stats}
                  onNavigateToStatistics={() => handleViewChange("statistics")}
                  onNavigateToSystemHealth={() =>
                    handleViewChange("system-health")
                  }
                  collapsed={leftPanelCollapsed}
                />
              }
              middlePanel={
                <AIAssistantPanel suggestions={[]} overallScore={null} />
              }
            >
              <PageTransition
                currentPage={activeView}
                previousPage={previousView}
              >
                {error ? (
                  <ErrorState
                    title="Failed to load JDDB"
                    message={error}
                    onAction={() => {
                      fetchJobs(true);
                      fetchStats();
                    }}
                  />
                ) : (
                  renderContent()
                )}
              </PageTransition>
            </ThreeColumnLayout>

            {/* Keyboard Shortcuts Modal */}
            <KeyboardShortcutsModal
              isOpen={shortcutsModalOpen}
              onClose={closeShortcutsModal}
              shortcuts={shortcuts}
            />

            {/* Create Job Modal */}
            <CreateJobModal
              isOpen={showCreateJobModal}
              onClose={() => setShowCreateJobModal(false)}
              onJobCreated={(jobId) => {
                setShowCreateJobModal(false);
                fetchJobs(true);
                fetchStats();
                // Optionally navigate to the new job
                apiClient.getJob(jobId).then((job) => {
                  selectJob(job);
                  handleViewChange("job-details");
                });
              }}
            />
          </ToastProvider>
        </LoadingProvider>
      </ErrorBoundaryWrapper>
    </ThemeProvider>
  );
}
