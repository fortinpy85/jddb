"use client";

import React, { useEffect, useState } from "react";

interface AnimatedCounterProps {
  end: number;
  start?: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  delay?: number;
}

export function AnimatedCounter({
  end,
  start = 0,
  duration = 2000,
  decimals = 0,
  prefix = "",
  suffix = "",
  className = "",
  delay = 0,
}: AnimatedCounterProps) {
  const [count, setCount] = useState(start);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setHasStarted(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  useEffect(() => {
    if (!hasStarted) return;

    let startTime: number | null = null;
    let animationFrame: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);

      // Easing function for smooth animation (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3);

      const currentCount = start + (end - start) * easeOut;
      setCount(currentCount);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      } else {
        setCount(end);
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [start, end, duration, hasStarted]);

  const formatNumber = (num: number) => {
    return prefix + num.toFixed(decimals) + suffix;
  };

  return (
    <span className={`tabular-nums ${className}`} data-testid="animated-counter">
      {formatNumber(count)}
    </span>
  );
}

export default AnimatedCounter;
