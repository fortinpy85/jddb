import { describe, beforeEach, it, expect } from "vitest";
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
      const { rerender, container } = render(<SkeletonCard showActions={true} />);
      expect(container.querySelectorAll(".h-8")).toHaveLength(2);

      rerender(<SkeletonCard showActions={false} />);
      expect(container.querySelectorAll(".h-8")).toHaveLength(0);
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
      expect(container.querySelectorAll(".animate-pulse")).toHaveLength(7);
    });
  });

  describe("SkeletonList", () => {
    it("renders the correct number of skeleton job cards", () => {
      const { container } = render(<SkeletonList count={3} />);
      // Select the SkeletonJobCard components by their unique class combination
      expect(container.querySelectorAll(".rounded-lg.border.bg-white.shadow-sm.p-4")).toHaveLength(3);
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
      const { rerender, container } = render(<SkeletonLoader type="job-list" />);
      expect(container.querySelector(".space-y-6")).toBeInTheDocument();

      rerender(<SkeletonLoader type="job-card" />);
      expect(container.querySelector(".space-y-3")).toBeInTheDocument();

      rerender(<SkeletonLoader type="job-details" />);
      expect(container.querySelector(".space-y-6")).toBeInTheDocument();

      rerender(<SkeletonLoader type="stats-dashboard" />);
      // Check for responsive grid classes (grid-cols-1 md:grid-cols-2 lg:grid-cols-4)
      expect(container.querySelector("[class*='grid-cols']")).toBeInTheDocument();

      rerender(<SkeletonLoader type="search-results" />);
      expect(container.querySelector(".space-y-4")).toBeInTheDocument();

      rerender(<SkeletonLoader type="upload-area" />);
      expect(container.querySelector(".border-dashed")).toBeInTheDocument();

      rerender(<SkeletonLoader type="comparison" />);
      // Check for responsive grid classes (grid-cols-1 lg:grid-cols-2)
      expect(container.querySelector("[class*='grid-cols']")).toBeInTheDocument();

      rerender(<SkeletonLoader type="table-rows" />);
      // Table rows skeleton uses space-y-2, not divide-y
      expect(container.querySelector(".space-y-2")).toBeInTheDocument();
    });
  });
});
