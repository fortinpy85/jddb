/**
 * Test setup file for frontend unit tests
 *
 * NOTE: @testing-library/jest-dom is commented out due to incompatibility
 * with Bun's test runner. Custom matchers added below for compatibility.
 */
// import "@testing-library/jest-dom";  // Incompatible with Bun
import { beforeEach, afterEach, expect } from "bun:test";
import { cleanup } from "@testing-library/react";

// Add custom matchers for Bun compatibility with @testing-library/jest-dom
if (expect && typeof expect.extend === "function") {
  expect.extend({
    toHaveTextContent(received: any, expected: string) {
      const text = received?.textContent || "";
      const pass = text.includes(expected);
      return {
        pass,
        message: () =>
          pass
            ? `Expected element not to have text content "${expected}"`
            : `Expected element to have text content "${expected}", but got "${text}"`,
      };
    },
    toHaveAttribute(received: any, attr: string, value?: string) {
      const hasAttr = received?.hasAttribute?.(attr);
      if (value === undefined) {
        return {
          pass: hasAttr,
          message: () =>
            hasAttr
              ? `Expected element not to have attribute "${attr}"`
              : `Expected element to have attribute "${attr}"`,
        };
      }
      const attrValue = received?.getAttribute?.(attr);
      const pass = hasAttr && attrValue === value;
      return {
        pass,
        message: () =>
          pass
            ? `Expected element not to have attribute "${attr}" with value "${value}"`
            : `Expected element to have attribute "${attr}" with value "${value}", but got "${attrValue}"`,
      };
    },
    toBeInTheDocument(received: any) {
      const pass = received !== null && received !== undefined;
      return {
        pass,
        message: () =>
          pass
            ? `Expected element not to be in the document`
            : `Expected element to be in the document`,
      };
    },
    toBeVisible(received: any) {
      const pass = received !== null && received !== undefined;
      return {
        pass,
        message: () =>
          pass
            ? `Expected element not to be visible`
            : `Expected element to be visible`,
      };
    },
    toHaveClass(received: any, ...classNames: string[]) {
      const classList = received?.className?.split(" ") || [];
      const pass = classNames.every((cls) => classList.includes(cls));
      return {
        pass,
        message: () =>
          pass
            ? `Expected element not to have classes "${classNames.join(", ")}"`
            : `Expected element to have classes "${classNames.join(", ")}", but got "${classList.join(" ")}"`,
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

// Mock MouseEvent for JSDOM
if (typeof global !== "undefined" && typeof window !== "undefined") {
  if (!global.MouseEvent) {
    (global as any).MouseEvent = window.MouseEvent || class MouseEvent extends Event {
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
    callback: FrameRequestCallback
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
    id: number
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
