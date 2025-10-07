/**
 * JDDB Unified Layout Component
 * Provides consistent layout structure across all pages with enhanced visual continuity
 */

"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Database,
  BarChart3,
  FileText,
  Upload,
  Search,
  Edit3,
  GitCompare,
  Activity,
  Palette,
  Settings,
  HelpCircle,
  Menu,
  X,
  ChevronLeft,
  Home,
} from "lucide-react";
import ThemeToggle from "@/components/ui/theme-toggle";
import { useStore } from "@/lib/store";
import { useLoadingContext } from "@/contexts/LoadingContext";

interface NavigationTab {
  id: string;
  label: string;
  shortLabel?: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  disabled?: boolean;
}

const NAVIGATION_TABS: NavigationTab[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: BarChart3,
    description: "Overview and quick actions",
  },
  {
    id: "jobs",
    label: "Jobs",
    icon: FileText,
    description: "Browse job descriptions",
  },
  {
    id: "upload",
    label: "Upload",
    icon: Upload,
    description: "Upload new files",
  },
  {
    id: "search",
    label: "Search",
    icon: Search,
    description: "Search and filter jobs",
  },
  {
    id: "editing",
    label: "Editing",
    shortLabel: "Edit",
    icon: Edit3,
    description: "Edit job descriptions",
  },
  {
    id: "compare",
    label: "Compare",
    icon: GitCompare,
    description: "Compare job descriptions",
  },
  {
    id: "statistics",
    label: "Statistics",
    shortLabel: "Stats",
    icon: Activity,
    description: "Analytics and reports",
  },
  {
    id: "modern",
    label: "Modern UI",
    shortLabel: "Modern",
    icon: Palette,
    description: "Enhanced components",
  },
];

interface JDDBLayoutProps {
  children: React.ReactNode;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  title?: string;
  subtitle?: string;
  showBackButton?: boolean;
  onBack?: () => void;
  className?: string;
  contentClassName?: string;
}

