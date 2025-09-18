/// <reference types="@testing-library/jest-dom" />

declare global {
  namespace Vi {
    interface Assertion {
      toBeInTheDocument(): void;
      toHaveTextContent(text: string | RegExp): void;
      toHaveClass(className: string): void;
      toBeVisible(): void;
      toBeDisabled(): void;
      toBeEnabled(): void;
      toHaveAttribute(attr: string, value?: string): void;
      toHaveValue(value: string | number): void;
      toBeChecked(): void;
      toHaveFocus(): void;
      toBeInvalid(): void;
      toBeValid(): void;
      toBeEmptyDOMElement(): void;
      toContainElement(element: HTMLElement | null): void;
      toContainHTML(htmlText: string): void;
      toHaveDisplayValue(value: string | RegExp | (string | RegExp)[]): void;
      toHaveFormValues(expectedValues: Record<string, any>): void;
      toHaveStyle(css: string | Record<string, any>): void;
      toHaveAccessibleDescription(expectedAccessibleDescription?: string | RegExp): void;
      toHaveAccessibleName(expectedAccessibleName?: string | RegExp): void;
      toHaveErrorMessage(expectedErrorMessage?: string | RegExp): void;
    }
  }
}

export {};