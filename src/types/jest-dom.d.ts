/// <reference types="@testing-library/jest-dom" />

declare module "bun:test" {
  interface Matchers<T = unknown> {
    toBeInTheDocument(): T;
    toHaveTextContent(text: string | RegExp): T;
    toHaveClass(className: string): T;
    toBeVisible(): T;
    toBeDisabled(): T;
    toBeEnabled(): T;
    toHaveAttribute(attr: string, value?: string): T;
    toHaveValue(value: string | number): T;
    toBeChecked(): T;
    toHaveFocus(): T;
    toBeInvalid(): T;
    toBeValid(): T;
    toBeEmptyDOMElement(): T;
    toContainElement(element: HTMLElement | null): T;
    toContainHTML(htmlText: string): T;
    toHaveDisplayValue(value: string | RegExp | (string | RegExp)[]): T;
    toHaveFormValues(expectedValues: Record<string, any>): T;
    toHaveStyle(css: string | Record<string, any>): T;
    toHaveAccessibleDescription(
      expectedAccessibleDescription?: string | RegExp,
    ): T;
    toHaveAccessibleName(expectedAccessibleName?: string | RegExp): T;
    toHaveErrorMessage(expectedErrorMessage?: string | RegExp): T;
  }
}

export {};
