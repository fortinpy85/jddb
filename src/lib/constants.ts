/**
 * Application constants and configuration values
 */

// Tab navigation configuration
export const TAB_ORDER = [
  "dashboard",
  "jobs",
  "upload",
  "search",
  "editing",
  "compare",
  "statistics",
] as const;

export type TabType = (typeof TAB_ORDER)[number];

// Tab display names
export const TAB_NAMES: Record<TabType, string> = {
  dashboard: "Dashboard",
  jobs: "Jobs",
  upload: "Upload",
  search: "Search",
  editing: "Editing",
  compare: "Compare",
  statistics: "Statistics",
} as const;

// API configuration
export const API_CONFIG = {
  DEFAULT_TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// UI constants
export const UI_CONFIG = {
  DEBOUNCE_DELAY: 300,
  ANIMATION_DURATION: 200,
  PAGE_SIZE: 20,
} as const;
