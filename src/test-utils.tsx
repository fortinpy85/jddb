/**
 * Test utilities for React component testing
 */
import React from "react";
import { render, RenderOptions } from "@testing-library/react";
import { ToastProvider } from "@/components/ui/toast";

/**
 * Custom render function that includes ToastProvider
 */
function customRender(
  ui: React.ReactElement,
  options: Omit<RenderOptions, "wrapper"> = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <ToastProvider>{children}</ToastProvider>;
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Test wrapper component that provides all necessary contexts
 */
export function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>;
}

// Re-export everything from testing-library/react
export * from "@testing-library/react";

// Override render method
export { customRender as render };