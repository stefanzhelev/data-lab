"""Screenshot each page of a built BI site for the gallery cards on its index page.

Run after the site's build (CI does this; see .github/workflows/ci.yml):

    uv run bi/thumbnails.py evidence      # bi/evidence/build    -> build/thumbnails/
    uv run bi/thumbnails.py observable    # bi/observable/dist   -> dist/thumbnails/

Serves the build under its base path (/evidence/, /observable/), loads every page except the
index, hides the site's header and sidebar, and writes <name>.png (light) and <name>-dark.png,
where <name> is the page path with "/" replaced by "-" (practice/customer-orders ->
practice-customer-orders.png). A site with only a dark theme gets <name>-dark.png only.
Uses the Chromium that `barnacles install-browser` installs.
"""

from __future__ import annotations

import base64
import functools
import http.server
import shutil
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import sync_playwright

BI = Path(__file__).resolve().parent
WIDTH = 640  # same size as the barnacles thumbnails (16:9)
HEIGHT = 360


@dataclass(frozen=True)
class Site:
    project: Path  # the tool's folder under bi/
    build: str  # build output folder, relative to project
    base: str  # base path the build is served under
    pages: str  # folder of the markdown pages, relative to project
    content: str  # CSS selector of the page content
    hide: str  # CSS selectors to hide (header, sidebar, table of contents)
    themes: tuple[str, ...]  # html[data-theme] values to screenshot; "" = the site's only theme
    trailing_slash: bool  # page URLs end in "/" (Evidence) or not (Observable: page.html)


SITES = {
    "evidence": Site(
        project=BI / "evidence",
        build="build",
        base="evidence",
        pages="pages",
        content="article",
        hide="header, aside, nav, .toc, [class*='sidebar']",
        themes=("dark", "light"),
        trailing_slash=True,
    ),
    "observable": Site(
        project=BI / "observable",
        build="dist",
        base="observable",
        pages="src",
        content="#observablehq-main",
        hide="#observablehq-header, #observablehq-sidebar, #observablehq-sidebar-toggle, #observablehq-toc",
        themes=("",),  # theme: "dark" in observablehq.config.js
        trailing_slash=False,
    ),
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Static files, with /page served from page.html (Framework's clean URLs) and no request log."""

    def translate_path(self, path: str) -> str:
        local = super().translate_path(path)
        if not Path(local).exists() and Path(local + ".html").is_file():
            return local + ".html"
        return local

    def log_message(self, *args) -> None:
        pass


def routes(site: Site) -> list[str]:
    """Every page except the index, e.g. 'practice/customer-orders'."""
    root = site.project / site.pages
    return sorted(
        p.relative_to(root).with_suffix("").as_posix()
        for p in root.rglob("*.md")
        if p.name != "index.md" and not p.relative_to(root).parts[0].startswith((".", "_", "data"))
    )


def main(name: str) -> None:
    site = SITES[name]
    build = site.project / site.build
    if not (build / "index.html").is_file():
        raise SystemExit(f"{build} has no build; build the {name} site first")
    out = build / "thumbnails"
    out.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as root:
        # Builds only work under their base path, so serve this one at /<base>/.
        shutil.copytree(build, Path(root) / site.base, ignore=shutil.ignore_patterns("thumbnails"))
        handler = functools.partial(QuietHandler, directory=root)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}/{site.base}"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 720, "height": 900}, device_scale_factor=2)
                for route in routes(site):
                    thumb = route.replace("/", "-")
                    page.goto(f"{base}/{route}{'/' if site.trailing_slash else ''}", wait_until="networkidle")
                    page.wait_for_timeout(2500)  # charts finish rendering after the queries
                    page.add_style_tag(content=f"{site.hide} {{ display: none !important; }}")
                    page.wait_for_timeout(300)
                    box = page.locator(site.content).first.bounding_box()
                    pad = 16  # a small margin around the content, like the barnacles thumbnails
                    width = box["width"] + 2 * pad
                    x, y = max(box["x"] - pad, 0), max(box["y"] - pad, 0)
                    clip = {"x": x, "y": y, "width": width, "height": width * HEIGHT / WIDTH}
                    written = []
                    for theme in site.themes:
                        if theme:
                            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
                            page.wait_for_timeout(800)  # charts re-colour on a theme change
                        path = out / f"{thumb}{'' if theme == 'light' else '-dark'}.png"
                        page.screenshot(path=path, clip=clip, scale="device")  # 2x, then scaled down: sharper
                        _resize(browser, path)
                        written.append(path.name)
                    print(f"  {route} -> thumbnails/{', '.join(written)}")
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
    if len(sys.argv) != 2 or sys.argv[1] not in SITES:
        raise SystemExit(f"usage: uv run bi/thumbnails.py {{{'|'.join(SITES)}}}")
    main(sys.argv[1])
