/**
 * Unit tests for StatsOverview component
 */
import React from "react";
import { render, screen } from "../../test-utils";
import { describe, test, expect, beforeEach, mock } from "bun:test";
import { StatsOverview } from "./StatsOverview";
import type { ProcessingStats } from "@/lib/types";

// Mock the UI components to focus on component logic
mock.module("@/components/ui/animated-counter", () => ({
  AnimatedCounter: ({ end }: { end: number }) => (
    <span data-testid="animated-counter">{end}</span>
  ),
}));

mock.module("@/components/ui/design-system", () => {
  interface MockStatsCardProps {
    title: string;
    value: React.ReactNode;
    tooltip: string;
    icon: React.ElementType;
    color: string;
  }
  return {
    StatsCard: ({
      title,
      value,
      tooltip,
      icon: Icon,
      color,
    }: MockStatsCardProps) => (
      <div data-testid="stats-card" aria-label={tooltip} data-color={color}>
        {Icon && <Icon data-testid="stats-card-icon" />}
        <h3>{title}</h3>
        <div>{value}</div>
      </div>
    ),
  };
});

mock.module("@/components/ui/transitions", () => ({
  StaggerAnimation: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className: string;
  }) => (
    <div className={className} data-testid="stagger-animation">
      {children}
    </div>
  ),
}));

const mockStats: ProcessingStats = {
  total_jobs: 150,
  processing_status: {
    completed: 120,
    processing: 10,
    pending: 15,
    needs_review: 5,
    failed: 0,
  },
  by_classification: {
    "EX-01": 50,
    "EX-02": 75,
    "EX-03": 25,
  },
  by_language: {
    EN: 100,
    FR: 50,
  },
  last_updated: "2024-01-17T12:00:00Z",
};

const emptyStats: ProcessingStats = {
  total_jobs: 0,
  processing_status: {
    completed: 0,
    processing: 0,
    pending: 0,
    needs_review: 0,
    failed: 0,
  },
  by_classification: {},
  by_language: {},
  last_updated: "",
};

describe("StatsOverview Component", () => {
  test("renders with valid stats", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("Total Jobs")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Need Review")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  test("displays correct stat values", () => {
    render(<StatsOverview stats={mockStats} />);

    // Check that AnimatedCounter components are rendered with correct values
    const counters = screen.getAllByTestId("animated-counter");
    expect(counters).toHaveLength(4);

    // Total jobs
    expect(screen.getByText("150")).toBeInTheDocument();
    // Completed
    expect(screen.getByText("120")).toBeInTheDocument();
    // Need Review
    expect(screen.getByText("5")).toBeInTheDocument();
    // Processing (processing + pending)
    expect(screen.getByText("25")).toBeInTheDocument();
  });

  test("handles empty stats gracefully", () => {
    render(<StatsOverview stats={emptyStats} />);

    expect(screen.getByText("Total Jobs")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Need Review")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();

    // Should show 0 for all values when stats is null
    const counters = screen.getAllByTestId("animated-counter");
    counters.forEach((counter) => {
      expect(counter).toHaveTextContent("0");
    });
  });

  test("handles missing processing_status gracefully", () => {
    const incompleteStats = {
      ...mockStats,
      processing_status: undefined,
    } as any;

    render(<StatsOverview stats={incompleteStats} />);

    // Should still render without crashing
    expect(screen.getByText("Total Jobs")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
  });

  test("calculates combined processing count correctly", () => {
    const statsWithBothProcessingTypes = {
      ...mockStats,
      processing_status: {
        ...mockStats.processing_status,
        processing: 8,
        pending: 12,
      },
    };

    render(<StatsOverview stats={statsWithBothProcessingTypes} />);

    // Processing should show processing + pending = 8 + 12 = 20
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  test("renders with StaggerAnimation wrapper", () => {
    render(<StatsOverview stats={mockStats} />);

    const staggerWrapper = screen.getByTestId("stagger-animation");
    expect(staggerWrapper).toBeInTheDocument();
    expect(staggerWrapper).toHaveClass(
      "grid",
      "grid-cols-1",
      "md:grid-cols-2",
      "lg:grid-cols-4",
      "gap-6",
    );
  });

  test("renders correct number of StatsCard components", () => {
    render(<StatsOverview stats={mockStats} />);

    const statsCards = screen.getAllByTestId("stats-card");
    expect(statsCards).toHaveLength(4);
  });

  test("includes proper tooltips for accessibility", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(
      screen.getByLabelText("Total number of job descriptions in the database"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "Jobs that have been fully processed and are ready for use",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "Jobs that require manual review due to processing issues",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "Jobs currently being processed or pending processing",
      ),
    ).toBeInTheDocument();
  });

  test("handles zero values correctly", () => {
    render(<StatsOverview stats={emptyStats} />);

    const counters = screen.getAllByTestId("animated-counter");
    counters.forEach((counter) => {
      expect(counter).toHaveTextContent("0");
    });
  });
});
