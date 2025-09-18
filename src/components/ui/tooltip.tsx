"use client";

import React, { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface TooltipProps {
  content: string;
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
  const [isVisible, setIsVisible] = useState(false);
  const [shouldShow, setShouldShow] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const showTooltip = () => {
    if (disabled) return;
    setShouldShow(true);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delayDuration);
  };

  const hideTooltip = () => {
    setShouldShow(false);
    setIsVisible(false);
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

  const getPositionClasses = () => {
    const baseClasses = "absolute z-50 text-xs px-2 py-1 max-w-xs";

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

  const getArrowClasses = () => {
    const arrowBase = "absolute w-2 h-2 rotate-45";

    switch (side) {
      case "top":
        return cn(arrowBase, "top-full left-1/2 -translate-x-1/2 -mt-1", {
          "left-2 translate-x-0": align === "start",
          "right-2 left-auto translate-x-0": align === "end",
        });
      case "bottom":
        return cn(arrowBase, "bottom-full left-1/2 -translate-x-1/2 -mb-1", {
          "left-2 translate-x-0": align === "start",
          "right-2 left-auto translate-x-0": align === "end",
        });
      case "left":
        return cn(arrowBase, "left-full top-1/2 -translate-y-1/2 -ml-1", {
          "top-2 translate-y-0": align === "start",
          "bottom-2 top-auto translate-y-0": align === "end",
        });
      case "right":
        return cn(arrowBase, "right-full top-1/2 -translate-y-1/2 -mr-1", {
          "top-2 translate-y-0": align === "start",
          "bottom-2 top-auto translate-y-0": align === "end",
        });
      default:
        return arrowBase;
    }
  };

  return (
    <div
      ref={triggerRef}
      className="relative inline-block"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {isVisible && content && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className={cn(
            getPositionClasses(),
            "bg-popover text-popover-foreground border rounded-md shadow-md",
            "animate-scale-in",
            className,
          )}
        >
          {content}
          <div
            className={cn(getArrowClasses(), "bg-popover border-l border-t")}
          />
        </div>
      )}
    </div>
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