export function JDDBLayout({
  children,
  activeTab = "dashboard",
  onTabChange,
  title,
  subtitle,
  showBackButton = false,
  onBack,
  className,
  contentClassName,
}: JDDBLayoutProps) {
  // Get stats and loading from store directly instead of props
  const { stats, loading } = useStore();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div
      data-testid="jddb-layout"
      className={cn(
        "min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-900 dark:via-slate-800/30 dark:to-slate-900/20 transition-colors duration-300",
        className,
      )}
    >
      {/* Fixed Header */}
      <JDDBHeader
        title={title}
        subtitle={subtitle}
        showBackButton={showBackButton}
        onBack={onBack}
      />

      {/* Navigation Tabs */}
      <JDDBNavigation
        tabs={NAVIGATION_TABS}
        activeTab={activeTab}
        onTabChange={onTabChange}
      />

      {/* Main Content Area */}
      <main className="pt-28">
        <div className="flex">
          {/* Left Sidebar (minimal) */}
          <aside
            data-testid="sidebar"
            className={cn(
              "transition-all duration-300 flex-shrink-0 bg-slate-50/50 dark:bg-slate-900/50 border-r border-slate-200/50 dark:border-slate-700/50",
              sidebarCollapsed ? "w-12" : "w-16 sm:w-20 lg:w-24",
            )}
          >
            <div className="p-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="w-full p-2"
                data-testid="sidebar-toggle"
              >
                {sidebarCollapsed ? (
                  <Menu className="w-4 h-4" />
                ) : (
                  <X className="w-4 h-4" />
                )}
              </Button>
            </div>
          </aside>

          {/* Content Container */}
          <div className="flex-1 px-4 sm:px-6 lg:px-8 py-8">
            {loading ? (
              <LoadingScreen />
            ) : (
              <div className={cn("max-w-7xl mx-auto", contentClassName)}>
                {children}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

/**
 * JDDB Header Component
 */
interface JDDBHeaderProps {
  title?: string;
  subtitle?: string;
  showBackButton?: boolean;
  onBack?: () => void;
}

function JDDBHeader({
  title,
  subtitle,
  showBackButton,
  onBack,
}: JDDBHeaderProps) {
  // Get stats from store directly instead of props
  const { stats } = useStore();
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-lg border-b border-white/20 dark:border-slate-700/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full">
        <div className="flex items-center justify-between h-full">
          {/* Left Side - Logo and Navigation */}
          <div className="flex items-center space-x-4">
            {showBackButton && onBack && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                <span className="hidden sm:inline">Back</span>
              </Button>
            )}

            {/* JDDB Logo and Title */}
            <div className="flex items-center group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg blur opacity-20 group-hover:opacity-30 transition-opacity duration-300"></div>
                <Database className="relative w-6 h-6 sm:w-8 sm:h-8 text-blue-600 mr-2 sm:mr-3 group-hover:scale-110 transition-transform duration-300" />
              </div>
              <div className="min-w-0">
                <h2 className="text-sm sm:text-lg lg:text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 transition-all duration-300 truncate">
                  {title || (
                    <>
                      <span className="hidden sm:inline">
                        Job Description Database
                      </span>
                      <span className="sm:hidden">JDDB</span>
                    </>
                  )}
                </h2>
                {subtitle && (
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 font-medium truncate">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Right Side - Stats and Controls */}
          <div className="flex items-center space-x-2 sm:space-x-4 min-w-0">
            {/* Theme Toggle */}
            <ThemeToggle size="sm" className="flex-shrink-0" />

            {/* Stats Display */}
            {stats && (
              <div className="text-xs sm:text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100/50 dark:bg-slate-800/50 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 truncate">
                <span className="font-semibold text-blue-600 dark:text-blue-400">
                  {stats.total_jobs}
                </span>
                <span className="hidden xs:inline"> jobs</span>
                <span className="hidden sm:inline"> • Updated:</span>
                <span className="hidden md:inline text-slate-500 dark:text-slate-400">
                  {" "}
                  {stats.last_updated
                    ? new Date(stats.last_updated).toLocaleDateString()
                    : "Never"}
                </span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center space-x-1">
              <Button variant="ghost" size="sm" className="p-2" title="Help">
                <HelpCircle className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="p-2"
                title="Settings"
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

/**
 * JDDB Navigation Component
 */
interface JDDBNavigationProps {
  tabs: NavigationTab[];
  activeTab: string;
  onTabChange?: (tab: string) => void;
}

function JDDBNavigation({ tabs, activeTab, onTabChange }: JDDBNavigationProps) {
  return (
    <nav className="fixed top-16 left-0 right-0 z-40 h-12 bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-900 dark:via-slate-800/30 dark:to-slate-900/20 border-b border-slate-200/50 dark:border-slate-700/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full">
        <div className="flex items-center h-full overflow-x-auto scrollbar-hide">
          <div className="flex items-center space-x-1 min-w-max">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange?.(tab.id)}
                disabled={tab.disabled}
                data-testid={
                  activeTab === tab.id ? "active-tab" : `tab-${tab.id}`
                }
                className={cn(
                  "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed",
                  activeTab === tab.id
                    ? "bg-white/80 dark:bg-slate-800/80 text-blue-600 dark:text-blue-400 shadow-md border border-blue-200/50 dark:border-blue-400/50"
                    : "text-slate-600 dark:text-slate-400 hover:bg-white/50 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-slate-200",
                )}
                title={tab.description}
              >
                <tab.icon className="w-4 h-4 flex-shrink-0" />
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.shortLabel || tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}

/**
 * Loading Screen Component with Context-Aware Messages
 */
function LoadingScreen() {
  const { getMessage } = useLoadingContext();
  const message = getMessage();

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center space-y-4">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <Database className="absolute inset-0 m-auto w-6 h-6 text-blue-600" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {message.title}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {message.description}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Page Container Component
 * Standardized container for consistent spacing and layout
 */
export interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  headerActions?: React.ReactNode;
  loading?: boolean;
}

export function PageContainer({
  children,
  className,
  title,
  subtitle,
  headerActions,
  loading,
}: PageContainerProps) {
  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className={cn("space-y-6", className)}>
      {(title || subtitle || headerActions) && (
        <div className="flex items-center justify-between">
          <div>
            {title && (
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="text-slate-600 dark:text-slate-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
          {headerActions && (
            <div className="flex items-center space-x-2">{headerActions}</div>
          )}
        </div>
      )}
      <div className="space-y-6">{children}</div>
    </div>
  );
}

/**
 * Content Section Component
 * Standardized content sections with consistent JDDB styling
 */
interface ContentSectionProps {
  title?: string;
  subtitle?: string;
  icon?: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  className?: string;
  headerActions?: React.ReactNode;
  variant?: "default" | "highlighted" | "compact";
  loading?: boolean;
}

export function ContentSection({
  title,
  subtitle,
  icon: Icon,
  children,
  className,
  headerActions,
  variant = "default",
  loading = false,
}: ContentSectionProps) {
  const isCompact = variant === "compact";
  const isHighlighted = variant === "highlighted";

  if (loading) {
    return (
      <div
        className={cn(
          "bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-white/20 dark:border-slate-700/20 rounded-xl p-6",
          className,
        )}
      >
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-white/20 dark:border-slate-700/20 hover:bg-white/90 dark:hover:bg-slate-800/90 transition-all duration-300 rounded-xl",
        isHighlighted &&
          "hover:shadow-xl border-blue-200/50 dark:border-blue-400/50",
        className,
      )}
    >
      {(title || subtitle || headerActions) && (
        <div
          className={cn("p-6 relative overflow-hidden", isCompact && "pb-3")}
        >
          {isHighlighted && (
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-50/30 to-indigo-50/20 rounded-full -mr-12 -mt-12"></div>
          )}
          <div className="flex items-center justify-between relative z-10">
            <div className="flex items-center space-x-3">
              {Icon && (
                <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-2 rounded-lg shadow-lg">
                  <Icon className="w-5 h-5 text-white" />
                </div>
              )}
              <div>
                {title && (
                  <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 tracking-wide">
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
            {headerActions && (
              <div className="flex items-center space-x-2">{headerActions}</div>
            )}
          </div>
        </div>
      )}
      <div
        className={cn(
          "p-6",
          isCompact && "pt-3",
          (title || subtitle || headerActions) && "pt-0",
        )}
      >
        {children}
      </div>
    </div>
  );
}
