/**
 * Language Sync Component
 * Synchronizes the HTML lang attribute with the current i18n language
 * Ensures WCAG 2.0 compliance by keeping lang attribute updated
 */

"use client";

import { useEffect } from "react";
import { useTranslation } from "react-i18next";

export function LanguageSync() {
  const { i18n } = useTranslation();

  useEffect(() => {
    // Update HTML lang attribute whenever language changes
    const updateHtmlLang = () => {
      const currentLang = i18n.language || "en";
      const langCode = currentLang.startsWith("en") ? "en" : "fr";
      document.documentElement.lang = langCode;
    };

    // Set initial language
    updateHtmlLang();

    // Listen for language changes
    i18n.on("languageChanged", updateHtmlLang);

    // Cleanup
    return () => {
      i18n.off("languageChanged", updateHtmlLang);
    };
  }, [i18n]);

  return null; // This component doesn't render anything
}

export default LanguageSync;
