import { jest, describe, beforeEach, it, expect } from "@jest/globals";
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import {
  Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonStats,
  SkeletonJobCard,
  SkeletonList,
  SkeletonTable,
  SkeletonLoader,
} from "./skeleton";

describe("Skeleton Components", () => {
  describe("Skeleton", () => {
    it("renders with correct width, height, and rounded styles", () => {
      const { container } = render(
        <Skeleton width={100} height={50} rounded={true} />,
      );
      const skeleton = container.firstChild;
      expect(skeleton).toHaveStyle("width: 100px");
      expect(skeleton).toHaveStyle("height: 50px");
      expect(skeleton).toHaveClass("rounded-full");
    });
  });

  describe("SkeletonText", () => {
    it("renders the correct number of lines", () => {
      const { container } = render(<SkeletonText lines={5} />);
      expect(container.querySelectorAll(".animate-pulse")).toHaveLength(5);
    });
  });

  describe("SkeletonCard", () => {
    it("renders with or without actions", () => {
      const { rerender } = render(<SkeletonCard showActions={true} />);
      expect(screen.getAllByRole("generic", { name: "" })).toHaveLength(2);

      rerender(<SkeletonCard showActions={false} />);
      expect(screen.queryAllByRole("generic", { name: "" })).toHaveLength(0);
    });
  });

  describe("SkeletonStats", () => {
    it("renders the correct number of stats cards", () => {
      const { container } = render(<SkeletonStats />);
      expect(container.querySelectorAll(".rounded-lg")).toHaveLength(4);
    });
  });

  describe("SkeletonJobCard", () => {
    it("renders the basic structure of a job card", () => {
      const { container } = render(<SkeletonJobCard />);
      expect(container.querySelectorAll(".animate-pulse")).toHaveLength(5);
    });
  });

  describe("SkeletonList", () => {
    it("renders the correct number of skeleton job cards", () => {
      const { container } = render(<SkeletonList count={3} />);
      expect(container.querySelectorAll(".space-y-3 > div")).toHaveLength(3);
    });
  });

  describe("SkeletonTable", () => {
    it("renders the correct number of rows", () => {
      const { container } = render(<SkeletonTable rows={4} />);
      expect(container.querySelectorAll(".divide-y > div")).toHaveLength(4);
    });
  });

  describe("SkeletonLoader", () => {
    it("renders the correct skeleton based on the type prop", () => {
      const { rerender } = render(<SkeletonLoader type="job-list" />);
      expect(screen.getByText(/Job Cards/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="job-card" />);
      expect(screen.getByText(/Job Card Skeleton/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="job-details" />);
      expect(screen.getByText(/Job Details Skeleton/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="stats-dashboard" />);
      expect(screen.getByText(/Stats Dashboard Skeleton/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="search-results" />);
      expect(screen.getByText(/Search Results Skeleton/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="upload-area" />);
      expect(screen.getByText(/Upload Area Skeleton/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="comparison" />);
      expect(screen.getByText(/Comparison Skeleton/)).toBeInTheDocument();

      rerender(<SkeletonLoader type="table-rows" />);
      expect(screen.getByText(/Table Rows Skeleton/)).toBeInTheDocument();
    });
  });
});
