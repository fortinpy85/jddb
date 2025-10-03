
/**
 * Profile Header Component
 * Sits below the main AppHeader and contains contextual navigation 
 * like breadcrumbs and open tabs.
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Home, ChevronRight, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

export interface TabItem {
  id: string;
  title: string;
  active: boolean;
}

export interface ProfileHeaderProps {
  breadcrumbs?: BreadcrumbItem[];
  openTabs?: TabItem[];
  onTabClick?: (id: string) => void;
  onTabClose?: (id: string) => void;
  className?: string;
}

export function ProfileHeader({
  breadcrumbs = [],
  openTabs = [],
  onTabClick,
  onTabClose,
  className,
}: ProfileHeaderProps) {
  return (
    <div
      className={cn(
        "fixed top-16 left-0 right-0 z-40 h-16",
        "bg-white/80 dark:bg-slate-800/80 backdrop-blur-md",
        "border-b border-slate-200/50 dark:border-slate-700/50",
        "px-4 sm:px-6 lg:px-8",
        className,
      )}
    >
      <div className="flex items-center justify-between h-full">
        {/* Breadcrumbs */}
        <nav className="flex items-center text-sm font-medium text-slate-600 dark:text-slate-400">
          <Home className="w-4 h-4 mr-2 flex-shrink-0" />
          {breadcrumbs.map((item, index) => (
            <React.Fragment key={index}>
              <a
                href={item.href}
                onClick={item.onClick}
                className="hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
              >
                {item.label}
              </a>
              {index < breadcrumbs.length - 1 && (
                <ChevronRight className="w-4 h-4 mx-1 text-slate-400 dark:text-slate-500" />
              )}
            </React.Fragment>
          ))}
        </nav>

        {/* Open Tabs */}
        <div className="flex items-center space-x-1">
          {openTabs.map((tab) => (
            <Button
              key={tab.id}
              variant={tab.active ? "secondary" : "ghost"}
              size="sm"
              onClick={() => onTabClick?.(tab.id)}
              className="group pl-3 pr-2 py-1 h-auto text-xs"
            >
              <span>{tab.title}</span>
              <X
                className="w-3 h-3 ml-2 text-slate-500 group-hover:text-slate-900 dark:group-hover:text-slate-200"
                onClick={(e) => {
                  e.stopPropagation();
                  onTabClose?.(tab.id);
                }}
              />
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
