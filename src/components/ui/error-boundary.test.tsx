import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ErrorBoundary } from "./error-boundary";

// A component that throws an error
const ErrorComponent = () => {
  throw new Error("Test Error");
};

describe("ErrorBoundary", () => {
  let consoleErrorSpy: any;

  // Suppress console.error output
  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy?.mockRestore();
  });

  it("renders children when there is no error", () => {
    render(
      <ErrorBoundary>
        <div>Test Children</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Test Children")).toBeInTheDocument();
  });

  it("catches an error and renders the default error UI", () => {
    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Oops! Something went wrong")).toBeInTheDocument();
  });

  it("renders a custom fallback UI", () => {
    render(
      <ErrorBoundary fallback={<div>Custom Fallback</div>}>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Custom Fallback")).toBeInTheDocument();
  });

  it("calls onError callback when an error is caught", () => {
    const onError = vi.fn(() => {});
    render(
      <ErrorBoundary onError={onError}>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(onError).toHaveBeenCalledTimes(1);
  });

  it("shows/hides error details", () => {
    render(
      <ErrorBoundary showDetails={true}>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Technical Details")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Technical Details"));
    expect(screen.getAllByText(/Test Error/)[0]).toBeInTheDocument();
  });

  it("resets the error state when resetKeys prop changes", () => {
    const { rerender } = render(
      <ErrorBoundary resetKeys={["key1"]}>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Oops! Something went wrong")).toBeInTheDocument();

    // When resetKeys change, error resets but children component needs to NOT throw
    rerender(
      <ErrorBoundary resetKeys={["key2"]}>
        <div>Recovered Children</div>
      </ErrorBoundary>,
    );

    expect(screen.queryByText("Oops! Something went wrong")).toBeNull();
    expect(screen.getByText("Recovered Children")).toBeInTheDocument();
  });

  it("calls handleRetry, handleReload, and handleGoHome", () => {
    // Mock window.location.reload and window.location.href
    const reload = vi.fn(() => {});
    Object.defineProperty(window, "location", {
      value: {
        reload,
        href: "/home",
      },
      writable: true,
    });

    // Test handleRetry - clicking Try Again should reset error boundary
    let shouldThrow = true;
    const ConditionalErrorComponent = () => {
      if (shouldThrow) {
        throw new Error("Test Error");
      }
      return <div>Recovered Content</div>;
    };

    const { rerender } = render(
      <ErrorBoundary>
        <ConditionalErrorComponent />
      </ErrorBoundary>,
    );

    const retryButton = screen.getByRole("button", { name: "Try Again" });

    // Stop throwing and click retry
    shouldThrow = false;
    fireEvent.click(retryButton);

    // Force re-render to trigger the recovered component
    rerender(
      <ErrorBoundary>
        <ConditionalErrorComponent />
      </ErrorBoundary>,
    );

    expect(screen.queryByText("Oops! Something went wrong")).toBeNull();
    expect(screen.getByText("Recovered Content")).toBeInTheDocument();

    // Test handleReload - clicking Reload Page should call window.location.reload
    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    const reloadButton = screen.getByRole("button", { name: "Reload Page" });
    fireEvent.click(reloadButton);
    expect(reload).toHaveBeenCalledTimes(1);

    // Test handleGoHome - clicking Go Home should navigate to "/"
    const goHomeButton = screen.getByRole("button", { name: "Go Home" });
    fireEvent.click(goHomeButton);
    expect(window.location.href).toBe("/");
  });
});
