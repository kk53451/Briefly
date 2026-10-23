"""Serve only this design prototype and the repository's local font assets."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse

ROOT = Path(__file__).resolve().parent
FONTS = ROOT.parents[2] / "flutter" / "assets" / "fonts"

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        requested = unquote(urlsplit(path).path)
        if requested.startswith("/flutter/assets/fonts/"):
            base = FONTS
            relative = requested.removeprefix("/flutter/assets/fonts/")
        else:
            base = ROOT
            relative = requested.lstrip("/") or "index.html"
        target = (base / relative).resolve()
        if not target.is_relative_to(base) or target.suffix.lower() not in {".html", ".css", ".js", ".png", ".svg", ".jpg", ".woff2", ".ttf", ".otf"}:
            return str(ROOT / "not-found")
        return str(target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"BRIEFLY BI: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
