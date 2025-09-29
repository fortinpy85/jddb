"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { ChevronRight, CheckCircle } from "lucide-react";

export interface SidebarNavItem {
  id: string;
  title: string;
  icon?: React.ReactNode;
  isActive?: boolean;
  isCompleted?: boolean;
  isRequired?: boolean;
  children?: SidebarNavItem[];
}

interface SidebarNavProps {
  items: SidebarNavItem[];
  onItemClick?: (item: SidebarNavItem) => void;
  className?: string;
}

export function SidebarNav({ items, onItemClick, className }: SidebarNavProps) {
  const handleItemClick = (item: SidebarNavItem) => {
    onItemClick?.(item);
  };

  const renderNavItem = (item: SidebarNavItem, level: number = 0) => (
    <div key={item.id} className={cn("", { "ml-4": level > 0 })}>
      <button
        onClick={() => handleItemClick(item)}
        className={cn(
          "w-full flex items-center justify-between px-3 py-2.5 text-left text-sm font-medium rounded-lg transition-all duration-150 group",
          {
            "bg-blue-500 text-white shadow-sm": item.isActive,
            "bg-green-50 text-green-700 border border-green-200":
              item.isCompleted && !item.isActive,
            "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800":
              !item.isActive && !item.isCompleted,
            "border-l-4 border-blue-500": item.isActive,
            "border-l-4 border-green-400": item.isCompleted && !item.isActive,
          },
        )}
      >
        <div className="flex items-center space-x-3">
          {/* Status Indicator */}
          <div className="flex-shrink-0">
            {item.isCompleted ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : item.icon ? (
              <div
                className={cn("w-4 h-4", {
                  "text-white": item.isActive,
                  "text-gray-500": !item.isActive,
                })}
              >
                {item.icon}
              </div>
            ) : (
              <div
                className={cn("w-2 h-2 rounded-full", {
                  "bg-white": item.isActive,
                  "bg-blue-400": !item.isActive && !item.isCompleted,
                  "bg-green-400": item.isCompleted,
                })}
              />
            )}
          </div>

          {/* Title */}
          <span className="flex-1 truncate">{item.title}</span>

          {/* Required Indicator */}
          {item.isRequired && !item.isCompleted && (
            <span className="text-xs text-red-500 font-medium">*</span>
          )}
        </div>

        {/* Expand Arrow for items with children */}
        {item.children && item.children.length > 0 && (
          <ChevronRight
            className={cn("w-4 h-4 transition-transform", {
              "text-white": item.isActive,
              "text-gray-400": !item.isActive,
            })}
          />
        )}
      </button>

      {/* Render children if they exist */}
      {item.children && item.children.length > 0 && (
        <div className="mt-1 space-y-1">
          {item.children.map((child) => renderNavItem(child, level + 1))}
        </div>
      )}
    </div>
  );

  return (
    <nav className={cn("space-y-1", className)}>
      {items.map((item) => renderNavItem(item))}
    </nav>
  );
}

// Preset navigation configurations
export const JOB_MANAGEMENT_NAV: SidebarNavItem[] = [
  {
    id: "preview",
    title: "Preview Job",
    isActive: false,
    isCompleted: true,
  },
  {
    id: "information",
    title: "Job Information",
    isActive: true,
    isCompleted: true,
    isRequired: true,
  },
  {
    id: "summary",
    title: "Job Summary",
    isActive: false,
    isCompleted: true,
    isRequired: true,
  },
  {
    id: "requirements",
    title: "General Requirements",
    isActive: false,
    isCompleted: false,
    isRequired: true,
  },
  {
    id: "skills",
    title: "General Skills",
    isActive: false,
    isCompleted: false,
    isRequired: true,
  },
  {
    id: "education",
    title: "Education",
    isActive: false,
    isCompleted: false,
    isRequired: true,
  },
  {
    id: "experience",
    title: "Experience",
    isActive: false,
    isCompleted: false,
    isRequired: true,
  },
  {
    id: "licensure",
    title: "Licensure",
    isActive: false,
    isCompleted: false,
    isRequired: false,
  },
  {
    id: "competencies",
    title: "Competencies",
    isActive: false,
    isCompleted: false,
    isRequired: true,
  },
];

export const TRANSLATION_NAV: SidebarNavItem[] = [
  {
    id: "source-text",
    title: "Source Text",
    isActive: false,
    isCompleted: true,
  },
  {
    id: "translation",
    title: "Translation",
    isActive: true,
    isCompleted: false,
  },
  {
    id: "quality-check",
    title: "Quality Check",
    isActive: false,
    isCompleted: false,
  },
  {
    id: "terminology",
    title: "Terminology",
    isActive: false,
    isCompleted: false,
  },
  {
    id: "review",
    title: "Review & Approve",
    isActive: false,
    isCompleted: false,
  },
];
