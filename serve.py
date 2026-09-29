"""Fresh Mart Faridpur — local preview with friendly URLs.

Serves the public site pages, product details, assets, styles and scripts for local previews.
Development evidence, source tools and directory listings are not public.
Use a static host for production deployment.
"""
import os
import re
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

ROOT = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))


class FreshMartHandler(SimpleHTTPRequestHandler):
    FORCE_HTML_ROUTES = {
        "/": "index.html",
        "/about": "about.html",
        "/products": "products.html",
        "/gallery": "gallery.html",
        "/contact": "contact.html",
    }
    PUBLIC_PAGES = frozenset(FORCE_HTML_ROUTES.values())
    PUBLIC_EXTENSIONS = {
        "assets": frozenset({".avif", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".svg", ".webp", ".woff", ".woff2", ".ttf", ".otf"}),
        "css": frozenset({".css", ".woff", ".woff2", ".ttf", ".otf"}),
        "js": frozenset({".js"}),
    }
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".svg": "image/svg+xml",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".js": "text/javascript",
        ".css": "text/css",
    }

    def __init__(self, *args, **kwargs):
        kwargs["directory"] = ROOT
        super().__init__(*args, **kwargs)

    def translate_path(self, path):
        clean = unquote(path.split("?", 1)[0].split("#", 1)[0])
        # Reject traversal and Windows path syntax before superclass normalization.
        components = clean.replace("\\", "/").split("/")
        if "\x00" in clean or any(
            part.startswith(".") or ":" in part for part in components if part
        ):
            raise ValueError("Not a public site route")

        # The superclass safely decodes and normalizes paths within directory.
        candidate = super().translate_path(path)
        route = "/" + "/".join(part for part in components if part)
        if route in self.FORCE_HTML_ROUTES:
            candidate = os.path.join(ROOT, self.FORCE_HTML_ROUTES[route])
        elif not os.path.splitext(candidate)[1] and os.path.isfile(candidate + ".html"):
            candidate += ".html"

        candidate = os.path.realpath(candidate)
        try:
            within_root = os.path.commonpath([ROOT, candidate]) == ROOT
        except ValueError:
            within_root = False
        if not within_root:
            raise ValueError("Not a public site route")

        relative = os.path.relpath(candidate, ROOT)
        segments = relative.split(os.sep)
        if any(segment.startswith(".") for segment in segments):
            raise ValueError("Not a public site route")
        page = len(segments) == 1 and (
            relative in self.PUBLIC_PAGES
            or re.fullmatch(r"product-[a-z0-9]+(?:-[a-z0-9]+)*\.html", relative) is not None
        )
        asset = (
            len(segments) > 1
            and segments[0].lower() in self.PUBLIC_EXTENSIONS
            and os.path.splitext(candidate)[1].lower() in self.PUBLIC_EXTENSIONS[segments[0].lower()]
        )
        if not (page or asset):
            raise ValueError("Not a public site route")
        return candidate

    def send_head(self):
        try:
            return super().send_head()
        except (ValueError, OSError):
            self.send_error(404, "File not found")
            return None

    def list_directory(self, path):
        self.send_error(404, "File not found")
        return None

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = "0.0.0.0"
    print(f"Fresh Mart Faridpur serving on http://{host}:{port}")
    print(f"Root: {ROOT}")
    server = ThreadingHTTPServer((host, port), FreshMartHandler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
