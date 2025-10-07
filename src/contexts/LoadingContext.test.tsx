import { describe, it, expect } from "bun:test";
import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import React from "react";
import {
  LoadingProvider,
  useLoadingContext,
  useLoadingMessage,
} from "./LoadingContext";

// Test component that uses LoadingContext
function TestComponent() {
  const { context, getMessage, setContext } = useLoadingContext();

  return (
    <div>
      <div data-testid="context">{context}</div>
      <div data-testid="title">{getMessage().title}</div>
      <div data-testid="description">{getMessage().description}</div>
      <button onClick={() => setContext("jobs")}>Set Jobs</button>
      <button onClick={() => setContext("search")}>Set Search</button>
      <button onClick={() => setContext("dashboard")}>Set Dashboard</button>
    </div>
  );
}

// Test component that uses custom messages
function TestCustomMessageComponent() {
  const { getMessage, setCustomMessage, clearCustomMessage } =
    useLoadingContext();

  return (
    <div>
      <div data-testid="title">{getMessage().title}</div>
      <div data-testid="description">{getMessage().description}</div>
      <button
        onClick={() => setCustomMessage("Custom Title", "Custom Description")}
      >
        Set Custom
      </button>
      <button onClick={() => setCustomMessage("Only Title")}>
        Set Custom Title Only
      </button>
      <button onClick={() => clearCustomMessage()}>Clear Custom</button>
    </div>
  );
}

// Test component that uses the useLoadingMessage hook
function TestLoadingMessageComponent() {
  const {
    getMessage,
    setJobsLoading,
    setSearchLoading,
    setComparisonLoading,
    setUploadLoading,
    setJobDetailsLoading,
    setStatsLoading,
    setProcessingLoading,
    setDashboardLoading,
  } = useLoadingMessage();

  return (
    <div>
      <div data-testid="title">{getMessage().title}</div>
      <div data-testid="description">{getMessage().description}</div>
      <button onClick={setJobsLoading}>Jobs</button>
      <button onClick={setSearchLoading}>Search</button>
      <button onClick={setComparisonLoading}>Comparison</button>
      <button onClick={setUploadLoading}>Upload</button>
      <button onClick={setJobDetailsLoading}>Job Details</button>
      <button onClick={setStatsLoading}>Stats</button>
      <button onClick={setProcessingLoading}>Processing</button>
      <button onClick={setDashboardLoading}>Dashboard</button>
    </div>
  );
}

