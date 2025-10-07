/**
 * This file is the main server file for the Bun application.
 * It defines routes for the API and serves the built application from dist/.
 */
import { serve, file } from "bun";
import { existsSync } from "fs";
import { join } from "path";

function main() {
  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3003;
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const distDir = "./dist";

  // Check if dist directory exists
  if (!existsSync(distDir)) {
    console.error(
      "❌ Error: dist directory not found. Please run 'bun run build' first.",
    );
    process.exit(1);
  }

  const server = serve({
    port,
    async fetch(req) {
      const url = new URL(req.url);

      // Proxy all /api/* requests to the backend server
      if (url.pathname.startsWith("/api/")) {
        const backendReq = new Request(
          `${backendUrl}${url.pathname}${url.search}`,
          {
            method: req.method,
            headers: req.headers,
            body:
              req.method !== "GET" && req.method !== "HEAD"
                ? req.body
                : undefined,
          },
        );

        try {
          const response = await fetch(backendReq);
          return response;
        } catch (error) {
          console.error("❌ Proxy error:", error);
          return new Response(
            JSON.stringify({ error: "Backend unavailable" }),
            {
              status: 503,
              headers: { "Content-Type": "application/json" },
            },
          );
        }
      }

      // Try to serve static files from dist/ directory
      const pathname = url.pathname === "/" ? "/index.html" : url.pathname;
      const filePath = join(distDir, pathname);

      if (existsSync(filePath)) {
        return new Response(file(filePath));
      }

      // Serve index.html for all other routes (SPA fallback)
      return new Response(file(join(distDir, "index.html")));
    },
  });

  console.log(`🚀 Server running at ${server.url}`);
  console.log(`📡 Proxying /api/* to ${backendUrl}`);
  console.log(`📁 Serving from ${distDir}/`);
}

main();
