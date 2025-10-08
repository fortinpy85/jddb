/**
 * i18next Configuration for Bilingual Support
 * Supports English and French (Government of Canada requirement)
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// Import translation files
import commonEn from "@/locales/en/common.json";
import jobsEn from "@/locales/en/jobs.json";
import errorsEn from "@/locales/en/errors.json";
import navigationEn from "@/locales/en/navigation.json";
import dashboardEn from "@/locales/en/dashboard.json";

import commonFr from "@/locales/fr/common.json";
import jobsFr from "@/locales/fr/jobs.json";
import errorsFr from "@/locales/fr/errors.json";
import navigationFr from "@/locales/fr/navigation.json";
import dashboardFr from "@/locales/fr/dashboard.json";

// Configure i18next
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        common: commonEn,
        jobs: jobsEn,
        errors: errorsEn,
        navigation: navigationEn,
        dashboard: dashboardEn,
      },
      fr: {
        common: commonFr,
        jobs: jobsFr,
        errors: errorsFr,
        navigation: navigationFr,
        dashboard: dashboardFr,
      },
    },
    fallbackLng: "en",
    defaultNS: "common",
    supportedLngs: ["en", "fr"],
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      // Order of detection methods
      order: ["querystring", "cookie", "localStorage", "navigator", "htmlTag"],
      // Cache language in localStorage
      caches: ["localStorage", "cookie"],
      // Query parameter name
      lookupQuerystring: "lang",
      // Cookie name
      lookupCookie: "jddb_language",
      // LocalStorage key
      lookupLocalStorage: "jddb_language",
    },
    react: {
      useSuspense: true,
    },
  });

export default i18n;
