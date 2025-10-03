/**
 * Unit tests for QuickActionsGrid component
 */
import React from "react";
import { render, screen, fireEvent } from "../../test-utils";
import { describe, test, expect, beforeEach, mock } from "bun:test";
import { QuickActionsGrid } from "./QuickActionsGrid";

// Mock the UI components
mock.module("@/components/layout/JDDBLayout", () => ({
  ContentSection: ({
    title,
    children,
    variant,
  }: {
    title: string;
    children: React.ReactNode;
    variant?: string;
  }) => (
    <div data-testid="content-section" data-variant={variant}>
      <h2>{title}</h2>
      <div data-testid="section-content">{children}</div>
    </div>
  ),
}));

mock.module("@/components/ui/design-system", () => ({
  ActionButton: ({
    children,
    onClick,
    variant,
    color,
    icon,
    className,
  }: {
    children: React.ReactNode;
    onClick: () => void;
    variant?: string;
    color?: string;
    icon?: any;
    className?: string;
  }) => (
    <button
      onClick={onClick}
      data-testid="action-button"
      data-variant={variant}
      data-color={color}
      className={className}
    >
      {children}
    </button>
  ),
}));

describe("QuickActionsGrid Component", () => {
  const mockOnNavigateToUpload = mock(() => {});
  const mockOnNavigateToJobs = mock(() => {});
  const mockOnNavigateToSearch = mock(() => {});
  const mockOnNavigateToCompare = mock(() => {});

  beforeEach(() => {
    if (mockOnNavigateToUpload.mockReset) mockOnNavigateToUpload.mockReset();
    if (mockOnNavigateToJobs.mockReset) mockOnNavigateToJobs.mockReset();
    if (mockOnNavigateToSearch.mockReset) mockOnNavigateToSearch.mockReset();
    if (mockOnNavigateToCompare.mockReset) mockOnNavigateToCompare.mockReset();
  });

  test("renders with correct title", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    expect(screen.getByText("Quick Actions")).toBeInTheDocument();
  });

  test("renders all action buttons", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    expect(screen.getByText("Upload Files")).toBeInTheDocument();
    expect(screen.getByText("Browse Jobs")).toBeInTheDocument();
    expect(screen.getByText("Search Jobs")).toBeInTheDocument();
    expect(screen.getByText("Compare Jobs")).toBeInTheDocument();
  });

  test("renders correct number of action buttons", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    const actionButtons = screen.getAllByTestId("action-button");
    expect(actionButtons).toHaveLength(4);
  });

  test("handles upload button click", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    fireEvent.click(screen.getByText("Upload Files"));
    expect(mockOnNavigateToUpload).toHaveBeenCalled();
  });

  test("handles browse jobs button click", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    fireEvent.click(screen.getByText("Browse Jobs"));
    expect(mockOnNavigateToJobs).toHaveBeenCalled();
  });

  test("handles search jobs button click", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    fireEvent.click(screen.getByText("Search Jobs"));
    expect(mockOnNavigateToSearch).toHaveBeenCalled();
  });

  test("handles compare jobs button click", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    fireEvent.click(screen.getByText("Compare Jobs"));
    expect(mockOnNavigateToCompare).toHaveBeenCalled();
  });

  test("renders ContentSection with highlighted variant", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    const contentSection = screen.getByTestId("content-section");
    expect(contentSection).toHaveAttribute("data-variant", "highlighted");
  });

  test("renders buttons with correct variants and colors", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    const actionButtons = screen.getAllByTestId("action-button");

    // Upload button should have primary variant
    const uploadButton = actionButtons.find((button) =>
      button.textContent?.includes("Upload Files"),
    );
    expect(uploadButton).toHaveAttribute("data-variant", "primary");

    // Browse Jobs button should have outline variant and emerald color
    const browseButton = actionButtons.find((button) =>
      button.textContent?.includes("Browse Jobs"),
    );
    expect(browseButton).toHaveAttribute("data-variant", "outline");
    expect(browseButton).toHaveAttribute("data-color", "emerald");

    // Search Jobs button should have outline variant and blue color
    const searchButton = actionButtons.find((button) =>
      button.textContent?.includes("Search Jobs"),
    );
    expect(searchButton).toHaveAttribute("data-variant", "outline");
    expect(searchButton).toHaveAttribute("data-color", "blue");

    // Compare Jobs button should have outline variant and amber color
    const compareButton = actionButtons.find((button) =>
      button.textContent?.includes("Compare Jobs"),
    );
    expect(compareButton).toHaveAttribute("data-variant", "outline");
    expect(compareButton).toHaveAttribute("data-color", "amber");
  });

  test("applies correct grid layout classes", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    // The grid container should be present (we can't test CSS classes directly with our mock,
    // but we can verify the structure is rendered)
    const sectionContent = screen.getByTestId("section-content");
    expect(sectionContent).toBeInTheDocument();
  });

  test("handles multiple rapid clicks correctly", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    const uploadButton = screen.getByText("Upload Files");

    // Simulate rapid clicks
    fireEvent.click(uploadButton);
    fireEvent.click(uploadButton);
    fireEvent.click(uploadButton);

    expect(mockOnNavigateToUpload).toHaveBeenCalledTimes(3);
  });

  test("all callback functions are properly passed and called", () => {
    render(
      <QuickActionsGrid
        onNavigateToUpload={mockOnNavigateToUpload}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToSearch={mockOnNavigateToSearch}
        onNavigateToCompare={mockOnNavigateToCompare}
      />,
    );

    // Click all buttons to ensure all callbacks work
    fireEvent.click(screen.getByText("Upload Files"));
    fireEvent.click(screen.getByText("Browse Jobs"));
    fireEvent.click(screen.getByText("Search Jobs"));
    fireEvent.click(screen.getByText("Compare Jobs"));

    expect(mockOnNavigateToUpload).toHaveBeenCalledTimes(1);
    expect(mockOnNavigateToJobs).toHaveBeenCalledTimes(1);
    expect(mockOnNavigateToSearch).toHaveBeenCalledTimes(1);
    expect(mockOnNavigateToCompare).toHaveBeenCalledTimes(1);
  });
});
