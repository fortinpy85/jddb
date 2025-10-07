import {
  jest,
  describe,
  beforeEach,
  it,
  expect,
  afterEach,
} from "@jest/globals";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ErrorBoundary } from "./error-boundary";

// A component that throws an error
const ErrorComponent = () => {
  throw new Error("Test Error");
};

describe("ErrorBoundary", () => {
  // Suppress console.error output from jsdom
  beforeEach(() => {
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
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
    const onError = jest.fn();
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
    expect(screen.getByText(/Test Error/)).toBeInTheDocument();
  });

  it("resets the error state when resetKeys prop changes", () => {
    const { rerender } = render(
      <ErrorBoundary resetKeys={["key1"]}>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Oops! Something went wrong")).toBeInTheDocument();

    rerender(
      <ErrorBoundary resetKeys={["key2"]}>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    expect(
      screen.queryByText("Oops! Something went wrong"),
    ).not.toBeInTheDocument();
  });

  it("calls handleRetry, handleReload, and handleGoHome", () => {
    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    const retryButton = screen.getByRole("button", { name: "Try Again" });
    const reloadButton = screen.getByRole("button", { name: "Reload Page" });
    const goHomeButton = screen.getByRole("button", { name: "Go Home" });

    // Mock window.location.reload and window.location.href
    const reload = jest.fn();
    const goHome = jest.fn();
    Object.defineProperty(window, "location", {
      value: {
        reload,
        href: "",
      },
      writable: true,
    });
    window.location.reload = reload;
    window.location.href = "/home";

    fireEvent.click(retryButton);
    expect(
      screen.queryByText("Oops! Something went wrong"),
    ).not.toBeInTheDocument();

    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>,
    );

    fireEvent.click(reloadButton);
    expect(reload).toHaveBeenCalledTimes(1);

    fireEvent.click(goHomeButton);
    expect(window.location.href).toBe("/");
  });
});
