/**
 * Simple Dialog Component
 * Basic modal dialog implementation for UI components
 */

"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "./button";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

interface DialogContentProps {
  className?: string;
  children: React.ReactNode;
  "data-testid"?: string;
}

interface DialogHeaderProps {
  children: React.ReactNode;
}

interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}

interface DialogDescriptionProps {
  children: React.ReactNode;
}

interface DialogFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  // Handle Escape key to close modal
  useEffect(() => {
    if (!open) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {/* Modal */}
      <div className="relative">{children}</div>
    </div>
  );
}

export function DialogContent({
  className,
  children,
  "data-testid": testId,
}: DialogContentProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      const dialog = contentRef.current;
      if (!dialog) return;

      const focusableElements = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      const focusableArray = Array.from(focusableElements) as HTMLElement[];
      const firstElement = focusableArray[0];
      const lastElement = focusableArray[focusableArray.length - 1];

      if (e.shiftKey) {
        // Shift + Tab: going backwards
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab: going forwards
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div
      ref={contentRef}
      className={cn(
        "relative bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6",
        className,
      )}
      data-testid={testId}
      role="dialog"
      aria-modal="true"
    >
      {children}
    </div>
  );
}

export function DialogHeader({ children }: DialogHeaderProps) {
  return <div className="mb-4">{children}</div>;
}

export function DialogTitle({ children, className }: DialogTitleProps) {
  return (
    <h2
      className={cn(
        "text-lg font-semibold text-gray-900 dark:text-gray-100",
        className,
      )}
    >
      {children}
    </h2>
  );
}

export function DialogDescription({ children }: DialogDescriptionProps) {
  return (
    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{children}</p>
  );
}

export function DialogFooter({ children, className }: DialogFooterProps) {
  return (
    <div
      className={cn(
        "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-6",
        className,
      )}
    >
      {children}
    </div>
  );
}
