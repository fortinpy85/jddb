/**
 * Keyboard Shortcuts Hook
 * Provides comprehensive keyboard navigation and shortcuts for power users
 */

import { useEffect, useCallback } from "react";

export interface KeyboardShortcut {
  key: string;
  modifiers?: ("ctrl" | "shift" | "alt" | "meta")[];
  description: string;
  action: () => void;
  category: "navigation" | "actions" | "search" | "editing";
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
  preventDefault?: boolean;
}

/**
 * Hook for managing keyboard shortcuts
 */
export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  options: UseKeyboardShortcutsOptions = {},
) {
  const { enabled = true, preventDefault = true } = options;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't trigger shortcuts when user is typing in input fields
      const target = event.target as HTMLElement;
      const isInputElement =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (isInputElement) return;

      const pressedKey = event.key.toLowerCase();
      const hasCtrl = event.ctrlKey || event.metaKey; // Support both Ctrl and Cmd
      const hasShift = event.shiftKey;
      const hasAlt = event.altKey;

      for (const shortcut of shortcuts) {
        if (shortcut.key.toLowerCase() !== pressedKey) continue;

        const requiredModifiers = shortcut.modifiers || [];
        const hasRequiredCtrl =
          requiredModifiers.includes("ctrl") ||
          requiredModifiers.includes("meta");
        const hasRequiredShift = requiredModifiers.includes("shift");
        const hasRequiredAlt = requiredModifiers.includes("alt");

        // Check if all required modifiers match
        if (
          (hasRequiredCtrl ? hasCtrl : !hasCtrl) &&
          (hasRequiredShift ? hasShift : !hasShift) &&
          (hasRequiredAlt ? hasAlt : !hasAlt)
        ) {
          if (preventDefault) {
            event.preventDefault();
          }
          shortcut.action();
          break;
        }
      }
    },
    [shortcuts, enabled, preventDefault],
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, enabled]);

  return {
    shortcuts,
    enabled,
  };
}

/**
 * Common keyboard shortcuts for JDDB application
 */
export function createJDDBShortcuts(handlers: {
  onNavigateToJobs?: () => void;
  onNavigateToUpload?: () => void;
  onNavigateToSearch?: () => void;
  onNavigateToCompare?: () => void;
  onNavigateToStats?: () => void;
  onFocusSearch?: () => void;
  onNewUpload?: () => void;
  onToggleTheme?: () => void;
  onShowShortcuts?: () => void;
}): KeyboardShortcut[] {
  return [
    // Navigation shortcuts
    {
      key: "1",
      modifiers: ["ctrl"],
      description: "Navigate to Dashboard",
      action: handlers.onNavigateToJobs || (() => {}),
      category: "navigation",
    },
    {
      key: "2",
      modifiers: ["ctrl"],
      description: "Navigate to Jobs List",
      action: handlers.onNavigateToJobs || (() => {}),
      category: "navigation",
    },
    {
      key: "3",
      modifiers: ["ctrl"],
      description: "Navigate to Upload",
      action: handlers.onNavigateToUpload || (() => {}),
      category: "navigation",
    },
    {
      key: "4",
      modifiers: ["ctrl"],
      description: "Navigate to Search",
      action: handlers.onNavigateToSearch || (() => {}),
      category: "navigation",
    },
    {
      key: "5",
      modifiers: ["ctrl"],
      description: "Navigate to Compare",
      action: handlers.onNavigateToCompare || (() => {}),
      category: "navigation",
    },
    {
      key: "6",
      modifiers: ["ctrl"],
      description: "Navigate to Statistics",
      action: handlers.onNavigateToStats || (() => {}),
      category: "navigation",
    },

    // Search shortcuts
    {
      key: "/",
      description: "Focus search input",
      action: handlers.onFocusSearch || (() => {}),
      category: "search",
    },
    {
      key: "k",
      modifiers: ["ctrl"],
      description: "Quick search (alternative)",
      action: handlers.onFocusSearch || (() => {}),
      category: "search",
    },

    // Action shortcuts
    {
      key: "n",
      modifiers: ["ctrl"],
      description: "New upload",
      action: handlers.onNewUpload || (() => {}),
      category: "actions",
    },
    {
      key: "t",
      modifiers: ["ctrl", "shift"],
      description: "Toggle theme",
      action: handlers.onToggleTheme || (() => {}),
      category: "actions",
    },

    // Help shortcuts
    {
      key: "?",
      modifiers: ["shift"],
      description: "Show keyboard shortcuts",
      action: handlers.onShowShortcuts || (() => {}),
      category: "navigation",
    },
    {
      key: "h",
      modifiers: ["ctrl"],
      description: "Show help",
      action: handlers.onShowShortcuts || (() => {}),
      category: "navigation",
    },
  ];
}

/**
 * Hook for JDDB-specific keyboard shortcuts
 */
export function useJDDBKeyboardShortcuts(
  handlers: Parameters<typeof createJDDBShortcuts>[0],
) {
  const shortcuts = createJDDBShortcuts(handlers);

  return useKeyboardShortcuts(shortcuts, {
    enabled: true,
    preventDefault: true,
  });
}

/**
 * Utility function to format shortcut for display
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const modifiers = shortcut.modifiers || [];
  const parts: string[] = [];

  // Use appropriate symbols for the platform
  const isMac =
    typeof navigator !== "undefined" &&
    navigator.platform.toUpperCase().indexOf("MAC") >= 0;

  if (modifiers.includes("ctrl") || modifiers.includes("meta")) {
    parts.push(isMac ? "⌘" : "Ctrl");
  }
  if (modifiers.includes("shift")) {
    parts.push(isMac ? "⇧" : "Shift");
  }
  if (modifiers.includes("alt")) {
    parts.push(isMac ? "⌥" : "Alt");
  }

  // Format special keys
  const keyMap: Record<string, string> = {
    " ": "Space",
    arrowup: "↑",
    arrowdown: "↓",
    arrowleft: "←",
    arrowright: "→",
    enter: "↵",
    escape: "Esc",
    tab: "Tab",
    "/": "/",
    "?": "?",
  };

  const formattedKey =
    keyMap[shortcut.key.toLowerCase()] || shortcut.key.toUpperCase();
  parts.push(formattedKey);

  return parts.join(isMac ? "" : "+");
}
