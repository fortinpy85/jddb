/**
 * JDDB Application Header
 * Modern top navigation banner with logo, primary navigation, and user controls
 * Implements glassmorphism with elevated shadow system
 */

"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Database,
  BarChart3,
  Upload,
  Search,
  GitCompare,
  Languages,
  Settings,
  HelpCircle,
  User,
  LogOut,
  Bell,
  Command,
  Sparkles,
  Wand2,
  Menu,
  X,
  FileText,
  Megaphone,
} from "lucide-react";
import ThemeToggle from "@/components/ui/theme-toggle";
import { LanguageToggle } from "@/components/wet/LanguageToggle";
import { useTranslation } from "react-i18next";

export type AppView =
  | "home"
  | "dashboard"
  | "jobs"
  | "upload"
  | "improve"
  | "writer"
  | "posting"
  | "analytics"
  | "search"
  | "compare"
  | "translate"
  | "statistics"
  | "system-health"
  | "preferences"
  | "ai-demo";

interface AppHeaderProps {
  currentView?: AppView;
  onNavigate?: (view: AppView) => void;
  userName?: string;
  notificationCount?: number;
  jobCount?: number;
  hasSelectedJob?: boolean;
  className?: string;
}

interface NavItem {
  id: AppView;
  labelKey: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  descriptionKey?: string;
}

const primaryNavItems: NavItem[] = [
  {
    id: "dashboard",
    labelKey: "navigation.main.dashboard",
    icon: BarChart3,
    descriptionKey: "navigation.tooltips.dashboardDesc",
  },
  {
    id: "jobs",
    labelKey: "navigation.main.jobs",
    icon: Database,
    descriptionKey: "navigation.tooltips.jobsDesc",
  },
  {
    id: "upload",
    labelKey: "navigation.main.upload",
    icon: Upload,
    descriptionKey: "navigation.tooltips.uploadDesc",
  },
  {
    id: "improve",
    labelKey: "navigation.main.improve",
    icon: Wand2,
    descriptionKey: "navigation.tooltips.improveDesc",
  },
  {
    id: "writer",
    labelKey: "AI Writer",
    icon: FileText,
    descriptionKey: "Generate job descriptions with AI",
  },
  {
    id: "posting",
    labelKey: "Job Posting",
    icon: Megaphone,
    descriptionKey: "Create public postings",
  },
  {
    id: "analytics",
    labelKey: "Predictive Analytics",
    icon: BarChart3,
    descriptionKey: "Content predictions & insights",
  },
  {
    id: "search",
    labelKey: "navigation.main.search",
    icon: Search,
    descriptionKey: "navigation.tooltips.searchDesc",
  },
  {
    id: "compare",
    labelKey: "navigation.main.compare",
    icon: GitCompare,
    descriptionKey: "navigation.tooltips.compareDesc",
  },
  {
    id: "translate",
    labelKey: "navigation.main.translate",
    icon: Languages,
    descriptionKey: "navigation.tooltips.translateDesc",
  },
  {
    id: "ai-demo",
    labelKey: "navigation.main.aiDemo",
    icon: Sparkles,
    descriptionKey: "navigation.tooltips.aiDemoDesc",
  },
  {
    id: "statistics",
    labelKey: "navigation.main.statistics",
    icon: BarChart3,
    descriptionKey: "navigation.tooltips.statisticsDesc",
  },
];

