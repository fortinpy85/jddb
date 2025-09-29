#!/usr/bin/env bun

/**
 * JDDB Unified Development Server
 * Serves both API (proxied) and static frontend files from the same origin
 * Solves CORS issues by eliminating cross-origin requests
 */

import { serve } from "bun";
import { file } from "bun";

const BACKEND_API_URL = "http://localhost:8000";
const SERVER_PORT = 3003;
const DIST_DIR = "./dist";

console.log("🚀 Starting JDDB Unified Development Server...");
console.log(`📡 Server: http://localhost:${SERVER_PORT}`);
console.log(`🔗 API Proxy: ${BACKEND_API_URL}`);
console.log(`📁 Static Files: ${DIST_DIR}`);

const server = serve({
  port: SERVER_PORT,
  async fetch(req) {
    const url = new URL(req.url);
    console.log(`${req.method} ${url.pathname}`);

    // Handle API requests - proxy to backend
    if (url.pathname.startsWith("/api/")) {
      const backendUrl = `${BACKEND_API_URL}${url.pathname}${url.search}`;
      console.log(`🔄 Proxying API: ${backendUrl}`);

      try {
        const response = await fetch(backendUrl, {
          method: req.method,
          headers: req.headers,
          body: req.body,
        });

        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
        });
      } catch (error) {
        console.error("❌ API Proxy Error:", error);
        return new Response(
          JSON.stringify({
            error: "Backend API unavailable",
            message: "Please ensure the backend server is running on port 8000"
          }),
          {
            status: 503,
            headers: { "Content-Type": "application/json" },
          }
        );
      }
    }

    // Handle static files
    try {
      let filePath = url.pathname;

      // Default to index.html for SPA routing
      if (filePath === "/" || filePath === "/index.html") {
        filePath = "/index.html";
      }

      // Try to serve the static file
      const staticFile = file(`${DIST_DIR}${filePath}`);

      if (await staticFile.exists()) {
        console.log(`📄 Serving static: ${filePath}`);
        return new Response(staticFile);
      }

      // Fallback to index.html for SPA routes
      const indexFile = file(`${DIST_DIR}/index.html`);
      if (await indexFile.exists()) {
        console.log(`📄 SPA Fallback: ${filePath} → index.html`);
        return new Response(indexFile, {
          headers: { "Content-Type": "text/html" },
        });
      }

      // File not found
      return new Response("404 - File Not Found", {
        status: 404,
        headers: { "Content-Type": "text/plain" },
      });

    } catch (error) {
      console.error("❌ Static File Error:", error);
      return new Response("500 - Internal Server Error", {
        status: 500,
        headers: { "Content-Type": "text/plain" },
      });
    }
  },

  error(error) {
    console.error("❌ Server Error:", error);
    return new Response("500 - Server Error", {
      status: 500,
      headers: { "Content-Type": "text/plain" },
    });
  }
});

console.log(`✅ JDDB Unified Development Server started successfully!`);
console.log(`🌐 Open: http://localhost:${SERVER_PORT}`);
console.log(`📋 API Status: http://localhost:${SERVER_PORT}/api/jobs/status`);
console.log(`📚 API Docs: ${BACKEND_API_URL}/api/docs`);
console.log(`🛑 Press Ctrl+C to stop`);