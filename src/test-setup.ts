/**
 * Test setup file for frontend unit tests
 * Configures Vitest with JSDOM and testing-library matchers
 */
import "@testing-library/jest-dom";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Import translation files for testing
import commonEn from "@/locales/en/common.json";
import jobsEn from "@/locales/en/jobs.json";
import errorsEn from "@/locales/en/errors.json";
import navigationEn from "@/locales/en/navigation.json";
import dashboardEn from "@/locales/en/dashboard.json";
import uploadEn from "@/locales/en/upload.json";
import formsEn from "@/locales/en/forms.json";

import commonFr from "@/locales/fr/common.json";
import jobsFr from "@/locales/fr/jobs.json";
import errorsFr from "@/locales/fr/errors.json";
import navigationFr from "@/locales/fr/navigation.json";
import dashboardFr from "@/locales/fr/dashboard.json";
import uploadFr from "@/locales/fr/upload.json";
import formsFr from "@/locales/fr/forms.json";

// Initialize i18next for test environment
i18n.use(initReactI18next).init({
  lng: "en",
  fallbackLng: "en",
  defaultNS: "common",
  supportedLngs: ["en", "fr"],
  resources: {
    en: {
      common: commonEn,
      jobs: jobsEn,
      errors: errorsEn,
      navigation: navigationEn,
      dashboard: dashboardEn,
      upload: uploadEn,
      forms: formsEn,
    },
    fr: {
      common: commonFr,
      jobs: jobsFr,
      errors: errorsFr,
      navigation: navigationFr,
      dashboard: dashboardFr,
      upload: uploadFr,
      forms: formsFr,
    },
  },
  interpolation: {
    escapeValue: false, // React already escapes
  },
  react: {
    useSuspense: false, // Disable suspense in test environment
  },
});

// @testing-library/jest-dom provides all necessary matchers for Vitest
// No custom matchers needed - jest-dom works natively with Vitest

// Mock environment variables for testing
if (typeof global !== "undefined") {
  global.process = global.process || {};
  global.process.env = global.process.env || {};
  global.process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api";
}

// Setup DOM environment
if (typeof window === "undefined") {
  const { JSDOM } = require("jsdom");
  const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
    url: "http://localhost:3000",
    pretendToBeVisual: true,
    resources: "usable",
  });

  // @ts-ignore
  global.window = dom.window;
  // @ts-ignore
  global.document = dom.window.document;
  // @ts-ignore
  global.navigator = dom.window.navigator;
  // @ts-ignore
  global.HTMLElement = dom.window.HTMLElement;
}

// Mock fetch for API calls
if (!global.fetch) {
  global.fetch = (() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(""),
      preconnect: () => Promise.resolve(),
    } as unknown as Response)) as unknown as typeof fetch;
}

// Mock window.matchMedia
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
  });
}

// Mock MouseEvent for JSDOM
if (typeof global !== "undefined" && typeof window !== "undefined") {
  if (!global.MouseEvent) {
    (global as any).MouseEvent =
      window.MouseEvent ||
      class MouseEvent extends Event {
        constructor(type: string, eventInitDict?: MouseEventInit) {
          super(type, eventInitDict);
        }
      };
  }
}

// Mock IntersectionObserver
if (typeof window !== "undefined") {
  const IntersectionObserverMock = class IntersectionObserver {
    root: Element | null = null;
    rootMargin: string = "0px";
    thresholds: ReadonlyArray<number> = [0];

    constructor(
      callback: IntersectionObserverCallback,
      options?: IntersectionObserverInit,
    ) {}

    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords(): IntersectionObserverEntry[] {
      return [];
    }
  } as any;

  // Set on both window and global to ensure availability
  window.IntersectionObserver = IntersectionObserverMock;
  (global as any).IntersectionObserver = IntersectionObserverMock;
}

// Mock ResizeObserver
if (typeof window !== "undefined" && !window.ResizeObserver) {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// Mock requestAnimationFrame and cancelAnimationFrame for animation tests
if (typeof global !== "undefined" && typeof window !== "undefined") {
  let rafId = 0;
  const rafCallbacks = new Map<number, FrameRequestCallback>();

  // Force override to ensure polyfill is always available
  (global as any).requestAnimationFrame = window.requestAnimationFrame = (
    callback: FrameRequestCallback,
  ): number => {
    const id = ++rafId;
    rafCallbacks.set(id, callback);
    // Execute callback asynchronously to simulate browser behavior
    setTimeout(() => {
      const cb = rafCallbacks.get(id);
      if (cb) {
        rafCallbacks.delete(id);
        cb(Date.now());
      }
    }, 16); // ~60fps
    return id;
  };

  (global as any).cancelAnimationFrame = window.cancelAnimationFrame = (
    id: number,
  ): void => {
    rafCallbacks.delete(id);
  };
}

// Cleanup DOM after each test to prevent test pollution
// Note: Using manual document.body.innerHTML = '' instead of cleanup()
// because cleanup() interferes with JSDOM global document
afterEach(() => {
  if (typeof document !== "undefined" && document.body) {
    document.body.innerHTML = "";
  }
});