export function AppHeader({
  currentView = "dashboard",
  onNavigate,
  userName = "Admin User",
  notificationCount = 0,
  jobCount,
  hasSelectedJob = false,
  className,
}: AppHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { t } = useTranslation(["navigation", "common"]);

  const handleNavigation = (view: AppView) => {
    if (onNavigate) {
      onNavigate(view);
    }
    // Close mobile menu when navigating
    setMobileMenuOpen(false);
  };

  // Get initials for avatar
  const getInitials = (name: string): string => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header
      className={cn(
        // Base styles
        "fixed top-0 left-0 right-0 z-50",
        "h-16",

        // Glassmorphism effect
        "bg-white/95 dark:bg-slate-900/95",
        "backdrop-blur-md",

        // Modern elevation from elevation.css
        "shadow-card border-b",
        "border-slate-200/50 dark:border-slate-700/30",

        className,
      )}
    >
      <div className="h-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-full gap-4">
          {/* ========================================
              LEFT SECTION - Logo & Brand
              ======================================== */}
          <div className="flex items-center space-x-6">
            {/* Logo and Title */}
            <button
              onClick={() => handleNavigation("dashboard")}
              className="flex items-center group transition-all duration-300 hover:scale-105"
            >
              {/* Icon with gradient glow */}
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg blur-md opacity-20 group-hover:opacity-40 transition-opacity duration-300" />
                <Database className="relative w-7 h-7 text-blue-700 dark:text-blue-400 transition-transform duration-300 group-hover:rotate-[-5deg]" />
              </div>

              {/* Title with gradient */}
              <div className="ml-3 hidden sm:block">
                <div className="text-lg font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 dark:group-hover:from-blue-400 dark:group-hover:to-indigo-400 transition-all duration-300">
                  Job Description Database
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  AI-Powered Management System
                </p>
              </div>

              {/* Mobile short title */}
              <span className="ml-3 sm:hidden text-lg font-bold text-blue-700 dark:text-blue-400">
                JDDB
              </span>
            </button>
          </div>

          {/* ========================================
              CENTER SECTION - Primary Navigation
              ======================================== */}
          {/* Mobile Menu Button */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
                aria-label="Open navigation menu"
              >
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-[280px] sm:w-[320px]">
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-blue-700" />
                  JDDB Navigation
                </SheetTitle>
                <SheetDescription>
                  Navigate through the application
                </SheetDescription>
              </SheetHeader>
              <nav
                className="mt-6 flex flex-col space-y-1"
                role="tablist"
                aria-label="Main navigation"
              >
                {primaryNavItems.map((item) => {
                  const isActive = currentView === item.id;
                  const Icon = item.icon;
                  const requiresJob =
                    item.id === "translate" || item.id === "improve";
                  const isDisabled = requiresJob && !hasSelectedJob;

                  // Get translated label and description
                  const label = item.labelKey.startsWith("navigation.")
                    ? (t as any)(item.labelKey.replace("navigation.", ""))
                    : item.labelKey;
                  const description = item.descriptionKey?.startsWith(
                    "navigation.",
                  )
                    ? (t as any)(item.descriptionKey.replace("navigation.", ""))
                    : item.descriptionKey;

                  const tooltipText = isDisabled
                    ? t("tooltips.selectJobFirst")
                    : (description as string | undefined);

                  return (
                    <Button
                      key={item.id}
                      id={`${item.id}-tab`}
                      variant={isActive ? "secondary" : "ghost"}
                      onClick={isDisabled ? undefined : () => handleNavigation(item.id)}
                      disabled={isDisabled}
                      role="tab"
                      aria-selected={isActive}
                      aria-controls={isDisabled ? undefined : `${item.id}-panel`}
                      aria-disabled={isDisabled}
                      tabIndex={isDisabled ? -1 : isActive ? 0 : -1}
                      className={cn(
                        "w-full justify-start gap-3 h-11",
                        isActive &&
                          "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
                        isDisabled && "opacity-50 cursor-not-allowed",
                      )}
                      title={tooltipText}
                      aria-label={label}
                    >
                      <Icon className="w-4 h-4" />
                      <div className="flex-1 text-left">
                        <div className="font-medium">{label}</div>
                        {description && (
                          <div className="text-xs text-muted-foreground">
                            {description}
                          </div>
                        )}
                      </div>
                      {item.badge && item.badge > 0 && (
                        <Badge variant="destructive" className="ml-auto">
                          {item.badge > 9 ? "9+" : item.badge}
                        </Badge>
                      )}
                    </Button>
                  );
                })}
              </nav>
            </SheetContent>
          </Sheet>

          {/* Desktop Navigation */}
          <nav
            id="main-navigation"
            className="hidden lg:flex items-center space-x-1"
            role="tablist"
            aria-label="Main navigation"
          >
            {primaryNavItems.map((item) => {
              const isActive = currentView === item.id;
              const Icon = item.icon;

              // Disable translate and improve when no job is selected
              const requiresJob =
                item.id === "translate" || item.id === "improve";
              const isDisabled = requiresJob && !hasSelectedJob;

              // Get translated label and description
              const label = item.labelKey.startsWith("navigation.")
                ? (t as any)(item.labelKey.replace("navigation.", ""))
                : item.labelKey;
              const description = item.descriptionKey?.startsWith("navigation.")
                ? (t as any)(item.descriptionKey.replace("navigation.", ""))
                : item.descriptionKey;

              const tooltipText = isDisabled
                ? t("tooltips.selectJobFirst")
                : (description as string | undefined);

              return (
                <Button
                  key={item.id}
                  id={`${item.id}-tab`}
                  variant="ghost"
                  size="sm"
                  onClick={isDisabled ? undefined : () => handleNavigation(item.id)}
                  disabled={isDisabled}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={isDisabled ? undefined : `${item.id}-panel`}
                  aria-disabled={isDisabled}
                  aria-label={label}
                  tabIndex={isDisabled ? -1 : isActive ? 0 : -1}
                  className={cn(
                    // Base styles
                    "relative px-3 py-2 h-auto",
                    "flex flex-col items-center gap-1",
                    "transition-all duration-200",

                    // Hover state
                    !isDisabled &&
                      "hover:bg-slate-100/80 dark:hover:bg-slate-800/80",
                    !isDisabled && "hover:shadow-button",

                    // Active state
                    isActive && [
                      "bg-blue-50/80 dark:bg-blue-900/20",
                      "text-blue-600 dark:text-blue-400",
                      "shadow-inner",
                    ],

                    // Inactive state
                    !isActive &&
                      !isDisabled &&
                      "text-slate-600 dark:text-slate-400",

                    // Disabled state
                    isDisabled && "opacity-50 cursor-not-allowed",
                  )}
                  title={tooltipText}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-xs font-medium">{label}</span>

                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full" />
                  )}

                  {/* Badge for notifications */}
                  {item.badge && item.badge > 0 && (
                    <Badge
                      variant="destructive"
                      className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px]"
                    >
                      {item.badge > 9 ? "9+" : item.badge}
                    </Badge>
                  )}
                </Button>
              );
            })}
          </nav>

          {/* ========================================
              RIGHT SECTION - Controls & User Menu
              ======================================== */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* Notifications */}
            <Button
              variant="ghost"
              size="sm"
              className="relative p-2 hover:bg-slate-100 dark:hover:bg-slate-800 shadow-focus"
              title="Notifications"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              {notificationCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              )}
            </Button>

            {/* Language Toggle */}
            <LanguageToggle variant="ghost" className="shadow-focus" />

            {/* Theme Toggle */}
            <ThemeToggle size="sm" className="shadow-focus" />

            {/* Divider */}
            <div className="w-px h-6 bg-slate-200 dark:bg-slate-700" />

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex items-center gap-2 pl-2 pr-3 h-9 hover:bg-slate-100 dark:hover:bg-slate-800 shadow-focus"
                >
                  {/* Avatar */}
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-semibold shadow-elevation-2">
                    {getInitials(userName)}
                  </div>

                  {/* User greeting (hidden on mobile) */}
                  <div className="hidden sm:flex flex-col items-start">
                    <span className="text-xs text-slate-500 dark:text-slate-400 leading-none">
                      Hi,
                    </span>
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300 leading-none mt-0.5">
                      {userName.split(" ")[0]}
                    </span>
                  </div>
                </Button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end" className="w-56 shadow-dropdown">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{userName}</p>
                    <p className="text-xs text-muted-foreground">
                      admin@jddb.gc.ca
                    </p>
                  </div>
                </DropdownMenuLabel>

                <DropdownMenuSeparator />

                <DropdownMenuItem
                  onClick={() => handleNavigation("preferences")}
                >
                  <User className="mr-2 h-4 w-4" />
                  <span>Preferences</span>
                </DropdownMenuItem>

                <DropdownMenuItem
                  onClick={() => handleNavigation("system-health")}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  <span>System Settings</span>
                </DropdownMenuItem>

                <DropdownMenuItem>
                  <HelpCircle className="mr-2 h-4 w-4" />
                  <span>Help & Shortcuts</span>
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem className="text-red-600 dark:text-red-400">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  );
}

export default AppHeader;
