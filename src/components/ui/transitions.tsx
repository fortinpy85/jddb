/**
 * JDDB Page Transitions
 * Smooth transitions between pages and components for enhanced UX
 */

"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

/**
 * Fade Transition Component
 */
interface FadeTransitionProps {
  children: React.ReactNode;
  show: boolean;
  duration?: number;
  className?: string;
}

export function FadeTransition({
  children,
  show,
  duration = 300,
  className,
}: FadeTransitionProps) {
  const [shouldRender, setShouldRender] = useState(show);

  useEffect(() => {
    if (show) {
      setShouldRender(true);
    } else {
      const timeout = setTimeout(() => setShouldRender(false), duration);
      return () => clearTimeout(timeout);
    }
  }, [show, duration]);

  if (!shouldRender) return null;

  return (
    <div
      className={cn(
        "transition-all ease-in-out",
        show ? "opacity-100 scale-100" : "opacity-0 scale-95",
        className,
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

/**
 * Slide Transition Component
 */
interface SlideTransitionProps {
  children: React.ReactNode;
  show: boolean;
  direction?: "left" | "right" | "up" | "down";
  duration?: number;
  className?: string;
}

export function SlideTransition({
  children,
  show,
  direction = "right",
  duration = 300,
  className,
}: SlideTransitionProps) {
  const [shouldRender, setShouldRender] = useState(show);

  useEffect(() => {
    if (show) {
      setShouldRender(true);
    } else {
      const timeout = setTimeout(() => setShouldRender(false), duration);
      return () => clearTimeout(timeout);
    }
  }, [show, duration]);

  const getTransform = () => {
    if (!show) {
      switch (direction) {
        case "left":
          return "translateX(-100%)";
        case "right":
          return "translateX(100%)";
        case "up":
          return "translateY(-100%)";
        case "down":
          return "translateY(100%)";
        default:
          return "translateX(100%)";
      }
    }
    return "translate(0, 0)";
  };

  if (!shouldRender) return null;

  return (
    <div
      className={cn(
        "transition-all ease-in-out",
        show ? "opacity-100" : "opacity-0",
        className,
      )}
      style={{
        transitionDuration: `${duration}ms`,
        transform: getTransform(),
      }}
    >
      {children}
    </div>
  );
}

/**
 * Page Transition Container
 */
interface PageTransitionProps {
  children: React.ReactNode;
  currentPage: string;
  previousPage?: string;
  className?: string;
}

export function PageTransition({
  children,
  currentPage,
  previousPage,
  className,
}: PageTransitionProps) {
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (previousPage && previousPage !== currentPage) {
      setIsTransitioning(true);
      const timeout = setTimeout(() => setIsTransitioning(false), 150);
      return () => clearTimeout(timeout);
    }
  }, [currentPage, previousPage]);

  return (
    <div
      className={cn(
        "transition-all duration-300 ease-in-out",
        isTransitioning ? "opacity-0 scale-98" : "opacity-100 scale-100",
        className,
      )}
    >
      {children}
    </div>
  );
}

/**
 * Stagger Animation Component
 */
interface StaggerAnimationProps {
  children: React.ReactNode[];
  staggerDelay?: number;
  initialDelay?: number;
  className?: string;
}

export function StaggerAnimation({
  children,
  staggerDelay = 100,
  initialDelay = 0,
  className,
}: StaggerAnimationProps) {
  const [visibleItems, setVisibleItems] = useState<number[]>([]);

  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = [];

    children.forEach((_, index) => {
      const timeout = setTimeout(
        () => {
          setVisibleItems((prev) => [...prev, index]);
        },
        initialDelay + index * staggerDelay,
      );
      timeouts.push(timeout);
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [children, staggerDelay, initialDelay]);

  return (
    <div className={className}>
      {children.map((child, index) => (
        <div
          key={index}
          className={cn(
            "transition-all duration-500 ease-out",
            visibleItems.includes(index)
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-4",
          )}
        >
          {child}
        </div>
      ))}
    </div>
  );
}

/**
 * Tab Transition Component
 */
interface TabTransitionProps {
  activeTab: string;
  tabs: Array<{
    id: string;
    content: React.ReactNode;
  }>;
  className?: string;
}

export function TabTransition({
  activeTab,
  tabs,
  className,
}: TabTransitionProps) {
  const [currentContent, setCurrentContent] = useState<React.ReactNode>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const newTab = tabs.find((tab) => tab.id === activeTab);
    if (newTab && newTab.content !== currentContent) {
      setIsTransitioning(true);

      setTimeout(() => {
        setCurrentContent(newTab.content);
        setIsTransitioning(false);
      }, 150);
    }
  }, [activeTab, tabs, currentContent]);

  return (
    <div
      className={cn(
        "transition-all duration-300 ease-in-out min-h-[200px]",
        isTransitioning ? "opacity-0 scale-98" : "opacity-100 scale-100",
        className,
      )}
    >
      {currentContent}
    </div>
  );
}

/**
 * Loading Transition Component
 */
interface LoadingTransitionProps {
  children: React.ReactNode;
  loading: boolean;
  loadingComponent?: React.ReactNode;
  className?: string;
}

export function LoadingTransition({
  children,
  loading,
  loadingComponent,
  className,
}: LoadingTransitionProps) {
  return (
    <div className={cn("relative", className)}>
      <FadeTransition show={!loading}>{children}</FadeTransition>

      <FadeTransition show={loading}>
        <div className="absolute inset-0 flex items-center justify-center">
          {loadingComponent || (
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-slate-600 dark:text-slate-400">
                Loading...
              </span>
            </div>
          )}
        </div>
      </FadeTransition>
    </div>
  );
}

/**
 * Modal Transition Component
 */
interface ModalTransitionProps {
  children: React.ReactNode;
  show: boolean;
  onClose?: () => void;
  className?: string;
}

export function ModalTransition({
  children,
  show,
  onClose,
  className,
}: ModalTransitionProps) {
  const [shouldRender, setShouldRender] = useState(show);

  useEffect(() => {
    if (show) {
      setShouldRender(true);
      document.body.style.overflow = "hidden";
    } else {
      const timeout = setTimeout(() => {
        setShouldRender(false);
        document.body.style.overflow = "unset";
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [show]);

  if (!shouldRender) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className={cn(
          "absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300",
          show ? "opacity-100" : "opacity-0",
        )}
        onClick={onClose}
      />

      {/* Modal Content */}
      <div
        className={cn(
          "relative z-10 transition-all duration-300 ease-out",
          show
            ? "opacity-100 scale-100 translate-y-0"
            : "opacity-0 scale-95 translate-y-4",
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}

/**
 * Hover Transition Component
 */
interface HoverTransitionProps {
  children: React.ReactNode;
  hoverContent?: React.ReactNode;
  className?: string;
  duration?: number;
}

export function HoverTransition({
  children,
  hoverContent,
  className,
  duration = 200,
}: HoverTransitionProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={cn("relative", className)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className="transition-all ease-in-out"
        style={{ transitionDuration: `${duration}ms` }}
      >
        {children}
      </div>

      {hoverContent && (
        <div
          className={cn(
            "absolute inset-0 transition-all ease-in-out",
            isHovered ? "opacity-100" : "opacity-0 pointer-events-none",
          )}
          style={{ transitionDuration: `${duration}ms` }}
        >
          {hoverContent}
        </div>
      )}
    </div>
  );
}

/**
 * Scroll Reveal Component
 */
interface ScrollRevealProps {
  children: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
  className?: string;
}

export function ScrollReveal({
  children,
  threshold = 0.1,
  rootMargin = "0px",
  className,
}: ScrollRevealProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [element, setElement] = useState<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(element);
        }
      },
      { threshold, rootMargin },
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [element, threshold, rootMargin]);

  return (
    <div
      ref={setElement}
      className={cn(
        "transition-all duration-700 ease-out",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8",
        className,
      )}
    >
      {children}
    </div>
  );
}
