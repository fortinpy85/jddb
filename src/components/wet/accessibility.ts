/**
 * Accessibility Utilities
 * Helper functions for WCAG 2.0 Level AA compliance
 */

/**
 * Generates a unique ID for ARIA relationships
 * @param prefix - Prefix for the ID
 * @returns Unique ID string
 */
export function generateAriaId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Announces a message to screen readers
 * Uses ARIA live regions for dynamic content updates
 * @param message - Message to announce
 * @param priority - 'polite' (default) or 'assertive'
 */
export function announceToScreenReader(
  message: string,
  priority: "polite" | "assertive" = "polite",
): void {
  const announcement = document.createElement("div");
  announcement.setAttribute("role", "status");
  announcement.setAttribute("aria-live", priority);
  announcement.setAttribute("aria-atomic", "true");
  announcement.className = "sr-only";
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

/**
 * Manages focus for modal dialogs and overlays
 * Returns a cleanup function to restore focus
 * @param element - Element to focus
 * @returns Cleanup function
 */
export function trapFocus(element: HTMLElement): () => void {
  const previousActiveElement = document.activeElement as HTMLElement;

  // Focus the element
  element.focus();

  // Get all focusable elements within the container
  const focusableElements = element.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  // Handle tab key
  const handleTab = (e: KeyboardEvent) => {
    if (e.key !== "Tab") return;

    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };

  element.addEventListener("keydown", handleTab);

  // Return cleanup function
  return () => {
    element.removeEventListener("keydown", handleTab);
    if (previousActiveElement) {
      previousActiveElement.focus();
    }
  };
}

/**
 * Checks if an element is visible to screen readers
 * @param element - Element to check
 * @returns True if visible to screen readers
 */
export function isAccessible(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  const isHidden =
    element.hasAttribute("aria-hidden") &&
    element.getAttribute("aria-hidden") === "true";
  const isDisplayNone = style.display === "none";
  const isVisibilityHidden = style.visibility === "hidden";

  return !isHidden && !isDisplayNone && !isVisibilityHidden;
}

/**
 * Creates ARIA label for sortable table headers
 * @param column - Column name
 * @param sortDirection - Current sort direction
 * @returns ARIA label string
 */
export function getTableSortLabel(
  column: string,
  sortDirection?: "asc" | "desc",
): string {
  if (!sortDirection) {
    return `${column}, sortable`;
  }
  const direction = sortDirection === "asc" ? "ascending" : "descending";
  return `${column}, sorted ${direction}`;
}

/**
 * Creates ARIA label for pagination
 * @param current - Current page
 * @param total - Total pages
 * @returns ARIA label string
 */
export function getPaginationLabel(current: number, total: number): string {
  return `Page ${current} of ${total}`;
}

/**
 * Creates ARIA label for progress indicators
 * @param current - Current value
 * @param max - Maximum value
 * @param label - Label for the progress
 * @returns ARIA label string
 */
export function getProgressLabel(
  current: number,
  max: number,
  label: string,
): string {
  const percentage = Math.round((current / max) * 100);
  return `${label}: ${percentage}% complete`;
}

/**
 * Validates color contrast ratio for WCAG AA compliance
 * @param foreground - Foreground color (hex)
 * @param background - Background color (hex)
 * @returns True if contrast ratio meets WCAG AA (4.5:1)
 */
export function meetsContrastRequirements(
  foreground: string,
  background: string,
): boolean {
  // This is a simplified check - real implementation would calculate luminance
  // For production, use a library like color-contrast-checker

  // Parse hex colors
  const fgRgb = hexToRgb(foreground);
  const bgRgb = hexToRgb(background);

  if (!fgRgb || !bgRgb) return false;

  // Calculate relative luminance (simplified)
  const fgLuminance = relativeLuminance(fgRgb);
  const bgLuminance = relativeLuminance(bgRgb);

  // Calculate contrast ratio
  const contrast =
    (Math.max(fgLuminance, bgLuminance) + 0.05) /
    (Math.min(fgLuminance, bgLuminance) + 0.05);

  // WCAG AA requires 4.5:1 for normal text, 3:1 for large text
  return contrast >= 4.5;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

function relativeLuminance(rgb: { r: number; g: number; b: number }): number {
  const rsRGB = rgb.r / 255;
  const gsRGB = rgb.g / 255;
  const bsRGB = rgb.b / 255;

  const r =
    rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
  const g =
    gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
  const b =
    bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Keyboard event helpers
 */
export const KeyCodes = {
  ENTER: "Enter",
  SPACE: " ",
  ESCAPE: "Escape",
  TAB: "Tab",
  ARROW_UP: "ArrowUp",
  ARROW_DOWN: "ArrowDown",
  ARROW_LEFT: "ArrowLeft",
  ARROW_RIGHT: "ArrowRight",
  HOME: "Home",
  END: "End",
} as const;

/**
 * Check if an element is focusable
 * @param element - Element to check
 * @returns True if focusable
 */
export function isFocusable(element: HTMLElement): boolean {
  if (element.hasAttribute("disabled")) return false;
  if (element.getAttribute("tabindex") === "-1") return false;

  const focusableSelectors = [
    "a[href]",
    "button",
    "input",
    "select",
    "textarea",
    "[tabindex]",
    "audio[controls]",
    "video[controls]",
  ];

  return focusableSelectors.some((selector) => element.matches(selector));
}

/**
 * Get all focusable elements within a container
 * @param container - Container element
 * @returns Array of focusable elements
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

  return Array.from(
    container.querySelectorAll<HTMLElement>(focusableSelectors),
  ).filter((el) => isAccessible(el) && isFocusable(el));
}
