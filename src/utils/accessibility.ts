/**
 * Accessibility Testing Utilities
 * Integrates axe-core for automated WCAG 2.0 compliance checking
 */

import type React from "react";
import { logger } from "@/utils/logger";

/**
 * Initialize axe-core accessibility testing in development mode
 * Automatically runs accessibility audits and logs violations to console
 *
 * @param React - React library
 * @param ReactDOM - ReactDOM library
 * @param delay - Delay in milliseconds before running first audit (default: 1000)
 */
export async function initializeAxe(
  React: typeof import("react"),
  ReactDOM: typeof import("react-dom/client"),
  delay: number = 1000,
): Promise<void> {
  // Only run in development mode
  if (process.env.NODE_ENV !== "production") {
    try {
      const axe = await import("@axe-core/react");
      await axe.default(React, ReactDOM, delay, {
        // axe-core configuration
        rules: [
          {
            id: "color-contrast",
            enabled: true,
          },
          {
            id: "label",
            enabled: true,
          },
          {
            id: "button-name",
            enabled: true,
          },
          {
            id: "link-name",
            enabled: true,
          },
          {
            id: "image-alt",
            enabled: true,
          },
          {
            id: "list",
            enabled: true,
          },
          {
            id: "listitem",
            enabled: true,
          },
        ],
      });

      logger.info("[Accessibility] axe-core initialized successfully");
      logger.info("[Accessibility] Automated WCAG 2.0 audits will run after each render");
    } catch (error) {
      logger.warn("[Accessibility] Failed to initialize axe-core:", {
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }
}

/**
 * Manual accessibility audit
 * Run an on-demand accessibility check
 *
 * @returns Promise with audit results
 */
export async function runAccessibilityAudit() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const axe = await import("axe-core");
    const results = await axe.default.run();

    logger.info("[Accessibility Audit] Results", {
      violations: results.violations.length,
      passes: results.passes.length,
      incomplete: results.incomplete.length,
      inapplicable: results.inapplicable.length,
    });

    if (results.violations.length > 0) {
      results.violations.forEach((violation) => {
        logger.error(`${violation.impact?.toUpperCase()} - ${violation.help}`, {
          description: violation.description,
          helpUrl: violation.helpUrl,
          affectedNodes: violation.nodes.length,
          nodes: violation.nodes.map((node, index) => ({
            index: index + 1,
            html: node.html,
            fix: node.failureSummary,
          })),
        });
      });
    }

    if (results.incomplete.length > 0) {
      logger.warn("Incomplete accessibility checks", {
        items: results.incomplete.map((item) => ({
          help: item.help,
          description: item.description,
        })),
      });
    }

    return results;
  } catch (error) {
    logger.error("[Accessibility] Audit failed:", error);
    return null;
  }
}

/**
 * Get accessibility score (0-100)
 * Calculate a simple score based on violations
 *
 * @returns Accessibility score
 */
export async function getAccessibilityScore(): Promise<number> {
  const results = await runAccessibilityAudit();
  if (!results) return 0;

  const total = results.violations.length + results.passes.length;
  if (total === 0) return 100;

  // Weight violations by impact
  let violationScore = 0;
  results.violations.forEach((v) => {
    const weight =
      v.impact === "critical"
        ? 4
        : v.impact === "serious"
          ? 3
          : v.impact === "moderate"
            ? 2
            : 1;
    violationScore += weight * v.nodes.length;
  });

  const passScore = results.passes.length;
  const totalScore = passScore + violationScore;

  const score = Math.round((passScore / totalScore) * 100);
  return Math.max(0, Math.min(100, score));
}

/**
 * Export accessibility report to console
 * Formatted report with detailed information
 */
export async function exportAccessibilityReport() {
  const results = await runAccessibilityAudit();
  if (!results) return;

  const score = await getAccessibilityScore();

  const byImpact = {
    critical: results.violations.filter((v) => v.impact === "critical"),
    serious: results.violations.filter((v) => v.impact === "serious"),
    moderate: results.violations.filter((v) => v.impact === "moderate"),
    minor: results.violations.filter((v) => v.impact === "minor"),
  };

  const wcagPass = !results.violations.some(
    (v) => v.impact === "critical" || v.impact === "serious",
  );

  logger.info("📊 Accessibility Report", {
    score: `${score}/100`,
    totalRulesChecked: results.passes.length + results.violations.length,
    wcag2Level: wcagPass ? "PASS" : "FAIL",
    summary: {
      passes: results.passes.length,
      violations: results.violations.length,
      incomplete: results.incomplete.length,
      inapplicable: results.inapplicable.length,
    },
    topIssuesByImpact: {
      critical: byImpact.critical.length,
      serious: byImpact.serious.length,
      moderate: byImpact.moderate.length,
      minor: byImpact.minor.length,
    },
  });

  return {
    score,
    summary: {
      passes: results.passes.length,
      violations: results.violations.length,
      incomplete: results.incomplete.length,
    },
    violations: results.violations,
  };
}

// Make utilities available globally in development
if (typeof window !== "undefined" && process.env.NODE_ENV !== "production") {
  (window as any).a11y = {
    audit: runAccessibilityAudit,
    score: getAccessibilityScore,
    report: exportAccessibilityReport,
  };

  logger.info("[Accessibility] Global utilities available", {
    methods: [
      "window.a11y.audit()  - Run accessibility audit",
      "window.a11y.score()  - Get accessibility score",
      "window.a11y.report() - Export detailed report",
    ],
  });
}
