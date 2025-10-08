/**
 * This file is the entry point for the React app. It sets up the root
 * element and renders the App component to the DOM. It is included in
 * `src/index.html`.
 */
import React, { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import HomePage from "./app/page";
import "./i18n/config"; // Initialize i18next for bilingual support
import { initializeAxe } from "./utils/accessibility"; // Accessibility testing

async function main() {
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

    const root = ReactDOM.createRoot(rootElement);
    root.render(app);

    // Initialize accessibility testing in development mode
    if (process.env.NODE_ENV !== "production") {
      await initializeAxe(React, ReactDOM, 1000);
    }
  } catch (error) {
    console.error("Failed to render the app:", error);
  }
}

main();
