const http = require("http");

// MEDIUM FIX: Add graceful shutdown handling
let isShuttingDown = false;

const server = http.createServer((req, res) => {
  // MEDIUM FIX: Return 503 during shutdown
  if (isShuttingDown) {
    res.writeHead(503, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "shutting_down" }));
    return;
  }

  // MEDIUM FIX: Add security headers
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("X-XSS-Protection", "1; mode=block");
  res.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains");

  if (req.url === "/v1/health" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
    return;
  }
  if (req.url === "/v1/ready" && req.method === "GET") {
    // MEDIUM FIX: Return not ready during shutdown
    const status = isShuttingDown ? "not_ready" : "ready";
    const statusCode = isShuttingDown ? 503 : 200;
    res.writeHead(statusCode, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status }));
    return;
  }
  res.writeHead(404);
  res.end();
});

const PORT = process.env.PORT || 8080;

// MEDIUM FIX: Add request timeout (30s)
server.timeout = 30000;
server.keepAliveTimeout = 65000; // > ALB timeout (60s)
server.headersTimeout = 66000; // > keepAliveTimeout

server.listen(PORT, () => {
  console.log(`Admin service listening on port ${PORT}`);
});

// MEDIUM FIX: Graceful shutdown on SIGTERM/SIGINT
function gracefulShutdown(signal) {
  console.log(`Received ${signal}, shutting down gracefully...`);
  isShuttingDown = true;

  // Stop accepting new connections
  server.close(() => {
    console.log("HTTP server closed");
    process.exit(0);
  });

  // Force shutdown after 10 seconds
  setTimeout(() => {
    console.error("Forced shutdown after timeout");
    process.exit(1);
  }, 10000);
}

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
