/**
 * Accessibility Testing Utilities
 * Integrates axe-core for automated WCAG 2.0 compliance checking
 */

import type React from "react";

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

      console.log(
        "%c[Accessibility] axe-core initialized successfully",
        "color: #22c55e; font-weight: bold",
      );
      console.log(
        "%c[Accessibility] Automated WCAG 2.0 audits will run after each render",
        "color: #3b82f6",
      );
    } catch (error) {
      console.warn("[Accessibility] Failed to initialize axe-core:", error);
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

    console.group(
      "%c[Accessibility Audit] Results",
      "color: #8b5cf6; font-weight: bold; font-size: 14px",
    );
    console.log("Violations:", results.violations.length);
    console.log("Passes:", results.passes.length);
    console.log("Incomplete:", results.incomplete.length);
    console.log("Inapplicable:", results.inapplicable.length);

    if (results.violations.length > 0) {
      console.group("❌ Violations");
      results.violations.forEach((violation) => {
        console.group(
          `%c${violation.impact?.toUpperCase()} - ${violation.help}`,
          `color: ${violation.impact === "critical" || violation.impact === "serious" ? "#ef4444" : "#f59e0b"}; font-weight: bold`,
        );
        console.log("Description:", violation.description);
        console.log("Help URL:", violation.helpUrl);
        console.log("Affected nodes:", violation.nodes.length);
        violation.nodes.forEach((node, index) => {
          console.log(`  ${index + 1}.`, node.html);
          console.log("     Fix:", node.failureSummary);
        });
        console.groupEnd();
      });
      console.groupEnd();
    }

    if (results.incomplete.length > 0) {
      console.group("⚠️  Incomplete Checks");
      results.incomplete.forEach((item) => {
        console.log(`${item.help} - ${item.description}`);
      });
      console.groupEnd();
    }

    console.groupEnd();

    return results;
  } catch (error) {
    console.error("[Accessibility] Audit failed:", error);
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

  console.group(
    "%c📊 Accessibility Report",
    "color: #06b6d4; font-weight: bold; font-size: 16px",
  );
  console.log(`Score: ${score}/100`);
  console.log(
    `Total Rules Checked: ${results.passes.length + results.violations.length}`,
  );
  console.log(
    `WCAG 2.0 Level: ${results.violations.some((v) => v.impact === "critical" || v.impact === "serious") ? "❌ FAIL" : "✅ PASS"}`,
  );
  console.log("\nSummary:");
  console.log(`  ✅ Passes: ${results.passes.length}`);
  console.log(`  ❌ Violations: ${results.violations.length}`);
  console.log(`  ⚠️  Incomplete: ${results.incomplete.length}`);
  console.log(`  ℹ️  Inapplicable: ${results.inapplicable.length}`);

  if (results.violations.length > 0) {
    console.log("\nTop Issues by Impact:");
    const byImpact = {
      critical: results.violations.filter((v) => v.impact === "critical"),
      serious: results.violations.filter((v) => v.impact === "serious"),
      moderate: results.violations.filter((v) => v.impact === "moderate"),
      minor: results.violations.filter((v) => v.impact === "minor"),
    };

    if (byImpact.critical.length > 0)
      console.log(`  🔴 Critical: ${byImpact.critical.length}`);
    if (byImpact.serious.length > 0)
      console.log(`  🟠 Serious: ${byImpact.serious.length}`);
    if (byImpact.moderate.length > 0)
      console.log(`  🟡 Moderate: ${byImpact.moderate.length}`);
    if (byImpact.minor.length > 0)
      console.log(`  🟢 Minor: ${byImpact.minor.length}`);
  }

  console.groupEnd();

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

  console.log(
    "%c[Accessibility] Global utilities available:",
    "color: #8b5cf6; font-weight: bold",
  );
  console.log("  window.a11y.audit()  - Run accessibility audit");
  console.log("  window.a11y.score()  - Get accessibility score");
  console.log("  window.a11y.report() - Export detailed report");
}
