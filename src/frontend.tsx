/**
 * This file is the entry point for the React app. It sets up the root
 * element and renders the App component to the DOM. It is included in
 * `src/index.html`.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import HomePage from "./app/page";

function main() {
  try {
    const rootElement = document.getElementById("root");
    if (!rootElement) {
      throw new Error("Root element not found");
    }

    const app = (
      <StrictMode>
        <HomePage />
      </StrictMode>
    );

    const root = createRoot(rootElement);
    root.render(app);
  } catch (error) {
    console.error("Failed to render the app:", error);
  }
}

main();
