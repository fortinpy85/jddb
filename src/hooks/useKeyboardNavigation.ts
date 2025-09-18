"use client";

import { useEffect, useCallback } from "react";

interface KeyboardNavigationOptions {
  onEscape?: () => void;
  onEnter?: () => void;
  onArrowUp?: () => void;
  onArrowDown?: () => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  onTab?: () => void;
  onShiftTab?: () => void;
  onCtrlS?: () => void;
  onCtrlF?: () => void;
  onCtrlK?: () => void;
  disabled?: boolean;
  captureGlobal?: boolean;
}

export function useKeyboardNavigation(options: KeyboardNavigationOptions = {}) {
  const {
    onEscape,
    onEnter,
    onArrowUp,
    onArrowDown,
    onArrowLeft,
    onArrowRight,
    onTab,
    onShiftTab,
    onCtrlS,
    onCtrlF,
    onCtrlK,
    disabled = false,
    captureGlobal = true,
  } = options;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (disabled) return;

      // Don't intercept if user is typing in an input/textarea
      const activeElement = document.activeElement;
      const isTyping =
        activeElement &&
        (activeElement.tagName === "INPUT" ||
          activeElement.tagName === "TEXTAREA" ||
          activeElement.getAttribute("contenteditable") === "true");

      switch (event.key) {
        case "Escape":
          if (onEscape && !isTyping) {
            event.preventDefault();
            onEscape();
          }
          break;

        case "Enter":
          if (onEnter && !isTyping) {
            event.preventDefault();
            onEnter();
          }
          break;

        case "ArrowUp":
          if (onArrowUp && !isTyping) {
            event.preventDefault();
            onArrowUp();
          }
          break;

        case "ArrowDown":
          if (onArrowDown && !isTyping) {
            event.preventDefault();
            onArrowDown();
          }
          break;

        case "ArrowLeft":
          if (onArrowLeft && !isTyping) {
            event.preventDefault();
            onArrowLeft();
          }
          break;

        case "ArrowRight":
          if (onArrowRight && !isTyping) {
            event.preventDefault();
            onArrowRight();
          }
          break;

        case "Tab":
          if (event.shiftKey && onShiftTab) {
            event.preventDefault();
            onShiftTab();
          } else if (onTab && !event.shiftKey) {
            event.preventDefault();
            onTab();
          }
          break;

        case "s":
        case "S":
          if ((event.ctrlKey || event.metaKey) && onCtrlS) {
            event.preventDefault();
            onCtrlS();
          }
          break;

        case "f":
        case "F":
          if ((event.ctrlKey || event.metaKey) && onCtrlF) {
            event.preventDefault();
            onCtrlF();
          }
          break;

        case "k":
        case "K":
          if ((event.ctrlKey || event.metaKey) && onCtrlK) {
            event.preventDefault();
            onCtrlK();
          }
          break;

        default:
          break;
      }
    },
    [
      disabled,
      onEscape,
      onEnter,
      onArrowUp,
      onArrowDown,
      onArrowLeft,
      onArrowRight,
      onTab,
      onShiftTab,
      onCtrlS,
      onCtrlF,
      onCtrlK,
    ],
  );

  useEffect(() => {
    if (captureGlobal) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [handleKeyDown, captureGlobal]);

  return { handleKeyDown };
}

// Predefined keyboard shortcut configurations
export const KEYBOARD_SHORTCUTS = {
  navigation: {
    escape: "Esc - Close modal/go back",
    enter: "Enter - Select/confirm",
    arrows: "Arrow keys - Navigate items",
    tab: "Tab - Move between elements",
  },
  actions: {
    save: "Ctrl/Cmd + S - Save",
    search: "Ctrl/Cmd + F - Search",
    quickAccess: "Ctrl/Cmd + K - Quick access menu",
  },
} as const;

export default useKeyboardNavigation;
