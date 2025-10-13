/**
 * useAccessibility Hook
 * Runs axe-core accessibility checks in development mode
 * Reports WCAG 2.0 violations to the console
 */

import { useEffect } from "react";
import { logger } from "@/utils/logger";

export function useAccessibility(
  enabled = process.env.NODE_ENV === "development",
) {
  useEffect(() => {
    if (!enabled) return;

    // Dynamically import axe-core only in development
    import("@axe-core/react")
      .then((axe) => {
        const React = require("react");
        const ReactDOM = require("react-dom");

        axe.default(React, ReactDOM, 1000, {
          rules: [
            // WCAG 2.0 Level AA rules
            { id: "color-contrast", enabled: true },
            { id: "label", enabled: true },
            { id: "button-name", enabled: true },
            { id: "link-name", enabled: true },
            { id: "image-alt", enabled: true },
            { id: "aria-valid-attr", enabled: true },
            { id: "aria-valid-attr-value", enabled: true },
            { id: "aria-required-attr", enabled: true },
            { id: "aria-roles", enabled: true },
            { id: "duplicate-id", enabled: true },
            { id: "html-has-lang", enabled: true },
            { id: "landmark-one-main", enabled: true },
            { id: "page-has-heading-one", enabled: true },
          ],
        });
      })
      .catch((error) => {
        logger.warn("Failed to initialize axe-core:", error);
      });
  }, [enabled]);
}

export default useAccessibility;
