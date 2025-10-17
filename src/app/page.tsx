/**
 * JDDB Main Application Page
 * Modernized with Two-Panel layout architecture
 * Dashboard sidebar (left) + Main content (center) + Optional panels (right)
 */

"use client";

import React, { useState, useEffect, lazy, Suspense, useRef, useCallback } from "react";
import { ThreeColumnLayout } from "@/components/layout/ThreeColumnLayout";
import { ProfileHeader } from "@/components/layout/ProfileHeader";
import { AppHeader, type AppView } from "@/components/layout/AppHeader";

// Lazy load heavy layout components for better initial page load performance
const AIAssistantPanel = lazy(() => import("@/components/ai/AIAssistantPanel").then(m => ({ default: m.AIAssistantPanel })));
const DashboardSidebar = lazy(() => import("@/components/dashboard/DashboardSidebar").then(m => ({ default: m.DashboardSidebar })));
const JobsTable = lazy(() => import("@/components/jobs/JobsTable").then(m => ({ default: m.JobsTable })));
const JobDetailView = lazy(() => import("@/components/jobs/JobDetailView").then(m => ({ default: m.JobDetailView })));
const CreateJobModal = lazy(() => import("@/components/jobs/CreateJobModal").then(m => ({ default: m.CreateJobModal })));
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
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges";

// Lazy load route-level components for better performance
const BulkUpload = lazy(() => import("@/components/BulkUpload"));
const SearchInterface = lazy(() => import("@/components/SearchInterface"));
// Import SearchInterfaceRef type for ref typing
import type { SearchInterfaceRef } from "@/components/SearchInterface";
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
const BilingualEditorWrapper = lazy(
  () => import("@/components/translation/BilingualEditorWrapper"),
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
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [shouldFocusSearch, setShouldFocusSearch] = useState(false);
  const { stats, selectedJob, fetchJobs, fetchStats, selectJob, error } =
    useStore();

  const { confirmNavigation } = useUnsavedChanges({
    hasUnsavedChanges,
    message: "You have unsaved changes. Are you sure you want to leave?",
  });

  // Ref for SearchInterface to access focus method
  const searchInterfaceRef = useRef<SearchInterfaceRef>(null);

  // Track view changes for transitions
  const handleViewChange = (newView: ViewType) => {
    setPreviousView(activeView);
    setActiveView(newView);
  };

  // Memoized callback for search focus to prevent infinite re-renders
  const handleSearchFocused = useCallback(() => {
    setShouldFocusSearch(false);
  }, []);

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
      // Set flag to focus search input when component mounts
      setShouldFocusSearch(true);
    },
    onNewUpload: () => handleViewChange("upload"),
    onShowShortcuts: openShortcutsModal,
  });

  // Initialize API client and load data with deferred loading for better performance
  useEffect(() => {
    // Note: API key not required for current backend implementation
    // Backend uses environment-based configuration

    // Defer API calls to allow initial render to complete faster
    // This improves perceived performance and initial page load time
    const timer = setTimeout(() => {
      fetchJobs(true);
      fetchStats();
    }, 0); // Use 0ms timeout to defer to next event loop tick

    return () => clearTimeout(timer);
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
  const handleUploadComplete = async () => {
    // Refresh both stats and job list after upload
    await Promise.all([
      fetchStats(),
      fetchJobs(true), // Force refresh to show newly uploaded jobs
    ]);
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
    if (!confirmNavigation()) {
      return;
    }
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
                <h1 className="text-3xl font-bold">Dashboard</h1>
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
          <Suspense fallback={<LoadingState message="Loading jobs..." />}>
            <JobsTable
              onJobSelect={handleJobSelect}
              onNavigateToUpload={() => handleViewChange("upload")}
              onNavigateToSearch={() => handleViewChange("search")}
              onCreateNew={() => {
                setShowCreateJobModal(true);
              }}
            />
          </Suspense>,
          "jobs",
        );
      case "job-details":
        return wrapWithPanelId(
          selectedJob ? (
            <Suspense fallback={<LoadingState message="Loading job details..." />}>
              <JobDetailView
                jobId={selectedJob.id}
                onBack={handleBackFromDetails}
                onEdit={() => handleViewChange("improvement")}
                onTranslate={() => {
                  handleViewChange("translate");
                }}
                onCompare={() => handleViewChange("compare")}
              />
            </Suspense>
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
              acceptedFileTypes={[".txt", ".doc", ".docx", ".pdf", ".md"]}
            />
          </Suspense>,
          "upload",
        );
      case "search":
        return wrapWithPanelId(
          <Suspense fallback={<LoadingState message="Loading search..." />}>
            <SearchInterface
              ref={searchInterfaceRef}
              onJobSelect={handleJobSelect}
              autoFocus={shouldFocusSearch}
              onFocused={handleSearchFocused}
            />
          </Suspense>,
          "search",
        );
      case "editing": {
        const { mergedJob, setMergedJob } = useStore.getState();
        if (mergedJob) {
          setMergedJob(null);
        }
        return wrapWithPanelId(
          <Suspense fallback={<LoadingState message="Loading editor..." />}>
            <BasicEditingView
              jobId={selectedJob?.id}
              initialContent={mergedJob?.title}
              onBack={() =>
                handleViewChange(selectedJob ? "job-details" : "home")
              }
              onAdvancedEdit={() => {
                if (confirmNavigation()) {
                  // Future Enhancement: Add lock warning modal
                  // This modal should warn users that switching to advanced mode
                  // will lock the document for concurrent editing
                  // For now, advanced mode is accessible through the advanced tab
                }
              }}
              onUnsavedChangesChange={setHasUnsavedChanges}
            />
          </Suspense>,
          "improve",
        );
      }
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
              onSave={(_finalText) => {
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
              <BilingualEditorWrapper
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
                <h1 className="text-3xl font-bold">Statistics</h1>
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
                <h1 className="text-3xl font-bold">
                  AI Job Description Writer
                </h1>
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
                <h1 className="text-3xl font-bold">Job Posting Generator</h1>
                <p className="text-muted-foreground mt-2">
                  Transform job descriptions into optimized public postings
                </p>
              </div>
            </div>
            <Suspense
              fallback={<LoadingState message="Loading posting generator..." />}
            >
              <JobPostingGenerator selectedJob={selectedJob} />
            </Suspense>
          </div>,
          "posting",
        );
      case "analytics":
        return wrapWithPanelId(
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">
                  Predictive Content Analytics
                </h1>
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
          <Suspense fallback={<LoadingState message="Loading jobs..." />}>
            <JobsTable
              onJobSelect={handleJobSelect}
              onNavigateToUpload={() => handleViewChange("upload")}
              onNavigateToSearch={() => handleViewChange("search")}
            />
          </Suspense>,
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
                <Suspense fallback={<LoadingState message="Loading sidebar..." />}>
                  <DashboardSidebar
                    stats={stats}
                    onNavigateToStatistics={() => handleViewChange("statistics")}
                    onNavigateToSystemHealth={() =>
                      handleViewChange("system-health")
                    }
                    collapsed={leftPanelCollapsed}
                  />
                </Suspense>
              }
              middlePanel={
                <Suspense fallback={<LoadingState message="Loading AI panel..." />}>
                  <AIAssistantPanel suggestions={[]} overallScore={null} />
                </Suspense>
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
            <Suspense fallback={null}>
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
            </Suspense>
          </ToastProvider>
        </LoadingProvider>
      </ErrorBoundaryWrapper>
    </ThemeProvider>
  );
}
