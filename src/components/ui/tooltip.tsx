"use client";

import React, {
  useState,
  useRef,
  useEffect,
  createContext,
  useContext,
} from "react";
import { cn } from "@/lib/utils";

// Context for tooltip state (for Radix UI-style API compatibility)
const TooltipContext = createContext<{
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  delayDuration: number;
}>({
  isOpen: false,
  setIsOpen: () => {},
  delayDuration: 700,
});

// TooltipProvider - Provides context for nested components
export function TooltipProvider({
  children,
  delayDuration = 700,
}: {
  children: React.ReactNode;
  delayDuration?: number;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <TooltipContext.Provider value={{ isOpen, setIsOpen, delayDuration }}>
      {children}
    </TooltipContext.Provider>
  );
}

// TooltipTrigger - The element that triggers the tooltip
export const TooltipTrigger = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { asChild?: boolean }
>(({ children, asChild, ...props }, ref) => {
  const { setIsOpen, delayDuration } = useContext(TooltipContext);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      setIsOpen(true);
    }, delayDuration);
  };

  const hideTooltip = () => {
    setIsOpen(false);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      ...props,
      ref,
      onMouseEnter: (e: React.MouseEvent) => {
        showTooltip();
        (children as any).props?.onMouseEnter?.(e);
      },
      onMouseLeave: (e: React.MouseEvent) => {
        hideTooltip();
        (children as any).props?.onMouseLeave?.(e);
      },
      onFocus: (e: React.FocusEvent) => {
        showTooltip();
        (children as any).props?.onFocus?.(e);
      },
      onBlur: (e: React.FocusEvent) => {
        hideTooltip();
        (children as any).props?.onBlur?.(e);
      },
    });
  }

  return (
    <div
      ref={ref}
      {...props}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
    </div>
  );
});
TooltipTrigger.displayName = "TooltipTrigger";

// TooltipContent - The tooltip content that appears
export const TooltipContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    side?: "top" | "bottom" | "left" | "right";
    align?: "start" | "center" | "end";
  }
>(({ children, className, side = "top", align = "center", ...props }, ref) => {
  const { isOpen } = useContext(TooltipContext);

  const getPositionClasses = () => {
    const baseClasses = "absolute z-50 text-sm px-3 py-1.5";

    switch (side) {
      case "top":
        return cn(baseClasses, "bottom-full left-1/2 -translate-x-1/2 mb-2", {
          "left-0 translate-x-0": align === "start",
          "right-0 left-auto translate-x-0": align === "end",
        });
      case "bottom":
        return cn(baseClasses, "top-full left-1/2 -translate-x-1/2 mt-2", {
          "left-0 translate-x-0": align === "start",
          "right-0 left-auto translate-x-0": align === "end",
        });
      case "left":
        return cn(baseClasses, "right-full top-1/2 -translate-y-1/2 mr-2", {
          "top-0 translate-y-0": align === "start",
          "bottom-0 top-auto translate-y-0": align === "end",
        });
      case "right":
        return cn(baseClasses, "left-full top-1/2 -translate-y-1/2 ml-2", {
          "top-0 translate-y-0": align === "start",
          "bottom-0 top-auto translate-y-0": align === "end",
        });
      default:
        return baseClasses;
    }
  };

  if (!isOpen) return null;

  return (
    <div
      ref={ref}
      role="tooltip"
      className={cn(
        getPositionClasses(),
        "bg-popover text-popover-foreground border rounded-md shadow-md",
        "animate-scale-in",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
});
TooltipContent.displayName = "TooltipContent";

// Original Tooltip component (for backwards compatibility)
interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  delayDuration?: number;
  disabled?: boolean;
  className?: string;
}

export function Tooltip({
  content,
  children,
  side = "top",
  align = "center",
  delayDuration = 700,
  disabled = false,
  className = "",
}: TooltipProps) {
  return (
    <TooltipProvider delayDuration={delayDuration}>
      <div className="relative inline-block">
        <TooltipTrigger>{children}</TooltipTrigger>
        {!disabled && (
          <TooltipContent side={side} align={align} className={className}>
            {content}
          </TooltipContent>
        )}
      </div>
    </TooltipProvider>
  );
}

// Simple wrapper for easier usage
interface TooltipWrapperProps {
  tooltip: string;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function TooltipWrapper({
  tooltip,
  children,
  side = "top",
  className,
}: TooltipWrapperProps) {
  return (
    <Tooltip content={tooltip} side={side} className={className}>
      {children}
    </Tooltip>
  );
}

export default Tooltip;
