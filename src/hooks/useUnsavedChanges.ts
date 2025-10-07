/**
 * Hook to track unsaved changes and warn user before navigation
 * Addresses Usability Issue #5.1: No Unsaved Changes Warning
 */

"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

interface UseUnsavedChangesOptions {
  hasUnsavedChanges: boolean;
  message?: string;
  onBeforeUnload?: () => void;
  enabled?: boolean;
}

export function useUnsavedChanges({
  hasUnsavedChanges,
  message = "You have unsaved changes. Are you sure you want to leave?",
  onBeforeUnload,
  enabled = true,
}: UseUnsavedChangesOptions) {
  const messageRef = useRef(message);

  // Update message ref when it changes
  useEffect(() => {
    messageRef.current = message;
  }, [message]);

  // Handle browser beforeunload event
  useEffect(() => {
    if (!enabled || !hasUnsavedChanges) {
      return;
    }

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Call optional callback
      onBeforeUnload?.();

      // Show browser's default confirmation dialog
      e.preventDefault();
      e.returnValue = messageRef.current;
      return messageRef.current;
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [hasUnsavedChanges, enabled, onBeforeUnload]);

  // Return a function that can be used to check before navigation
  const confirmNavigation = useCallback(() => {
    if (!enabled || !hasUnsavedChanges) {
      return true;
    }

    return window.confirm(messageRef.current);
  }, [hasUnsavedChanges, enabled]);

  return {
    confirmNavigation,
    hasUnsavedChanges,
  };
}

/**
 * Hook to prevent navigation when there are unsaved changes
 * Works with React Router or custom navigation
 */
export function usePreventNavigation(
  hasUnsavedChanges: boolean,
  message?: string,
) {
  const { confirmNavigation } = useUnsavedChanges({
    hasUnsavedChanges,
    message,
  });

  // Return function to wrap navigation actions
  const wrapNavigation = useCallback(
    (navigateFunction: () => void) => {
      return () => {
        if (confirmNavigation()) {
          navigateFunction();
        }
      };
    },
    [confirmNavigation],
  );

  return {
    wrapNavigation,
    confirmNavigation,
  };
}
