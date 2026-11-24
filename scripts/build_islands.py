# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Turn every projects/<demo>/dashboards/<page>.py into marimo island fragments
for the SvelteKit site, plus a manifest the site's routes are generated from.

    uv run scripts/build_islands.py            # all demos
    uv run scripts/build_islands.py messy-orders

Each notebook is rendered in its own isolated environment, resolved from its
PEP 723 block, so demos never share (or fight over) dependencies.
Set DATA_URL to pre-render against something other than the live bucket.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "src" / "generated"


def render(notebook: Path, out_prefix: Path) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as req:
        subprocess.run(
            ["uv", "export", "--script", notebook.name, "--no-hashes", "--quiet", "-o", req.name],
            cwd=notebook.parent,
            check=True,
        )
    result = subprocess.run(
        [
            "uv",
            "run",
            "--quiet",
            "--no-project",
            "--isolated",
            "--with-requirements",
            req.name,
            "python",
            str(ROOT / "scripts" / "island_one.py"),
            notebook.name,
            str(out_prefix),
        ],
        cwd=notebook.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def main(only: set[str]) -> None:
    demos = []
    for demo_dir in sorted(p for p in (ROOT / "projects").iterdir() if p.is_dir()):
        if only and demo_dir.name not in only:
            continue
        meta = yaml.safe_load((demo_dir / "demo.yml").read_text())
        pages = []
        for notebook in sorted((demo_dir / "dashboards").glob("*.py")):
            print(f"rendering {demo_dir.name}/{notebook.stem} ...", flush=True)
            info = render(notebook, OUT / demo_dir.name / notebook.stem)
            pages.append({"slug": notebook.stem, **info})
        demos.append({"slug": demo_dir.name, **meta, "pages": pages})

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps({"demos": demos}, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}/manifest.json ({sum(len(d['pages']) for d in demos)} pages)")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
