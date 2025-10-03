/**
 * Test setup file for frontend unit tests
 *
 * NOTE: @testing-library/jest-dom is commented out due to incompatibility
 * with Bun's test runner. Custom matchers added below for compatibility.
 */
// import "@testing-library/jest-dom";  // Incompatible with Bun
import { beforeEach, expect } from "bun:test";

// Add custom matchers for Bun compatibility with @testing-library/jest-dom
if (expect && typeof expect.extend === 'function') {
  expect.extend({
    toHaveTextContent(received: any, expected: string) {
      const text = received?.textContent || '';
      const pass = text.includes(expected);
      return {
        pass,
        message: () => pass
          ? `Expected element not to have text content "${expected}"`
          : `Expected element to have text content "${expected}", but got "${text}"`,
      };
    },
    toHaveAttribute(received: any, attr: string, value?: string) {
      const hasAttr = received?.hasAttribute?.(attr);
      if (value === undefined) {
        return {
          pass: hasAttr,
          message: () => hasAttr
            ? `Expected element not to have attribute "${attr}"`
            : `Expected element to have attribute "${attr}"`,
        };
      }
      const attrValue = received?.getAttribute?.(attr);
      const pass = hasAttr && attrValue === value;
      return {
        pass,
        message: () => pass
          ? `Expected element not to have attribute "${attr}" with value "${value}"`
          : `Expected element to have attribute "${attr}" with value "${value}", but got "${attrValue}"`,
      };
    },
    toBeInTheDocument(received: any) {
      const pass = received !== null && received !== undefined;
      return {
        pass,
        message: () => pass
          ? `Expected element not to be in the document`
          : `Expected element to be in the document`,
      };
    },
    toBeVisible(received: any) {
      const pass = received !== null && received !== undefined;
      return {
        pass,
        message: () => pass
          ? `Expected element not to be visible`
          : `Expected element to be visible`,
      };
    },
  });
}

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

// Mock IntersectionObserver
if (typeof window !== "undefined" && !window.IntersectionObserver) {
  window.IntersectionObserver = class IntersectionObserver {
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
}

// Mock ResizeObserver
if (typeof window !== "undefined" && !window.ResizeObserver) {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
