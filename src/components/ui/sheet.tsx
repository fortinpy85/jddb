/**
 * Sheet Component
 * Slide-in panel for mobile navigation and side content
 */

"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "./button";

interface SheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

interface SheetTriggerProps {
  asChild?: boolean;
  children: React.ReactNode;
}

interface SheetContentProps {
  className?: string;
  children: React.ReactNode;
  side?: "left" | "right" | "top" | "bottom";
  "data-testid"?: string;
}

interface SheetHeaderProps {
  children: React.ReactNode;
}

interface SheetTitleProps {
  children: React.ReactNode;
  className?: string;
}

interface SheetDescriptionProps {
  children: React.ReactNode;
}

const SheetContext = React.createContext<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
}>({
  open: false,
  onOpenChange: () => {},
});

export function Sheet({ open, onOpenChange, children }: SheetProps) {
  return (
    <SheetContext.Provider value={{ open, onOpenChange }}>
      {children}
    </SheetContext.Provider>
  );
}

export function SheetTrigger({ asChild, children }: SheetTriggerProps) {
  const { onOpenChange } = React.useContext(SheetContext);

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      onClick: (e: any) => {
        children.props.onClick?.(e);
        onOpenChange(true);
      },
    } as any);
  }

  return (
    <button onClick={() => onOpenChange(true)} type="button">
      {children}
    </button>
  );
}

export function SheetContent({
  className,
  children,
  side = "right",
  "data-testid": testId,
}: SheetContentProps) {
  const { open, onOpenChange } = React.useContext(SheetContext);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onOpenChange(false);
      }

      if (e.key !== "Tab") return;

      const panel = contentRef.current;
      if (!panel) return;

      const focusableElements = panel.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      const focusableArray = Array.from(focusableElements) as HTMLElement[];
      const firstElement = focusableArray[0];
      const lastElement = focusableArray[focusableArray.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  // Prevent body scroll when sheet is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  const sideClasses = {
    left: "left-0 top-0 bottom-0 animate-slide-in-from-left",
    right: "right-0 top-0 bottom-0 animate-slide-in-from-right",
    top: "top-0 left-0 right-0 animate-slide-in-from-top",
    bottom: "bottom-0 left-0 right-0 animate-slide-in-from-bottom",
  };

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        onClick={() => onOpenChange(false)}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        ref={contentRef}
        className={cn(
          "fixed bg-white dark:bg-slate-900 shadow-xl",
          "overflow-y-auto",
          sideClasses[side],
          className,
        )}
        data-testid={testId}
        role="dialog"
        aria-modal="true"
      >
        {/* Close button */}
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
          onClick={() => onOpenChange(false)}
          aria-label="Close menu"
        >
          <X className="h-4 w-4" />
        </Button>

        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

export function SheetHeader({ children }: SheetHeaderProps) {
  return <div className="mb-6">{children}</div>;
}

export function SheetTitle({ children, className }: SheetTitleProps) {
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

export function SheetDescription({ children }: SheetDescriptionProps) {
  return (
    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{children}</p>
  );
}
