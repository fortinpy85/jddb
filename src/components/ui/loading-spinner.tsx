"use client";

import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  className?: string;
  variant?: "default" | "overlay" | "inline";
}

const sizeClasses = {
  sm: "w-4 h-4",
  md: "w-6 h-6",
  lg: "w-8 h-8",
};

export function LoadingSpinner({
  size = "md",
  text,
  className = "",
  variant = "default",
}: LoadingSpinnerProps) {
  const spinnerSize = sizeClasses[size];

  if (variant === "overlay") {
    return (
      <div
        className={`fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50 ${className}`}
      >
        <div className="bg-white rounded-lg p-6 shadow-xl flex flex-col items-center space-y-3">
          <Loader2 className={`${spinnerSize} animate-spin text-blue-500`} />
          {text && <p className="text-gray-600 text-sm">{text}</p>}
        </div>
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Loader2 className={`${spinnerSize} animate-spin text-blue-500`} />
        {text && <span className="text-gray-600 text-sm">{text}</span>}
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center justify-center p-8 ${className}`}
    >
      <Loader2 className={`${spinnerSize} animate-spin text-blue-500 mb-3`} />
      {text && <p className="text-gray-600 text-sm text-center">{text}</p>}
    </div>
  );
}

export default LoadingSpinner;
