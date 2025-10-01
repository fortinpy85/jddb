/**
 * JDDB Main Application Page
 * Modernized with Two-Panel layout architecture
 * Dashboard sidebar (left) + Main content (center) + Optional panels (right)
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import { TwoPanelLayout } from "@/components/layout/TwoPanelLayout";
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { AppHeader, type AppView } from "@/components/layout/AppHeader";
import { JobsTable } from "@/components/jobs/JobsTable";
import { JobDetailView } from "@/components/jobs/JobDetailView";
import BulkUpload from "@/components/BulkUpload";
import SearchInterface from "@/components/SearchInterface";
import JobComparison from "@/components/JobComparison";
import StatsDashboard from "@/components/StatsDashboard";
import { BasicEditingView } from "@/components/editing/BasicEditingView";
import { EnhancedDualPaneEditor } from "@/components/editing/EnhancedDualPaneEditor";
import type { JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { useStore } from "@/lib/store";
import { Database, Settings, HelpCircle } from "lucide-react";
import { ToastProvider } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { LoadingProvider } from "@/contexts/LoadingContext";
import { useJDDBKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import {
  KeyboardShortcutsModal,
  useKeyboardShortcutsModal,
} from "@/components/ui/keyboard-shortcuts-modal";
import { Button } from "@/components/ui/button";
import ThemeToggle from "@/components/ui/theme-toggle";
import { LoadingState, ErrorState } from "@/components/ui/states";
import {
  PageTransition,
} from "@/components/ui/transitions";
import { AlertBanner } from "@/components/ui/alert-banner";

// View types for routing
type ViewType = "home" | "job-details" | "upload" | "search" | "editing" | "compare" | "statistics" | "system-health" | "preferences";

export default function HomePage() {
  const [activeView, setActiveView] = useState<ViewType>("home");
  const [previousView, setPreviousView] = useState<ViewType | undefined>(undefined);
  const [showAlertBanner, setShowAlertBanner] = useState(true);
  const {
    stats,
    jobs,
    selectedJob,
    fetchJobs,
    fetchStats,
    selectJob,
    loading,
    error,
  } = useStore();

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
    onNavigateToStats: () => handleViewChange("statistics"),
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
      case "home":
        return "dashboard";
      case "job-details":
        return "jobs";
      case "editing":
        return "translate";
      default:
        return activeView as AppView;
    }
  };

  // Handle navigation from AppHeader
  const handleHeaderNavigation = (view: AppView) => {
    switch (view) {
      case "dashboard":
      case "jobs":
        handleViewChange("home");
        break;
      case "translate":
        if (selectedJob) {
          handleViewChange("editing");
        } else {
          handleViewChange("home");
        }
        break;
      default:
        handleViewChange(view as ViewType);
    }
  };

  // Determine if dashboard sidebar should be shown
  const showDashboardSidebar = ["home", "job-details"].includes(activeView);

  // Determine if we should show left panel collapsed
  const leftPanelCollapsed = !showDashboardSidebar;

  // Main content renderer based on active view
  const renderContent = () => {
    switch (activeView) {
      case "home":
        return (
          <JobsTable
            onJobSelect={handleJobSelect}
            onNavigateToUpload={() => handleViewChange("upload")}
            onNavigateToSearch={() => handleViewChange("search")}
            onCreateNew={() => {
              // TODO: Implement create new job workflow
              console.log("Create new job");
            }}
          />
        );
      case "job-details":
        return selectedJob ? (
          <JobDetailView
            jobId={selectedJob.id}
            onBack={handleBackFromDetails}
            onEdit={() => handleViewChange("editing")}
            onTranslate={() => {
              // TODO: Implement translation workflow
              console.log("Translate job", selectedJob.id);
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
        );
      case "upload":
        return (
          <BulkUpload
            onUploadComplete={handleUploadComplete}
            maxFileSize={50}
            acceptedFileTypes={[".txt", ".doc", ".docx", ".pdf"]}
          />
        );
      case "search":
        return <SearchInterface onJobSelect={handleJobSelect} />;
      case "editing":
        return (
          <BasicEditingView
            jobId={selectedJob?.id}
            onBack={() => handleViewChange(selectedJob ? "job-details" : "home")}
            onAdvancedEdit={() => {
              // TODO: Add lock warning modal
              console.log("Opening advanced editor");
            }}
          />
        );
      case "compare":
        return <JobComparison />;
      case "statistics":
        return <StatsDashboard />;
      case "system-health":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-bold">System Health</h1>
            <p>System health monitoring page coming soon...</p>
          </div>
        );
      case "preferences":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-bold">Preferences</h1>
            <p>User preferences page coming soon...</p>
          </div>
        );
      default:
        return (
          <JobsTable
            onJobSelect={handleJobSelect}
            onNavigateToUpload={() => handleViewChange("upload")}
            onNavigateToSearch={() => handleViewChange("search")}
          />
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
      jobCount={stats?.total_jobs}
    />
  );

  return (
    <ThemeProvider defaultTheme="system" enableSystem>
      <ErrorBoundaryWrapper
        showDetails={process.env.NODE_ENV === "development"}
      >
        <LoadingProvider initialContext="jddb">
          <ToastProvider>
            {/* Alert Banner - Dismissible system notifications */}
            {showAlertBanner && (
              <AlertBanner
                variant="info"
                title="Phase 2.1 UI Modernization Complete"
                message="The JDDB interface has been updated with a streamlined design, improved navigation, and enhanced accessibility features. Explore the new Statistics and Search capabilities!"
                dismissible={true}
                onDismiss={() => setShowAlertBanner(false)}
              />
            )}

            <TwoPanelLayout
              header={renderHeader()}
              leftPanel={
                <DashboardSidebar
                  stats={stats}
                  onNavigateToStatistics={() => handleViewChange("statistics")}
                  onNavigateToSystemHealth={() => handleViewChange("system-health")}
                  collapsed={leftPanelCollapsed}
                />
              }
              showLeftPanel={showDashboardSidebar}
              leftPanelCollapsible={false}
              hideLeftPanelOnMobile={false}
              leftPanelWidth={300}
              className="pt-16"
            >
              <PageTransition currentPage={activeView} previousPage={previousView}>
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
            </TwoPanelLayout>

            {/* Keyboard Shortcuts Modal */}
            <KeyboardShortcutsModal
              isOpen={shortcutsModalOpen}
              onClose={closeShortcutsModal}
              shortcuts={shortcuts}
            />
          </ToastProvider>
        </LoadingProvider>
      </ErrorBoundaryWrapper>
    </ThemeProvider>
  );
}
