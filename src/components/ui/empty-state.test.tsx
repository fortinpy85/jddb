import { jest, describe, beforeEach, it, expect } from "@jest/globals";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { EmptyState } from "./empty-state";

describe("EmptyState", () => {
  it("renders correct content for no-jobs type", () => {
    render(<EmptyState type="no-jobs" />);
    expect(screen.getByText("No Job Descriptions Yet")).toBeInTheDocument();
    expect(screen.getByText(/Start by uploading/)).toBeInTheDocument();
    expect(screen.getByTestId("empty-state-icon-advanced")).toBeInTheDocument();
    expect(screen.getByText("📋")).toBeInTheDocument();
  });

  it("renders correct content for no-search-results type", () => {
    render(<EmptyState type="no-search-results" searchQuery="test" />);
    expect(screen.getByText("No Results Found")).toBeInTheDocument();
    expect(
      screen.getByText(/No job descriptions found for "test"/),
    ).toBeInTheDocument();
  });

  it("renders custom title, description, and actions", () => {
    const onActionClick = jest.fn();
    render(
      <EmptyState
        type="general"
        title="Custom Title"
        description="Custom Description"
        actions={[{ label: "Custom Action", onClick: onActionClick }]}
      />,
    );

    expect(screen.getByText("Custom Title")).toBeInTheDocument();
    expect(screen.getByText("Custom Description")).toBeInTheDocument();

    const actionButton = screen.getByRole("button", { name: "Custom Action" });
    fireEvent.click(actionButton);
    expect(onActionClick).toHaveBeenCalledTimes(1);
  });

  it("shows/hides the illustration", () => {
    const { rerender } = render(
      <EmptyState type="no-jobs" showIllustration={true} />,
    );
    expect(screen.getByText("📋")).toBeInTheDocument();

    rerender(<EmptyState type="no-jobs" showIllustration={false} />);
    expect(screen.queryByText("📋")).not.toBeInTheDocument();
  });
});
