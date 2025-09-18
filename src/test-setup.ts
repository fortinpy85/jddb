/**
 * Test setup file for frontend unit tests
 */
import "@testing-library/jest-dom";
import { beforeEach } from "bun:test";

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
    } as Response)) as typeof fetch;
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

    constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {}

    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords(): IntersectionObserverEntry[] { return []; }
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
