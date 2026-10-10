"""Zero-dependency local server (standard library only). Run: python run_local.py  ->  http://localhost:8000
Serves the web app + the same /api endpoints as the FastAPI version, so the Live Demo works without FastAPI/Docker."""
import json, pathlib, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(ROOT))
from app.core.agents import ResearchSystem
system = ResearchSystem([json.loads(l) for l in (ROOT / "eval/data/corpus.jsonl").read_text().splitlines() if l])
STATIC = ROOT / "app/static"
TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".otf": "font/otf", ".gif": "image/gif"}

class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/health": return self.send(200, {"status": "ok", "sources": len(system.docs), "tools": list(system.tools.tools)})
        if p == "/api/tools": return self.send(200, system.tools.specs())
        if p == "/api/metrics": return self.send(200, system.cost.summary())
        f = (STATIC / ("index.html" if p == "/" else p.lstrip("/"))).resolve()
        if STATIC.resolve() in f.parents and f.is_file(): return self.send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))
        self.send(404, {"detail": "not found"})
    def do_POST(self):
        if self.path != "/api/research": return self.send(404, {"detail": "not found"})
        try: r = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError: return self.send(422, {"detail": "invalid JSON"})
        q = r.get("question", "")
        if not isinstance(q, str) or not 8 <= len(q) <= 500: return self.send(422, {"detail": "question must be 8-500 characters"})
        if not q.strip(): return self.send(400, {"detail": "question must not be blank"})
        self.send(200, system.run(q))
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Multi-agent research system running at http://localhost:{port}  (Ctrl+C to stop)"); ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
