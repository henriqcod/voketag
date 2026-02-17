const http = require("http");

const server = http.createServer((req, res) => {
  if (req.url === "/v1/health" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
    return;
  }
  if (req.url === "/v1/ready" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ready" }));
    return;
  }
  res.writeHead(404);
  res.end();
});

server.listen(8080);
