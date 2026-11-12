"""Crawler test against a real local static server (two linked pages)."""
from __future__ import annotations

import asyncio
import http.server
import threading
from pathlib import Path

from app.scriptgen.crawler import crawl_site

PAGE_A = """<html><head><title>Home</title></head>
<body><a href="/rooms.html">Rooms</a><a href="https://external.example.com/x">ext</a></body></html>"""

PAGE_B = """<html><head><title>Rooms</title></head><body><a href="/">back</a></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - http.server API
        body = PAGE_A if "rooms" not in self.path else PAGE_B
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # silence request logs
        pass


def test_crawl_finds_same_origin_pages(tmp_path: Path):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        pages = asyncio.run(crawl_site(base))
        urls = [p["url"] for p in pages]
        titles = [p["title"] for p in pages]
        # The landing page is stored without a trailing slash by the server URL normalization.
        assert base in [u.rstrip("/") for u in urls]
        assert any(u.endswith("rooms.html") for u in urls)
        assert "Home" in titles and "Rooms" in titles
        # External links must not be followed (only two same-origin pages exist).
        assert len(pages) == 2
    finally:
        server.shutdown()
