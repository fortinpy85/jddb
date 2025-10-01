/**
 * Two-Panel Layout Component
 * Modern layout structure with left sidebar panel, center content, and optional right panel
 * Supports responsive design with collapsible panels
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
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export interface TwoPanelLayoutProps {
  children: ReactNode;

  // Left Panel Props
  leftPanel?: ReactNode;
  leftPanelWidth?: number; // Width in pixels (default: 300)
  leftPanelCollapsedWidth?: number; // Width when collapsed (default: 80)
  showLeftPanel?: boolean;
  leftPanelCollapsible?: boolean;
  initialLeftPanelCollapsed?: boolean;
  onLeftPanelToggle?: (collapsed: boolean) => void;

  // Right Panel Props
  rightPanel?: ReactNode;
  rightPanelWidth?: number; // Width in pixels (default: 320)
  showRightPanel?: boolean;
  rightPanelCollapsible?: boolean;
  initialRightPanelCollapsed?: boolean;
  onRightPanelToggle?: (collapsed: boolean) => void;

  // Layout Props
  className?: string;
  contentClassName?: string;
  leftPanelClassName?: string;
  rightPanelClassName?: string;

  // Header/Footer
  header?: ReactNode;
  footer?: ReactNode;

  // Responsive
  hideLeftPanelOnMobile?: boolean;
  hideRightPanelOnMobile?: boolean;
}

export function TwoPanelLayout({
  children,
  leftPanel,
  leftPanelWidth = 300,
  leftPanelCollapsedWidth = 80,
  showLeftPanel = true,
  leftPanelCollapsible = true,
  initialLeftPanelCollapsed = false,
  onLeftPanelToggle,
  rightPanel,
  rightPanelWidth = 320,
  showRightPanel = false,
  rightPanelCollapsible = true,
  initialRightPanelCollapsed = false,
  onRightPanelToggle,
  className,
  contentClassName,
  leftPanelClassName,
  rightPanelClassName,
  header,
  footer,
  hideLeftPanelOnMobile = true,
  hideRightPanelOnMobile = true,
}: TwoPanelLayoutProps) {
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(
    initialLeftPanelCollapsed
  );
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(
    initialRightPanelCollapsed
  );

  const handleLeftPanelToggle = () => {
    const newState = !leftPanelCollapsed;
    setLeftPanelCollapsed(newState);
    onLeftPanelToggle?.(newState);
  };

  const handleRightPanelToggle = () => {
    const newState = !rightPanelCollapsed;
    setRightPanelCollapsed(newState);
    onRightPanelToggle?.(newState);
  };

  const currentLeftPanelWidth = leftPanelCollapsed
    ? leftPanelCollapsedWidth
    : leftPanelWidth;

  return (
    <div
      className={cn(
        "flex flex-col min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-900 dark:via-slate-800/30 dark:to-slate-900/20",
        className
      )}
    >
      {/* Header */}
      {header && (
        <div className="flex-shrink-0 z-50">
          {header}
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        {showLeftPanel && leftPanel && (
          <aside
            style={{
              width: leftPanelCollapsed ? `${leftPanelCollapsedWidth}px` : `${leftPanelWidth}px`,
            }}
            className={cn(
              "flex-shrink-0 transition-all duration-300 ease-in-out",
              "bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm",
              "border-r border-slate-200/50 dark:border-slate-700/50",
              "shadow-card",
              "overflow-y-auto overflow-x-hidden",
              hideLeftPanelOnMobile && "hidden lg:block",
              leftPanelClassName
            )}
          >
            <div className="relative h-full">
              {/* Collapse/Expand Button */}
              {leftPanelCollapsible && (
                <div className="absolute top-4 right-2 z-10">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLeftPanelToggle}
                    className="h-8 w-8 p-0 hover:bg-slate-100 dark:hover:bg-slate-700 shadow-button"
                    title={leftPanelCollapsed ? "Expand panel" : "Collapse panel"}
                  >
                    {leftPanelCollapsed ? (
                      <PanelLeftOpen className="h-4 w-4" />
                    ) : (
                      <PanelLeftClose className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              )}

              {/* Left Panel Content */}
              <div className={cn("h-full", leftPanelCollapsed && "px-2 py-4")}>
                {leftPanel}
              </div>
            </div>
          </aside>
        )}

        {/* Center Content */}
        <main
          className={cn(
            "flex-1 overflow-y-auto overflow-x-hidden",
            "bg-transparent",
            contentClassName
          )}
        >
          <div className="h-full p-4 sm:p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              {children}
            </div>
          </div>
        </main>

        {/* Right Panel */}
        {showRightPanel && rightPanel && (
          <aside
            style={{
              width: rightPanelCollapsed ? "48px" : `${rightPanelWidth}px`,
            }}
            className={cn(
              "flex-shrink-0 transition-all duration-300 ease-in-out",
              "bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm",
              "border-l border-slate-200/50 dark:border-slate-700/50",
              "shadow-card",
              "overflow-y-auto overflow-x-hidden",
              hideRightPanelOnMobile && "hidden xl:block",
              rightPanelClassName
            )}
          >
            <div className="relative h-full">
              {/* Collapse/Expand Button */}
              {rightPanelCollapsible && (
                <div className="absolute top-4 left-2 z-10">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRightPanelToggle}
                    className="h-8 w-8 p-0 hover:bg-slate-100 dark:hover:bg-slate-700 shadow-button"
                    title={rightPanelCollapsed ? "Expand panel" : "Collapse panel"}
                  >
                    {rightPanelCollapsed ? (
                      <PanelRightOpen className="h-4 w-4" />
                    ) : (
                      <PanelRightClose className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              )}

              {/* Right Panel Content */}
              <div className={cn("h-full", !rightPanelCollapsed && "p-4")}>
                {!rightPanelCollapsed && rightPanel}
              </div>
            </div>
          </aside>
        )}
      </div>

      {/* Footer */}
      {footer && (
        <div className="flex-shrink-0">
          {footer}
        </div>
      )}
    </div>
  );
}

/**
 * Mobile Panel Overlay Component
 * Shows left or right panel as an overlay on mobile devices
 */
interface MobilePanelOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: "left" | "right";
  title?: string;
}

export function MobilePanelOverlay({
  isOpen,
  onClose,
  children,
  side = "left",
  title,
}: MobilePanelOverlayProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={cn(
          "fixed top-0 bottom-0 z-50 w-80 max-w-[85vw]",
          "bg-white dark:bg-slate-800 shadow-modal",
          "transform transition-transform duration-300 ease-in-out",
          "overflow-y-auto",
          "lg:hidden",
          side === "left" ? "left-0" : "right-0"
        )}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between">
            {title && (
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {title}
              </h2>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="ml-auto"
            >
              {side === "left" ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">{children}</div>
      </div>
    </>
  );
}

/**
 * Panel Section Component
 * Standardized section wrapper for panel content
 */
interface PanelSectionProps {
  title?: string;
  icon?: React.ComponentType<{ className?: string }>;
  children: ReactNode;
  className?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  headerActions?: ReactNode;
}

export function PanelSection({
  title,
  icon: Icon,
  children,
  className,
  collapsible = false,
  defaultCollapsed = false,
  headerActions,
}: PanelSectionProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <div className={cn("space-y-3", className)}>
      {(title || headerActions) && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => collapsible && setCollapsed(!collapsed)}
            className={cn(
              "flex items-center space-x-2 text-sm font-semibold text-slate-700 dark:text-slate-300",
              collapsible && "hover:text-slate-900 dark:hover:text-slate-100 cursor-pointer"
            )}
            disabled={!collapsible}
          >
            {Icon && <Icon className="w-4 h-4" />}
            {title && <span>{title}</span>}
            {collapsible && (
              <ChevronRight
                className={cn(
                  "w-4 h-4 transition-transform",
                  !collapsed && "transform rotate-90"
                )}
              />
            )}
          </button>
          {headerActions && <div className="flex items-center space-x-2">{headerActions}</div>}
        </div>
      )}
      {!collapsed && <div>{children}</div>}
    </div>
  );
}
