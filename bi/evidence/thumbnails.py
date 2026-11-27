"""Screenshot each Evidence page into build/thumbnails/ for the gallery cards on the index page.

Run after `npm run build` (CI does this; see .github/workflows/ci.yml):

    uv run bi/evidence/thumbnails.py

Serves bi/evidence/build under /evidence/ (the basePath), loads every page in pages/ except the
index, and writes <name>.png (light) and <name>-dark.png, where <name> is the page path with "/"
replaced by "-" (pages/practice/customer-orders.md -> practice-customer-orders.png).
Uses the Chromium that `barnacles install-browser` installs.
"""

from __future__ import annotations

import base64
import functools
import http.server
import shutil
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
BASE_PATH = "evidence"  # deployment.basePath in evidence.config.yaml
WIDTH = 640  # same size as the barnacles thumbnails (16:9)
HEIGHT = 360
HIDE_CHROME = "header, aside, nav, .toc, [class*='sidebar'] { display: none !important; }"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # no line per request in the CI log
        pass


def pages() -> list[str]:
    """Routes of every page except the index, e.g. 'practice/customer-orders'."""
    return sorted(
        p.relative_to(HERE / "pages").with_suffix("").as_posix()
        for p in (HERE / "pages").rglob("*.md")
        if p.name != "index.md"
    )


def main() -> None:
    if not (BUILD / "index.html").is_file():
        raise SystemExit(f"{BUILD} has no build; run `npm run build` in {HERE} first")
    out = BUILD / "thumbnails"
    out.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as root:
        # The build only works under its basePath, so serve it at /evidence/.
        shutil.copytree(BUILD, Path(root) / BASE_PATH, ignore=shutil.ignore_patterns("thumbnails"))
        handler = functools.partial(QuietHandler, directory=root)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}/{BASE_PATH}"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 720, "height": 900}, device_scale_factor=2)
                for route in pages():
                    name = route.replace("/", "-")
                    page.goto(f"{base}/{route}/", wait_until="networkidle")
                    page.wait_for_timeout(2500)  # charts finish rendering after the queries
                    # The page content only: no header, sidebar or table of contents.
                    page.add_style_tag(content=HIDE_CHROME)
                    article = page.locator("article").first
                    box = article.bounding_box()
                    pad = 16  # a small margin around the content, like the barnacles thumbnails
                    width = box["width"] + 2 * pad
                    x, y = max(box["x"] - pad, 0), max(box["y"] - pad, 0)
                    clip = {"x": x, "y": y, "width": width, "height": width * HEIGHT / WIDTH}
                    for theme, suffix in (("dark", "-dark"), ("light", "")):
                        page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
                        page.wait_for_timeout(800)  # charts re-colour on a theme change
                        path = out / f"{name}{suffix}.png"
                        page.screenshot(path=path, clip=clip, scale="device")  # 2x, then scaled down: sharper
                        _resize(browser, path)
                    print(f"  {route} -> thumbnails/{name}.png, {name}-dark.png")
                browser.close()
        finally:
            server.shutdown()


def _resize(browser, path: Path) -> None:
    """Scale a screenshot to WIDTH x HEIGHT with the browser (no image library needed)."""
    data = base64.b64encode(path.read_bytes()).decode()
    page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
    page.set_content(
        f"<body style='margin:0'><img src='data:image/png;base64,{data}' "
        f"style='width:{WIDTH}px;height:{HEIGHT}px;object-fit:cover;object-position:top;display:block'></body>"
    )
    page.screenshot(path=path)
    page.close()


if __name__ == "__main__":
    main()
