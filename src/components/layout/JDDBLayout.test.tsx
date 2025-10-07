import { jest, describe, beforeEach, it, expect } from "@jest/globals";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { JDDBLayout } from "./JDDBLayout";
import { useStore } from "@/lib/store";
import { useLoadingContext } from "@/contexts/LoadingContext";

// Mock the custom hooks
jest.mock("@/lib/store", () => ({
  useStore: jest.fn(),
}));
jest.mock("@/contexts/LoadingContext", () => ({
  useLoadingContext: jest.fn(),
}));

const mockUseStore = useStore as jest.Mock;
const mockUseLoadingContext = useLoadingContext as jest.Mock;

describe("JDDBLayout", () => {
  beforeEach(() => {
    mockUseStore.mockReturnValue({
      stats: { total_jobs: 10, last_updated: new Date().toISOString() },
      loading: false,
    });
    mockUseLoadingContext.mockReturnValue({
      loading: false,
      getMessage: () => ({ title: "Loading...", description: "Please wait." }),
    });
  });

  it("renders the layout with children", () => {
    render(
      <JDDBLayout>
        <div>Test Children</div>
      </JDDBLayout>,
    );

    expect(screen.getByTestId("jddb-layout")).toBeInTheDocument();
    expect(screen.getByText("Test Children")).toBeInTheDocument();
  });

  it("renders the header with title and subtitle", () => {
    render(<JDDBLayout title="Test Title" subtitle="Test Subtitle" />);

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test Subtitle")).toBeInTheDocument();
  });

  it("shows the back button and handles onBack event", () => {
    const onBack = jest.fn();
    render(<JDDBLayout showBackButton onBack={onBack} />);

    const backButton = screen.getByRole("button", { name: /back/i });
    expect(backButton).toBeInTheDocument();
    fireEvent.click(backButton);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders the navigation tabs and handles tab change", () => {
    const onTabChange = jest.fn();
    render(<JDDBLayout activeTab="dashboard" onTabChange={onTabChange} />);

    const dashboardTab = screen.getByTestId("active-tab");
    expect(dashboardTab).toHaveTextContent("Dashboard");

    const jobsTab = screen.getByTestId("tab-jobs");
    fireEvent.click(jobsTab);
    expect(onTabChange).toHaveBeenCalledWith("jobs");
  });

  it("toggles the sidebar when the menu/close button is clicked", async () => {
    render(<JDDBLayout />);

    const toggleButton = screen.getByTestId("sidebar-toggle");
    const sidebar = screen.getByTestId("sidebar");

    // Initially not collapsed
    expect(sidebar).not.toHaveClass("w-12");

    // Collapse
    fireEvent.click(toggleButton);
    await waitFor(() => {
      expect(sidebar).toHaveClass("w-12");
    });

    // Expand
    fireEvent.click(toggleButton);
    await waitFor(() => {
      expect(sidebar).not.toHaveClass("w-12");
    });
  });

  it("displays the loading screen when loading", () => {
    mockUseStore.mockReturnValue({
      stats: { total_jobs: 10, last_updated: new Date().toISOString() },
      loading: true,
    });
    mockUseLoadingContext.mockReturnValue({
      loading: true,
      getMessage: () => ({ title: "Loading...", description: "Please wait." }),
    });

    render(
      <JDDBLayout>
        <div>Test Children</div>
      </JDDBLayout>,
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("Test Children")).not.toBeInTheDocument();
  });
});
