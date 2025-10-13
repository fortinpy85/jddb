/**
 * useVersionHistory Hook
 *
 * Manages version history for undo/redo functionality in the improvement workflow.
 * Tracks state changes and provides navigation through history.
 */

import { useState, useCallback, useRef, useEffect } from "react";

export interface VersionState {
  acceptedChangeIds: string[];
  rejectedChangeIds: string[];
  timestamp: number;
  description: string;
}

export interface UseVersionHistoryReturn {
  // Current state
  currentVersion: VersionState;
  currentIndex: number;

  // History navigation
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;

  // State management
  pushVersion: (state: Omit<VersionState, "timestamp">) => void;
  clearHistory: () => void;

  // History data
  history: VersionState[];

  // Keyboard shortcut handler
  handleKeyDown: (e: KeyboardEvent) => void;
}

interface UseVersionHistoryOptions {
  maxHistorySize?: number;
  onStateChange?: (state: VersionState) => void;
}

/**
 * Hook for managing version history with undo/redo
 */
export function useVersionHistory(
  initialState: Omit<VersionState, "timestamp">,
  options: UseVersionHistoryOptions = {},
): UseVersionHistoryReturn {
  const { maxHistorySize = 50, onStateChange } = options;

  const [history, setHistory] = useState<VersionState[]>([
    { ...initialState, timestamp: Date.now() },
  ]);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Ref to track if we're in the middle of an undo/redo operation
  const isNavigatingRef = useRef(false);

  const currentVersion = history[currentIndex];
  const canUndo = currentIndex > 0;
  const canRedo = currentIndex < history.length - 1;

  // Push new version to history
  const pushVersion = useCallback(
    (state: Omit<VersionState, "timestamp">) => {
      // Don't push if we're navigating through history
      if (isNavigatingRef.current) return;

      setHistory((prev) => {
        // Remove any "future" versions if we're not at the end
        // This is standard undo/redo behavior: when you undo and then make a new change,
        // the "redo" branch is discarded
        const newHistory = prev.slice(0, currentIndex + 1);

        // Add new version
        const newVersion: VersionState = {
          ...state,
          timestamp: Date.now(),
        };

        newHistory.push(newVersion);

        // Limit history size by keeping only the most recent entries
        if (newHistory.length > maxHistorySize) {
          const trimmed = newHistory.slice(-maxHistorySize);
          // Update currentIndex to account for trimmed history
          setCurrentIndex(trimmed.length - 1);
          return trimmed;
        }

        // Update currentIndex to point to the newly added version
        setCurrentIndex(newHistory.length - 1);
        return newHistory;
      });
    },
    [currentIndex, maxHistorySize],
  );

  // Undo to previous version
  const undo = useCallback(() => {
    if (!canUndo) return;

    isNavigatingRef.current = true;
    const newIndex = currentIndex - 1;
    setCurrentIndex(newIndex);
    onStateChange?.(history[newIndex]);

    // Reset navigation flag after state update
    setTimeout(() => {
      isNavigatingRef.current = false;
    }, 0);
  }, [canUndo, currentIndex, history, onStateChange]);

  // Redo to next version
  const redo = useCallback(() => {
    if (!canRedo) return;

    isNavigatingRef.current = true;
    const newIndex = currentIndex + 1;
    setCurrentIndex(newIndex);
    onStateChange?.(history[newIndex]);

    // Reset navigation flag after state update
    setTimeout(() => {
      isNavigatingRef.current = false;
    }, 0);
  }, [canRedo, currentIndex, history, onStateChange]);

  // Clear all history
  const clearHistory = useCallback(() => {
    const resetState: VersionState = {
      acceptedChangeIds: [],
      rejectedChangeIds: [],
      description: "Initial state",
      timestamp: Date.now(),
    };
    setHistory([resetState]);
    setCurrentIndex(0);
    onStateChange?.(resetState);
  }, [onStateChange]);

  // Keyboard shortcut handler
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Check for Ctrl+Z (Windows/Linux) or Cmd+Z (Mac)
      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        undo();
      }
      // Check for Ctrl+Shift+Z or Ctrl+Y (Windows/Linux) or Cmd+Shift+Z (Mac)
      else if (
        ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "z") ||
        (e.ctrlKey && e.key === "y")
      ) {
        e.preventDefault();
        redo();
      }
    },
    [undo, redo],
  );

  return {
    currentVersion,
    currentIndex,
    canUndo,
    canRedo,
    undo,
    redo,
    pushVersion,
    clearHistory,
    history,
    handleKeyDown,
  };
}
