/**
 * Unit tests for RecentJobsList component
 */
import React from "react";
import { render, screen, fireEvent } from "../../test-utils";
import { describe, test, expect, beforeEach, mock } from "bun:test";
import { RecentJobsList } from "./RecentJobsList";
import type { JobDescription } from "@/lib/types";

// Mock the UI components
mock.module("@/components/layout/JDDBLayout", () => ({
  ContentSection: ({
    title,
    children,
    headerActions,
  }: {
    title: string;
    children: React.ReactNode;
    headerActions?: React.ReactNode;
  }) => (
    <div data-testid="content-section">
      <div data-testid="section-header">
        <h2>{title}</h2>
        {headerActions && (
          <div data-testid="header-actions">{headerActions}</div>
        )}
      </div>
      <div data-testid="section-content">{children}</div>
    </div>
  ),
}));

mock.module("@/components/ui/design-system", () => ({
  ActionButton: ({
    children,
    onClick,
    variant,
    size,
    color,
  }: {
    children: React.ReactNode;
    onClick: () => void;
    variant?: string;
    size?: string;
    color?: string;
  }) => (
    <button
      onClick={onClick}
      data-testid="action-button"
      data-variant={variant}
      data-size={size}
      data-color={color}
    >
      {children}
    </button>
  ),
}));

mock.module("@/components/ui/empty-state", () => ({
  default: ({
    type,
    actions,
    showIllustration,
  }: {
    type: string;
    actions?: Array<{ label: string; onClick: () => void; icon?: any }>;
    showIllustration?: boolean;
  }) => (
    <div
      data-testid="empty-state"
      data-type={type}
      data-show-illustration={showIllustration}
    >
      <p>No jobs available</p>
      {actions &&
        actions.map((action, index) => (
          <button
            key={index}
            onClick={action.onClick}
            data-testid="empty-state-action"
          >
            {action.label}
          </button>
        ))}
    </div>
  ),
}));

const mockJobs: JobDescription[] = [
  {
    id: 1,
    job_number: "123456",
    title: "Director of Business Analysis",
    classification: "EX-01",
    language: "EN",
    processed_date: "2024-01-15T10:00:00Z",
    sections: [],
    metadata: undefined,
    file_path: "test/path/1",
    file_hash: "hash1",
  },
  {
    id: 2,
    job_number: "789012",
    title: "Senior Policy Analyst",
    classification: "EX-02",
    language: "FR",
    processed_date: "2024-01-16T11:00:00Z",
    sections: [],
    metadata: undefined,
    file_path: "test/path/2",
    file_hash: "hash2",
  },
];

describe("RecentJobsList Component", () => {
  const mockOnJobSelect = mock();
  const mockOnNavigateToJobs = mock();
  const mockOnNavigateToUpload = mock();

  beforeEach(() => {
    mockOnJobSelect.mockReset();
    mockOnNavigateToJobs.mockReset();
    mockOnNavigateToUpload.mockReset();
  });

  test("renders with jobs", () => {
    render(
      <RecentJobsList
        jobs={mockJobs}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    expect(screen.getByText("Recent Job Descriptions")).toBeInTheDocument();
    expect(
      screen.getByText("Director of Business Analysis"),
    ).toBeInTheDocument();
    expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();
  });

  test("displays job information correctly", () => {
    render(
      <RecentJobsList
        jobs={mockJobs}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    // Check job titles
    expect(
      screen.getByText("Director of Business Analysis"),
    ).toBeInTheDocument();
    expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();

    // Check job numbers and classifications
    expect(screen.getByText("123456 • EX-01")).toBeInTheDocument();
    expect(screen.getByText("789012 • EX-02")).toBeInTheDocument();

    // Check processed dates (formatted as locale date strings)
    // The exact format depends on system locale, so we check for date presence more flexibly
    expect(screen.getByText(/15.*01.*2024|1.*15.*2024/)).toBeInTheDocument();
    expect(screen.getByText(/16.*01.*2024|1.*16.*2024/)).toBeInTheDocument();
  });

  test("handles job selection on click", () => {
    render(
      <RecentJobsList
        jobs={mockJobs}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    fireEvent.click(screen.getByText("Director of Business Analysis"));
    expect(mockOnJobSelect).toHaveBeenCalledWith(mockJobs[0]);

    fireEvent.click(screen.getByText("Senior Policy Analyst"));
    expect(mockOnJobSelect).toHaveBeenCalledWith(mockJobs[1]);
  });

  test("renders View All button and handles click", () => {
    render(
      <RecentJobsList
        jobs={mockJobs}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    const viewAllButton = screen.getByText("View All");
    expect(viewAllButton).toBeInTheDocument();

    fireEvent.click(viewAllButton);
    expect(mockOnNavigateToJobs).toHaveBeenCalled();
  });

  test("shows empty state when no jobs", () => {
    render(
      <RecentJobsList
        jobs={[]}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    const emptyState = screen.getByTestId("empty-state");
    expect(emptyState).toBeInTheDocument();
    expect(emptyState).toHaveAttribute("data-type", "no-jobs");
    expect(emptyState).toHaveAttribute("data-show-illustration", "false");

    expect(screen.getByText("No jobs available")).toBeInTheDocument();
  });

  test("handles upload action in empty state", () => {
    render(
      <RecentJobsList
        jobs={[]}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    const uploadButton = screen.getByText("Upload Files");
    expect(uploadButton).toBeInTheDocument();

    fireEvent.click(uploadButton);
    expect(mockOnNavigateToUpload).toHaveBeenCalled();
  });

  test("handles jobs without processed_date", () => {
    const jobsWithoutDate = [
      {
        ...mockJobs[0],
        processed_date: undefined,
      },
    ];

    render(
      <RecentJobsList
        jobs={jobsWithoutDate}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    expect(screen.getByText("Not processed")).toBeInTheDocument();
  });

  test("handles jobs with undefined processed_date", () => {
    const jobsWithUndefinedDate = [
      {
        ...mockJobs[0],
        processed_date: undefined,
      },
    ] as JobDescription[];

    render(
      <RecentJobsList
        jobs={jobsWithUndefinedDate}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    expect(screen.getByText("Not processed")).toBeInTheDocument();
  });

  test("renders correct ActionButton props", () => {
    render(
      <RecentJobsList
        jobs={mockJobs}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    const actionButton = screen.getByTestId("action-button");
    expect(actionButton).toHaveAttribute("data-variant", "outline");
    expect(actionButton).toHaveAttribute("data-size", "sm");
    expect(actionButton).toHaveAttribute("data-color", "violet");
  });

  test("renders all jobs when multiple are provided", () => {
    const manyJobs = [
      ...mockJobs,
      {
        id: 3,
        job_number: "111222",
        title: "Project Manager",
        classification: "PM-05",
        language: "EN",
        processed_date: "2024-01-17T12:00:00Z",
        sections: [],
        metadata: undefined,
        file_path: "test/path/3",
        file_hash: "hash3",
      },
    ];

    render(
      <RecentJobsList
        jobs={manyJobs}
        onJobSelect={mockOnJobSelect}
        onNavigateToJobs={mockOnNavigateToJobs}
        onNavigateToUpload={mockOnNavigateToUpload}
      />,
    );

    expect(
      screen.getByText("Director of Business Analysis"),
    ).toBeInTheDocument();
    expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();
    expect(screen.getByText("Project Manager")).toBeInTheDocument();
    expect(screen.getByText("111222 • PM-05")).toBeInTheDocument();
  });
});
