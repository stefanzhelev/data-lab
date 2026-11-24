"""Render ONE marimo notebook to island fragments. Called by build_islands.py.

Runs inside the notebook's own environment (its PEP 723 dependencies), because
MarimoIslandGenerator.build() executes the notebook to pre-render outputs.

    python island_one.py <notebook.py> <out_prefix>
    -> <out_prefix>.head.html, <out_prefix>.body.html; prints JSON metadata
"""

import asyncio
import json
import re
import sys
from pathlib import Path

import marimo
from marimo import MarimoIslandGenerator


async def main(notebook: Path, out_prefix: Path) -> None:
    generator = MarimoIslandGenerator.from_file(str(notebook), display_code=False)
    await generator.build()
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    out_prefix.with_suffix(".head.html").write_text(generator.render_head())
    out_prefix.with_suffix(".body.html").write_text(
        generator.render_body(include_init_island=False, include_payload=True)
    )
    match = re.search(r'app_title\s*=\s*"([^"]+)"', notebook.read_text())
    title = match.group(1) if match else notebook.stem
    print(json.dumps({"title": title, "marimo": marimo.__version__}))


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()))
