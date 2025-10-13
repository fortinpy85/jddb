/**
 * Skip Links Component
 * WCAG 2.0 Level AA compliance - Success Criterion 2.4.1 (Bypass Blocks)
 * Allows keyboard users to skip directly to main content areas
 * Following WET-BOEW pattern for Government of Canada compliance
 */

"use client";

import React from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";

interface SkipLink {
  id: string;
  target: string;
  labelKey: string;
}

const skipLinks: SkipLink[] = [
  {
    id: "skip-main",
    target: "main-content",
    labelKey: "accessibility.skipToMain",
  },
  {
    id: "skip-nav",
    target: "main-navigation",
    labelKey: "accessibility.skipToNavigation",
  },
  {
    id: "skip-search",
    target: "search-interface",
    labelKey: "accessibility.skipToSearch",
  },
];

export function SkipLinks() {
  const { t } = useTranslation("common");

  const handleSkipClick = (
    e: React.MouseEvent<HTMLAnchorElement>,
    targetId: string,
  ) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="skip-links" role="navigation" aria-label="Skip links">
      {skipLinks.map((link) => (
        <a
          key={link.id}
          href={`#${link.target}`}
          onClick={(e) => handleSkipClick(e, link.target)}
          className={cn(
            // Position off-screen by default
            "absolute left-[-9999px] top-4 z-[9999]",
            "px-4 py-2 text-sm font-medium",
            "bg-blue-600 text-white rounded-md shadow-lg",
            "transition-all duration-200",
            // Show on focus (keyboard navigation)
            "focus:left-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
            // Hover state (when visible)
            "hover:bg-blue-700",
          )}
        >
          {(t as any)(link.labelKey)}
        </a>
      ))}
    </div>
  );
}

export default SkipLinks;
