/**
 * Three-Column Layout Component
 * New layout structure with a permanent narrow left panel, a collapsible middle panel,
 * and a main content area on the right.
 */

"use client";

import React, { useState, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";

export interface ThreeColumnLayoutProps {
  children: ReactNode;

  // Left Panel (Permanent)
  leftPanel?: ReactNode;
  leftPanelWidth?: number;

  // Middle Panel (Collapsible)
  middlePanel?: ReactNode;
  middlePanelWidth?: number;
  initialMiddlePanelCollapsed?: boolean;
  onMiddlePanelToggle?: (collapsed: boolean) => void;

  // Header/Footer
  header?: ReactNode;
  profileHeader?: ReactNode;
  alertBanner?: ReactNode;
  footer?: ReactNode;

  // classNames
  className?: string;
  contentClassName?: string;
  leftPanelClassName?: string;
  middlePanelClassName?: string;
}

export function ThreeColumnLayout({
  children,
  leftPanel,
  leftPanelWidth = 280,
  middlePanel,
  middlePanelWidth = 320,
  initialMiddlePanelCollapsed = true,
  onMiddlePanelToggle,
  header,
  profileHeader,
  alertBanner,
  footer,
  className,
  contentClassName,
  leftPanelClassName,
  middlePanelClassName,
}: ThreeColumnLayoutProps) {
  const [middlePanelCollapsed, setMiddlePanelCollapsed] = useState(
    initialMiddlePanelCollapsed,
  );

  const handleMiddlePanelToggle = () => {
    const newState = !middlePanelCollapsed;
    setMiddlePanelCollapsed(newState);
    onMiddlePanelToggle?.(newState);
  };

  return (
    <div
      className={cn(
        "flex flex-col min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-900 dark:via-slate-800/30 dark:to-slate-900/20",
        className,
      )}
    >
      {header && <div className="flex-shrink-0 relative z-50">{header}</div>}
      {profileHeader && (
        <div className="flex-shrink-0 relative z-40">{profileHeader}</div>
      )}
      {alertBanner && (
        <div className="flex-shrink-0 relative z-30 mt-32">{alertBanner}</div>
      )}

      <div className="flex flex-1 overflow-hidden pt-32">
        {/* Left Panel (Permanent) */}
        {leftPanel && (
          <aside
            style={{ width: `${leftPanelWidth}px` }}
            className={cn(
              "flex-shrink-0 transition-all duration-300 ease-in-out",
              "bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm",
              "border-r border-slate-200/50 dark:border-slate-700/50",
              "shadow-card hidden lg:block",
              leftPanelClassName,
            )}
          >
            {leftPanel}
          </aside>
        )}

        {/* Middle Panel (Collapsible) */}
        {middlePanel && (
          <aside
            style={{
              width: middlePanelCollapsed ? `48px` : `${middlePanelWidth}px`,
            }}
            className={cn(
              "flex-shrink-0 transition-all duration-300 ease-in-out",
              "bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm",
              "border-r border-slate-200/50 dark:border-slate-700/50",
              "shadow-card hidden md:block",
              middlePanelClassName,
            )}
          >
            <div className="relative h-full">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMiddlePanelToggle}
                className="absolute top-4 right-2 z-10 h-8 w-8 p-0 hover:bg-slate-100 dark:hover:bg-slate-700 shadow-button"
                title={
                  middlePanelCollapsed ? "Expand AI Panel" : "Collapse AI Panel"
                }
                aria-label={
                  middlePanelCollapsed ? "Expand AI Panel" : "Collapse AI Panel"
                }
              >
                {middlePanelCollapsed ? (
                  <PanelLeftOpen className="h-4 w-4" />
                ) : (
                  <PanelRightClose className="h-4 w-4" />
                )}
              </Button>
              <div
                className={cn(
                  "h-full",
                  middlePanelCollapsed && "overflow-hidden",
                )}
              >
                {!middlePanelCollapsed && middlePanel}
              </div>
            </div>
          </aside>
        )}

        {/* Main Content */}
        <main
          className={cn(
            "flex-1 overflow-y-auto overflow-x-hidden",
            "bg-transparent",
            contentClassName,
          )}
        >
          <div className="h-full p-4 sm:p-6 lg:p-8">
            <div className="max-w-full mx-auto">{children}</div>
          </div>
        </main>
      </div>

      {footer && <div className="flex-shrink-0">{footer}</div>}
    </div>
  );
}
