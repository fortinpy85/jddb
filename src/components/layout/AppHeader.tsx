/**
 * JDDB Application Header
 * Modern top navigation banner with logo, primary navigation, and user controls
 * Implements glassmorphism with elevated shadow system
 */

"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
} from "lucide-react";
import ThemeToggle from "@/components/ui/theme-toggle";

export type AppView =
  | "home"
  | "dashboard"
  | "jobs"
  | "upload"
  | "search"
  | "compare"
  | "translate"
  | "statistics"
  | "system-health"
  | "preferences";

interface AppHeaderProps {
  currentView?: AppView;
  onNavigate?: (view: AppView) => void;
  userName?: string;
  notificationCount?: number;
  jobCount?: number;
  className?: string;
}

interface NavItem {
  id: AppView;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  description?: string;
}

const primaryNavItems: NavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: BarChart3,
    description: "Overview and quick actions",
  },
  {
    id: "jobs",
    label: "Jobs",
    icon: Database,
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
    description: "Advanced search",
  },
  {
    id: "compare",
    label: "Compare",
    icon: GitCompare,
    description: "Compare jobs",
  },
  {
    id: "translate",
    label: "Translate",
    icon: Languages,
    description: "Bilingual editor",
  },
  {
    id: "statistics",
    label: "Statistics",
    icon: BarChart3,
    description: "Analytics and reports",
  },
];

export function AppHeader({
  currentView = "dashboard",
  onNavigate,
  userName = "Admin User",
  notificationCount = 0,
  jobCount,
  className,
}: AppHeaderProps) {
  const handleNavigation = (view: AppView) => {
    if (onNavigate) {
      onNavigate(view);
    }
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

        className
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
                <Database className="relative w-7 h-7 text-blue-600 dark:text-blue-400 transition-transform duration-300 group-hover:rotate-[-5deg]" />
              </div>

              {/* Title with gradient */}
              <div className="ml-3 hidden sm:block">
                <h1 className="text-lg font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-indigo-600 dark:group-hover:from-blue-400 dark:group-hover:to-indigo-400 transition-all duration-300">
                  Job Description Database
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  AI-Powered Management System
                </p>
              </div>

              {/* Mobile short title */}
              <span className="ml-3 sm:hidden text-lg font-bold text-blue-600 dark:text-blue-400">
                JDDB
              </span>
            </button>
          </div>

          {/* ========================================
              CENTER SECTION - Primary Navigation
              ======================================== */}
          <nav className="lg:flex items-center space-x-1 max-lg:hidden">
            {primaryNavItems.map((item) => {
              const isActive = currentView === item.id;
              const Icon = item.icon;

              return (
                <Button
                  key={item.id}
                  variant="ghost"
                  size="sm"
                  onClick={() => handleNavigation(item.id)}
                  className={cn(
                    // Base styles
                    "relative px-3 py-2 h-auto",
                    "flex flex-col items-center gap-1",
                    "transition-all duration-200",

                    // Hover state
                    "hover:bg-slate-100/80 dark:hover:bg-slate-800/80",
                    "hover:shadow-button",

                    // Active state
                    isActive && [
                      "bg-blue-50/80 dark:bg-blue-900/20",
                      "text-blue-600 dark:text-blue-400",
                      "shadow-inner",
                    ],

                    // Inactive state
                    !isActive && "text-slate-600 dark:text-slate-400"
                  )}
                  title={item.description}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-xs font-medium">{item.label}</span>

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
            {/* Job Count Badge */}
            {jobCount !== undefined && (
              <div className="hidden sm:flex items-center px-3 py-1.5 rounded-full bg-slate-100/80 dark:bg-slate-800/80 border border-slate-200/50 dark:border-slate-700/50 shadow-sm">
                <Database className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 mr-1.5" />
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {jobCount}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">
                  jobs
                </span>
              </div>
            )}

            {/* Quick Search Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleNavigation("search")}
              className="hidden md:flex items-center gap-2 px-3 h-9 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 shadow-focus"
              title="Quick search (⌘K)"
            >
              <Search className="w-4 h-4" />
              <span className="text-xs">Search</span>
              <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded">
                <Command className="w-2.5 h-2.5" />K
              </kbd>
            </Button>

            {/* Notifications */}
            <Button
              variant="ghost"
              size="sm"
              className="relative p-2 hover:bg-slate-100 dark:hover:bg-slate-800 shadow-focus"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              {notificationCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              )}
            </Button>

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

              <DropdownMenuContent
                align="end"
                className="w-56 shadow-dropdown"
              >
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{userName}</p>
                    <p className="text-xs text-muted-foreground">
                      admin@jddb.gc.ca
                    </p>
                  </div>
                </DropdownMenuLabel>

                <DropdownMenuSeparator />

                <DropdownMenuItem onClick={() => handleNavigation("preferences")}>
                  <User className="mr-2 h-4 w-4" />
                  <span>Preferences</span>
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => handleNavigation("system-health")}>
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
