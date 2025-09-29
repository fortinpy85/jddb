/**
 * JDDB Main Application Page
 * Enhanced with consistent layout system and modern UI patterns
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import { JDDBLayout, PageContainer } from "@/components/layout/JDDBLayout";
import JobList from "@/components/JobList";
import BulkUpload from "@/components/BulkUpload";
import JobDetails from "@/components/JobDetails";
import SearchInterface from "@/components/SearchInterface";
import JobComparison from "@/components/JobComparison";
import StatsDashboard from "@/components/StatsDashboard";
import { EditingWorkspace } from "@/components/editing/EditingWorkspace";
import { EnhancedDualPaneEditor } from "@/components/editing/EnhancedDualPaneEditor";
import { ModernDashboard } from "@/components/layout/ModernDashboard";
import { Dashboard } from "@/components/dashboard/Dashboard";
import type { JobDescription } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { useStore } from "@/lib/store";
import { TAB_ORDER, TAB_NAMES } from "@/lib/constants";
import { Layers } from "lucide-react";
import { ToastProvider } from "@/components/ui/toast";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { LoadingProvider, useLoadingMessage } from "@/contexts/LoadingContext";
import { useJDDBKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import {
  KeyboardShortcutsModal,
  useKeyboardShortcutsModal,
} from "@/components/ui/keyboard-shortcuts-modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState, ErrorState } from "@/components/ui/states";
import {
  PageTransition,
  FadeTransition,
  StaggerAnimation,
} from "@/components/ui/transitions";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("dashboard");
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

  // Keyboard shortcuts modal
  const {
    isOpen: shortcutsModalOpen,
    openModal: openShortcutsModal,
    closeModal: closeShortcutsModal,
  } = useKeyboardShortcutsModal();

  // Search input reference for focus
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcuts handlers
  const { shortcuts } = useJDDBKeyboardShortcuts({
    onNavigateToJobs: () => setActiveTab("jobs"),
    onNavigateToUpload: () => setActiveTab("upload"),
    onNavigateToSearch: () => setActiveTab("search"),
    onNavigateToCompare: () => setActiveTab("compare"),
    onNavigateToStats: () => setActiveTab("statistics"),
    onFocusSearch: () => {
      setActiveTab("search");
      // Focus search input after tab switch
      setTimeout(() => {
        const searchInput = document.querySelector(
          'input[placeholder*="search"], input[type="search"]',
        ) as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      }, 100);
    },
    onNewUpload: () => setActiveTab("upload"),
    onShowShortcuts: openShortcutsModal,
  });

  // Initialize API client with API key
  useEffect(() => {
    apiClient.setApiKey("your_api_key");
  }, []);

  const recentJobs = jobs.slice(0, 5);

  // Tab navigation order from constants
  const currentTabIndex = TAB_ORDER.indexOf(activeTab as any);

  // Keyboard navigation
  useKeyboardNavigation({
    onArrowLeft: () => {
      if (currentTabIndex > 0) {
        setActiveTab(TAB_ORDER[currentTabIndex - 1]);
      }
    },
    onArrowRight: () => {
      if (currentTabIndex < TAB_ORDER.length - 1) {
        setActiveTab(TAB_ORDER[currentTabIndex + 1]);
      }
    },
    onCtrlF: () => {
      setActiveTab("search");
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
    apiClient.setApiKey("your_api_key");
    fetchJobs(true);
    fetchStats();
  }, [fetchJobs, fetchStats]);

  // Handle tab changes
  const handleTabChange = (newTab: string) => {
    setActiveTab(newTab);
  };

  // Auto-focus search input when navigating to search tab
  useEffect(() => {
    if (activeTab === "search") {
      // Use requestAnimationFrame to ensure the SearchInterface component has rendered
      requestAnimationFrame(() => {
        const searchInput = document.querySelector(
          'input[placeholder*="Search"]',
        ) as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      });
    }
  }, [activeTab]);

  // Handle job selection
  const handleJobSelect = (job: JobDescription) => {
    selectJob(job);
    handleTabChange("job-details");
  };

  // Handle back from job details
  const handleBackFromDetails = () => {
    selectJob(null);
    handleTabChange("jobs");
  };

  // Handle upload completion
  const handleUploadComplete = () => {
    // Refresh stats after upload
    fetchStats();
    handleTabChange("jobs"); // Navigate to jobs list
  };

  // Dashboard content is now handled by the Dashboard component

  // Main content renderer based on active tab
  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <Dashboard
            stats={stats}
            recentJobs={recentJobs}
            onJobSelect={handleJobSelect}
            onNavigateToTab={setActiveTab}
          />
        );
      case "jobs":
        return <JobList onJobSelect={handleJobSelect} showFilters={true} />;
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
        return <EditingWorkspace />;
      case "compare":
        return <JobComparison />;
      case "statistics":
        return <StatsDashboard />;
      case "modern":
        return (
          <div className="space-y-8">
            <ModernDashboard />
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                Enhanced UI Components
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                Modern interfaces with JDDB branding
              </p>
            </div>
            <Card className="overflow-hidden">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Layers className="w-5 h-5" />
                  <span>Enhanced Dual-Pane Editor</span>
                  <Badge variant="secondary">Professional</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[600px]">
                  <EnhancedDualPaneEditor
                    mode="translation"
                    initialLeftContent="The Business Development Representative supports sales activities through qualifying leads generated from other teams, and committing to developing those leads into new business."
                    initialRightContent="Le représentant du développement commercial soutient les activités de vente en qualifiant les prospects générés par d'autres équipes et en s'engageant à développer ces prospects en nouvelles affaires."
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        );
      case "job-details":
        return selectedJob ? (
          <JobDetails jobId={selectedJob.id} onBack={handleBackFromDetails} />
        ) : null;
      default:
        return (
          <Dashboard
            stats={stats}
            recentJobs={recentJobs}
            onJobSelect={handleJobSelect}
            onNavigateToTab={setActiveTab}
          />
        );
    }
  };

  return (
    <ThemeProvider defaultTheme="system" enableSystem>
      <ErrorBoundaryWrapper
        showDetails={process.env.NODE_ENV === "development"}
      >
        <LoadingProvider initialContext="dashboard">
          <ToastProvider>
            <JDDBLayout activeTab={activeTab} onTabChange={handleTabChange}>
              <PageTransition currentPage={activeTab} previousPage={undefined}>
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
            </JDDBLayout>

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
