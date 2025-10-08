"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/ui/theme-provider";
import { Sun, Moon, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export default function ThemeToggle({
  className,
  size = "md",
}: ThemeToggleProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("system");
    } else {
      setTheme("light");
    }
  };

  const getIcon = () => {
    if (theme === "system") {
      return <Monitor className="w-4 h-4" />;
    }
    if (resolvedTheme === "dark") {
      return <Moon className="w-4 h-4" />;
    }
    return <Sun className="w-4 h-4" />;
  };

  const getTitle = () => {
    if (theme === "system") {
      return "Switch to light mode (System theme)";
    }
    if (resolvedTheme === "dark") {
      return "Switch to system mode (Dark mode)";
    }
    return "Switch to dark mode (Light mode)";
  };

  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-9 w-9",
    lg: "h-10 w-10",
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className={cn(
        sizeClasses[size],
        "relative group transition-all duration-200 hover:scale-110 hover:rotate-12",
        "hover:bg-slate-100/80 dark:hover:bg-slate-800/80",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
        "dark:focus:ring-blue-400 dark:focus:ring-offset-slate-800",
        className,
      )}
      title={getTitle()}
      aria-label={getTitle()}
    >
      {/* Animated icon container */}
      <div className="relative flex items-center justify-center">
        {/* Current icon with smooth transition */}
        <div className="transform transition-all duration-300 ease-out group-hover:scale-110">
          {getIcon()}
        </div>

        {/* Glow effect on hover */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500/20 to-indigo-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-sm"></div>
      </div>

      {/* Accessibility */}
      <span className="sr-only">{getTitle()}</span>
    </Button>
  );
}

export function ThemeToggleCompact({ className }: { className?: string }) {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <div
      className={cn(
        "flex items-center gap-1 rounded-lg border p-1 bg-background/80 backdrop-blur-sm",
        className,
      )}
    >
      <Button
        variant={theme === "light" ? "default" : "ghost"}
        size="sm"
        onClick={() => setTheme("light")}
        className="h-7 w-7 p-0"
        title="Light mode"
        aria-label="Light mode"
      >
        <Sun className="h-3.5 w-3.5" />
      </Button>
      <Button
        variant={theme === "dark" ? "default" : "ghost"}
        size="sm"
        onClick={() => setTheme("dark")}
        className="h-7 w-7 p-0"
        title="Dark mode"
        aria-label="Dark mode"
      >
        <Moon className="h-3.5 w-3.5" />
      </Button>
      <Button
        variant={theme === "system" ? "default" : "ghost"}
        size="sm"
        onClick={() => setTheme("system")}
        className="h-7 w-7 p-0"
        title="System theme"
        aria-label="System theme"
      >
        <Monitor className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
