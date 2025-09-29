/**
 * Development Proxy Configuration for JDDB
 * Resolves cross-origin issues between frontend and backend
 */

import { serve } from "bun";

const BACKEND_URL = "http://localhost:8000";
const FRONTEND_PORT = 3000;

console.log("🚀 Starting JDDB Development Proxy...");
console.log(`📡 Frontend: http://localhost:${FRONTEND_PORT}`);
console.log(`🔗 Backend Proxy: ${BACKEND_URL}`);

serve({
  port: FRONTEND_PORT,
  async fetch(req) {
    const url = new URL(req.url);

    // Proxy API requests to backend
    if (url.pathname.startsWith("/api")) {
      const backendUrl = `${BACKEND_URL}${url.pathname}${url.search}`;
      console.log(`🔄 Proxying: ${url.pathname} → ${backendUrl}`);

      try {
        const response = await fetch(backendUrl, {
          method: req.method,
          headers: req.headers,
          body: req.body,
        });

        // Add CORS headers
        const headers = new Headers(response.headers);
        headers.set("Access-Control-Allow-Origin", "*");
        headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        headers.set("Access-Control-Allow-Headers", "*");

        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers,
        });
      } catch (error) {
        console.error("❌ Proxy error:", error);
        return new Response(JSON.stringify({ error: "Backend unavailable" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        });
      }
    }

    // Serve static files (implement basic static file serving)
    if (url.pathname === "/" || url.pathname === "/index.html") {
      return new Response(`
<!DOCTYPE html>
<html>
<head>
  <title>JDDB - Development Proxy</title>
  <style>
    body { font-family: system-ui; padding: 2rem; background: #f8fafc; }
    .container { max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .status { color: #059669; font-weight: 600; }
    .error { color: #dc2626; }
    code { background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 JDDB Development Proxy</h1>
    <p class="status">✅ Proxy server running on port ${FRONTEND_PORT}</p>
    <p>🔗 Backend API: <code>${BACKEND_URL}</code></p>
    <p>📡 API Proxy: <code>http://localhost:${FRONTEND_PORT}/api/*</code></p>

    <h2>Quick Test</h2>
    <button onclick="testApi()">Test API Connection</button>
    <div id="result" style="margin-top: 1rem;"></div>

    <script>
      async function testApi() {
        const result = document.getElementById('result');
        try {
          result.innerHTML = '⏳ Testing API...';
          const response = await fetch('/api/jobs/status');
          const data = await response.json();
          result.innerHTML = '✅ API Connected! Jobs: ' + data.total_jobs;
        } catch (error) {
          result.innerHTML = '❌ API Error: ' + error.message;
        }
      }
    </script>
  </div>
</body>
</html>`, {
        headers: { "Content-Type": "text/html" },
      });
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`✅ JDDB Development Proxy started on http://localhost:${FRONTEND_PORT}`);