describe("LoadingContext", () => {
  describe("LoadingProvider", () => {
    it("provides default context as generic", () => {
      render(
        <LoadingProvider>
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("context")).toHaveTextContent("generic");
      expect(screen.getByTestId("title")).toHaveTextContent("Loading JDDB");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Preparing your job description database...",
      );
    });

    it("accepts initial context prop", () => {
      render(
        <LoadingProvider initialContext="jobs">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("context")).toHaveTextContent("jobs");
      expect(screen.getByTestId("title")).toHaveTextContent("Loading Jobs");
    });

    it("allows changing context", () => {
      render(
        <LoadingProvider>
          <TestComponent />
        </LoadingProvider>,
      );

      const button = screen.getByText("Set Jobs");
      act(() => {
        button.click();
      });

      expect(screen.getByTestId("context")).toHaveTextContent("jobs");
      expect(screen.getByTestId("title")).toHaveTextContent("Loading Jobs");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Fetching job descriptions from database...",
      );
    });

    it("updates messages for different contexts", () => {
      render(
        <LoadingProvider>
          <TestComponent />
        </LoadingProvider>,
      );

      // Test Search context
      act(() => {
        screen.getByText("Set Search").click();
      });
      expect(screen.getByTestId("title")).toHaveTextContent("Searching");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Finding matching job descriptions...",
      );

      // Test Dashboard context
      act(() => {
        screen.getByText("Set Dashboard").click();
      });
      expect(screen.getByTestId("title")).toHaveTextContent(
        "Loading Dashboard",
      );
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Preparing your job description overview...",
      );
    });
  });

  describe("custom messages", () => {
    it("allows setting custom message with title and description", () => {
      render(
        <LoadingProvider>
          <TestCustomMessageComponent />
        </LoadingProvider>,
      );

      act(() => {
        screen.getByText("Set Custom").click();
      });

      expect(screen.getByTestId("title")).toHaveTextContent("Custom Title");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Custom Description",
      );
    });

    it("uses default description when only title is provided", () => {
      render(
        <LoadingProvider>
          <TestCustomMessageComponent />
        </LoadingProvider>,
      );

      act(() => {
        screen.getByText("Set Custom Title Only").click();
      });

      expect(screen.getByTestId("title")).toHaveTextContent("Only Title");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Please wait while we complete this operation...",
      );
    });

    it("can clear custom message and return to context message", () => {
      render(
        <LoadingProvider initialContext="jobs">
          <TestCustomMessageComponent />
        </LoadingProvider>,
      );

      // Set custom message
      act(() => {
        screen.getByText("Set Custom").click();
      });
      expect(screen.getByTestId("title")).toHaveTextContent("Custom Title");

      // Clear custom message
      act(() => {
        screen.getByText("Clear Custom").click();
      });
      expect(screen.getByTestId("title")).toHaveTextContent("Loading Jobs");
    });
  });

  describe("useLoadingMessage hook", () => {
    it("provides all context setters", () => {
      render(
        <LoadingProvider>
          <TestLoadingMessageComponent />
        </LoadingProvider>,
      );

      // Test each context setter
      const contexts = [
        { button: "Jobs", title: "Loading Jobs" },
        { button: "Search", title: "Searching" },
        { button: "Comparison", title: "Analyzing Jobs" },
        { button: "Upload", title: "Processing Upload" },
        { button: "Job Details", title: "Loading Details" },
        { button: "Stats", title: "Loading Statistics" },
        { button: "Processing", title: "Processing" },
        { button: "Dashboard", title: "Loading Dashboard" },
      ];

      contexts.forEach(({ button, title }) => {
        act(() => {
          screen.getByText(button).click();
        });
        expect(screen.getByTestId("title")).toHaveTextContent(title);
      });
    });
  });

  describe("useLoadingContext hook", () => {
    it("throws error when used outside LoadingProvider", () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = () => {};

      function ComponentWithoutProvider() {
        try {
          useLoadingContext();
          return <div>No error</div>;
        } catch (error) {
          return (
            <div data-testid="error">
              {error instanceof Error ? error.message : "Unknown error"}
            </div>
          );
        }
      }

      render(<ComponentWithoutProvider />);

      expect(screen.getByTestId("error")).toHaveTextContent(
        "useLoadingContext must be used within a LoadingProvider",
      );

      // Restore console.error
      console.error = originalError;
    });
  });

  describe("all loading contexts", () => {
    it("dashboard context has correct message", () => {
      render(
        <LoadingProvider initialContext="dashboard">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("title")).toHaveTextContent(
        "Loading Dashboard",
      );
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Preparing your job description overview...",
      );
    });

    it("comparison context has correct message", () => {
      render(
        <LoadingProvider initialContext="comparison">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("title")).toHaveTextContent("Analyzing Jobs");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Comparing job descriptions and requirements...",
      );
    });

    it("upload context has correct message", () => {
      render(
        <LoadingProvider initialContext="upload">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("title")).toHaveTextContent(
        "Processing Upload",
      );
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Analyzing and extracting job description content...",
      );
    });

    it("job-details context has correct message", () => {
      render(
        <LoadingProvider initialContext="job-details">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("title")).toHaveTextContent("Loading Details");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Retrieving job description and sections...",
      );
    });

    it("stats context has correct message", () => {
      render(
        <LoadingProvider initialContext="stats">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("title")).toHaveTextContent(
        "Loading Statistics",
      );
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Calculating database metrics and insights...",
      );
    });

    it("processing context has correct message", () => {
      render(
        <LoadingProvider initialContext="processing">
          <TestComponent />
        </LoadingProvider>,
      );

      expect(screen.getByTestId("title")).toHaveTextContent("Processing");
      expect(screen.getByTestId("description")).toHaveTextContent(
        "Analyzing content and extracting information...",
      );
    });
  });
});
