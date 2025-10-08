/**
 * Language Toggle Component
 * Following WET-BOEW (Web Experience Toolkit) pattern for Government of Canada bilingual support
 * Allows users to switch between English and French
 */

"use client";

import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Languages } from "lucide-react";
import { cn } from "@/lib/utils";

interface LanguageToggleProps {
  className?: string;
  variant?: "default" | "ghost" | "link";
  showIcon?: boolean;
}

export function LanguageToggle({
  className,
  variant = "ghost",
  showIcon = false,
}: LanguageToggleProps) {
  const { i18n, t } = useTranslation("common");

  const currentLang = i18n.language || "en";
  const isEnglish = currentLang.startsWith("en");
  const targetLang = isEnglish ? "fr" : "en";
  const targetLabel = isEnglish ? "Français" : "English";

  const handleLanguageToggle = () => {
    i18n.changeLanguage(targetLang);
  };

  return (
    <Button
      variant={variant}
      size="sm"
      onClick={handleLanguageToggle}
      className={cn("gap-2 font-medium transition-colors", className)}
      lang={targetLang}
      aria-label={t("language.switchTo", { language: targetLabel })}
      title={t("language.switchTo", { language: targetLabel })}
    >
      {showIcon && <Languages className="h-4 w-4" />}
      <span className="text-sm">{targetLabel}</span>
    </Button>
  );
}

export default LanguageToggle;
