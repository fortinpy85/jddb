import { jest, describe, beforeEach, it, expect } from "@jest/globals";
import React from "react";
import { render, screen, act, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AnimatedCounter } from "./animated-counter";

describe("AnimatedCounter", () => {
  it("renders with initial value", () => {
    render(<AnimatedCounter start={10} end={100} />);
    expect(screen.getByTestId("animated-counter")).toHaveTextContent("10");
  });

  it("animates to the end value", async () => {
    render(<AnimatedCounter end={100} duration={100} />);
    await waitFor(
      () => {
        expect(screen.getByTestId("animated-counter")).toHaveTextContent("100");
      },
      { timeout: 200 },
    );
  });

  it("respects the delay prop", async () => {
    render(<AnimatedCounter end={100} delay={500} duration={100} />);
    expect(screen.getByTestId("animated-counter")).toHaveTextContent("0");
    await new Promise((r) => setTimeout(r, 499));
    expect(screen.getByTestId("animated-counter")).toHaveTextContent("0");
    await waitFor(
      () => {
        expect(screen.getByTestId("animated-counter")).toHaveTextContent("100");
      },
      { timeout: 200 },
    );
  });

  it("formats the number with prefix, suffix, and decimals", async () => {
    render(
      <AnimatedCounter
        end={123.456}
        decimals={2}
        prefix="$"
        suffix="M"
        duration={100}
      />,
    );
    await waitFor(
      () => {
        expect(screen.getByTestId("animated-counter")).toHaveTextContent(
          /\$123\.46M/,
        );
      },
      { timeout: 200 },
    );
  });
});
