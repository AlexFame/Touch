import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { join, extname, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(dirname(fileURLToPath(import.meta.url)), "dist");
const HOST = process.env.HOST || "0.0.0.0";
const PORT = process.env.PORT || 5173;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "application/javascript",
  ".css":  "text/css",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".svg":  "image/svg+xml",
  ".ico":  "image/x-icon",
  ".json": "application/json",
  ".woff2":"font/woff2",
  ".woff": "font/woff",
};

async function serve(req, res) {
  try {
    const urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);

    const candidates = [
      join(DIST, urlPath),
      join(DIST, urlPath, "index.html"),
    ];

    for (const filePath of candidates) {
      try {
        const s = await stat(filePath);
        if (s.isFile()) {
          const ext = extname(filePath).toLowerCase();
          const body = await readFile(filePath);
          res.writeHead(200, {
            "Content-Type": MIME[ext] || "application/octet-stream",
            "Cache-Control": ext === ".html" ? "no-cache" : "max-age=31536000,immutable",
          });
          res.end(body);
          return;
        }
      } catch {}
    }

    // SPA fallback
    const index = await readFile(join(DIST, "index.html"));
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-cache" });
    res.end(index);
  } catch (err) {
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Server error: " + err.message);
  }
}

const server = createServer(serve);

server.on("error", (err) => {
  console.error("miniapp server failed:", err);
  process.exit(1);
});

server.listen(PORT, HOST, () => {
  console.log(`miniapp served from ${DIST} on ${HOST}:${PORT}`);
});
