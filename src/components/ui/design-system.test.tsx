import { jest, describe, beforeEach, it, expect } from "@jest/globals";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import {
  ContentSection,
  StatsCard,
  ActionButton,
  JobCard,
} from "./design-system";
import { Home } from "lucide-react";

describe("Design System Components", () => {
  describe("ContentSection", () => {
    it("renders with title, subtitle, and children", () => {
      render(
        <ContentSection title="Test Title" subtitle="Test Subtitle">
          <div>Test Children</div>
        </ContentSection>,
      );

      expect(screen.getByText("Test Title")).toBeInTheDocument();
      expect(screen.getByText("Test Subtitle")).toBeInTheDocument();
      expect(screen.getByText("Test Children")).toBeInTheDocument();
    });

    it("renders header actions", () => {
      render(
        <ContentSection headerActions={<button>Action</button>}>
          <div />
        </ContentSection>,
      );

      expect(
        screen.getByRole("button", { name: "Action" }),
      ).toBeInTheDocument();
    });

    it("applies correct classes for variants", () => {
      const { container: defaultContainer } = render(
        <ContentSection variant="default">
          <div />
        </ContentSection>,
      );
      expect(defaultContainer.firstChild).not.toHaveClass("border-blue-200/50");

      const { container: highlightedContainer } = render(
        <ContentSection variant="highlighted">
          <div />
        </ContentSection>,
      );
      expect(highlightedContainer.firstChild).toHaveClass(
        "hover:shadow-xl border-blue-200/50 dark:border-blue-400/50",
      );

      const { container: compactContainer } = render(
        <ContentSection variant="compact">
          <div />
        </ContentSection>,
      );
      const pbElement = compactContainer.querySelector(".pb-3");
      expect(pbElement).not.toBeNull();
    });
  });

  describe("StatsCard", () => {
    it("renders with title, value, and icon", () => {
      render(<StatsCard title="Test Title" value="123" icon={Home} />);

      expect(screen.getByText("Test Title")).toBeInTheDocument();
      expect(screen.getByText("123")).toBeInTheDocument();
      expect(screen.getByTestId("stats-card-icon")).toBeInTheDocument();
    });

    it("applies correct colors", () => {
      const { container } = render(
        <StatsCard title="Test" value="123" icon={Home} color="emerald" />,
      );
      const emeraldElement = container.querySelector(".text-emerald-600");
      expect(emeraldElement).not.toBeNull();
    });

    it("shows a trend", () => {
      render(<StatsCard title="Test" value="123" icon={Home} trend="+10%" />);
      expect(screen.getByText("+10%")).toBeInTheDocument();
    });

    it("calls onClick when clicked", () => {
      const onClick = jest.fn();
      render(
        <StatsCard title="Test" value="123" icon={Home} onClick={onClick} />,
      );
      fireEvent.click(screen.getByTestId("stats-card"));
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe("ActionButton", () => {
    it("renders with children and an icon", () => {
      render(<ActionButton icon={Home}>Test Button</ActionButton>);
      expect(screen.getByText("Test Button")).toBeInTheDocument();
      expect(screen.getByTestId("action-button-icon")).toBeInTheDocument();
    });

    it("applies correct colors, variants, and sizes", () => {
      const { container } = render(
        <ActionButton color="emerald" variant="primary" size="lg">
          Test
        </ActionButton>,
      );
      expect(container.firstChild).toHaveClass("bg-gradient-to-r");
      expect(container.firstChild).toHaveClass("h-12");
    });

    it("is disabled when the disabled prop is true", () => {
      render(<ActionButton disabled>Test</ActionButton>);
      expect(screen.getByRole("button")).toBeDisabled();
    });

    it("calls onClick when clicked", () => {
      const onClick = jest.fn();
      render(<ActionButton onClick={onClick}>Test</ActionButton>);
      fireEvent.click(screen.getByRole("button"));
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe("JobCard", () => {
    const job = {
      id: 1,
      job_number: "123",
      title: "Test Job",
      classification: "CS-02",
      language: "en",
      processed_date: new Date().toISOString(),
      relevance_score: 0.85,
    };

    it("renders job information correctly", () => {
      render(<JobCard job={job} />);
      expect(screen.getByText("Test Job")).toBeInTheDocument();
      expect(screen.getByText("123")).toBeInTheDocument();
      expect(screen.getByText("CS-02")).toBeInTheDocument();
      expect(screen.getByText("English")).toBeInTheDocument();
      expect(screen.getByText(/85% match/)).toBeInTheDocument();
    });

    it("shows/hides action buttons", () => {
      const { rerender } = render(
        <JobCard job={job} showActions={true} onView={() => {}} />,
      );
      expect(screen.getByRole("button", { name: "View" })).toBeInTheDocument();

      rerender(<JobCard job={job} showActions={false} />);
      expect(
        screen.queryByRole("button", { name: "View" }),
      ).not.toBeInTheDocument();
    });

    it("calls onView, onExport, and onDelete", () => {
      const onView = jest.fn();
      const onExport = jest.fn();
      const onDelete = jest.fn();

      render(
        <JobCard
          job={job}
          onView={onView}
          onExport={onExport}
          onDelete={onDelete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "View" }));
      expect(onView).toHaveBeenCalledWith(job);

      fireEvent.click(screen.getByRole("button", { name: "Export" }));
      expect(onExport).toHaveBeenCalledWith(job);

      fireEvent.click(screen.getByRole("button", { name: "Delete" }));
      expect(onDelete).toHaveBeenCalledWith(job);
    });

    it("formats language and classification correctly", () => {
      render(
        <JobCard job={{ ...job, language: "fr", classification: "AS-05" }} />,
      );
      expect(screen.getByText("French")).toBeInTheDocument();
      expect(screen.getByText(/Level 5 \(AS\)/)).toBeInTheDocument();
    });
  });
});
