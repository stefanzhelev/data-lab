# /// script
# requires-python = ">=3.12"
# dependencies = ["boto3>=1.35", "pyyaml>=6"]
# ///
"""Build https://data.stefanzhelev.com/index.html (+ index.json) from what's in the bucket.

Lists every object over R2's S3 API, groups files by their top-level folder (the
demo), adds the description and licence from projects/<demo>/demo.yml, and
uploads both files to the bucket root. A Cloudflare rewrite rule (infra/r2.tf)
serves index.html at "/".

    R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... R2_BUCKET=... \
        uv run scripts/build_data_index.py [--dry-run]
"""

import html
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import boto3
import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_URL = "https://data.stefanzhelev.com"
SITE_URL = "https://lab.stefanzhelev.com"
GENERATED = {"index.html", "index.json"}


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def list_objects(s3, bucket: str) -> list[dict]:
    objects = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        for o in page.get("Contents", []):
            if o["Key"] not in GENERATED:
                objects.append(
                    {
                        "key": o["Key"],
                        "size": o["Size"],
                        "modified": o["LastModified"].astimezone(UTC).isoformat(),
                    }
                )
    return sorted(objects, key=lambda o: o["key"])


def group(objects: list[dict]) -> list[dict]:
    demos: dict[str, dict] = {}
    for o in objects:
        slug, _, rest = o["key"].partition("/")
        if not rest:  # file at the bucket root
            slug, rest = "", o["key"]
        meta_file = ROOT / "projects" / slug / "demo.yml"
        if slug not in demos:
            meta = yaml.safe_load(meta_file.read_text()) if slug and meta_file.exists() else {}
            demos[slug] = {
                "slug": slug,
                "title": meta.get("title", slug or "Other files"),
                "description": meta.get("description", ""),
                "licence": meta.get("licence", ""),
                "source": meta.get("source", ""),
                "dashboard": f"{SITE_URL}/{slug}/" if meta else "",
                "files": [],
            }
        about = (
            (yaml.safe_load(meta_file.read_text()) or {}).get("datasets", {}).get(rest, "")
            if slug and meta_file.exists()
            else ""
        )
        demos[slug]["files"].append(
            {**o, "name": rest, "url": f"{PUBLIC_URL}/{o['key']}", "description": about}
        )
    return sorted(demos.values(), key=lambda d: (d["slug"] == "", d["slug"]))


def render(demos: list[dict], generated: str) -> str:
    e = html.escape
    sections = []
    for d in demos:
        rows = "\n".join(
            f'<tr><td><a href="{e(f["url"])}">{e(f["name"])}</a>'
            + (f'<div class="muted">{e(f["description"])}</div>' if f["description"] else "")
            + f'</td><td class="num">{human(f["size"])}</td><td class="num">{e(f["modified"][:10])}</td></tr>'
            for f in d["files"]
        )
        meta = " · ".join(
            x
            for x in [
                e(d["description"]),
                f"Licence: {e(d['licence'])}" if d["licence"] else "",
                f'<a href="{e(d["dashboard"])}">Dashboard →</a>' if d["dashboard"] else "",
            ]
            if x
        )
        sections.append(
            f'<section><h2>{e(d["title"])}</h2><p class="muted">{meta}</p>'
            f'<table><thead><tr><th>File</th><th class="num">Size</th><th class="num">Updated</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></section>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data · Stefan Zhelev</title>
<meta name="description" content="Public datasets behind the Data Lab demos.">
<style>
:root {{ --bg:#fff; --fg:#18181b; --muted:#71717a; --line:#e4e4e7; --link:#18181b; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#09090b; --fg:#fafafa; --muted:#a1a1aa; --line:#27272a; --link:#fafafa; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--fg);
  font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif }}
main {{ max-width:56rem; margin:0 auto; padding:2rem 16px }} h1 {{ margin:0 0 .25rem; font-size:1.75rem }}
h2 {{ margin:2rem 0 .25rem; font-size:1.15rem }} a {{ color:var(--link); text-underline-offset:3px }}
.muted {{ color:var(--muted); font-size:.875rem }} table {{ width:100%; border-collapse:collapse; margin-top:.5rem }}
th,td {{ text-align:left; padding:.5rem .25rem; border-bottom:1px solid var(--line); vertical-align:top }}
th {{ font-weight:500; color:var(--muted); font-size:.8rem }} .num {{ text-align:right; white-space:nowrap }}
code {{ font-size:.85em }}
</style></head><body><main>
<h1>Data</h1>
<p class="muted">Public files behind the <a href="{SITE_URL}/">Data Lab</a> demos. Read them directly, e.g.
<code>SELECT * FROM '{PUBLIC_URL}/&lt;demo&gt;/&lt;file&gt;.parquet'</code> in DuckDB.
Machine-readable list: <a href="index.json">index.json</a>. Updated {e(generated[:16].replace("T", " "))} UTC.</p>
{"".join(sections) or "<p>No files yet.</p>"}
</main></body></html>
"""


def main(dry_run: bool) -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    bucket = os.environ["R2_BUCKET"]
    generated = datetime.now(UTC).isoformat(timespec="seconds")
    demos = group(list_objects(s3, bucket))
    page = render(demos, generated)
    index = json.dumps({"generated": generated, "base_url": PUBLIC_URL, "demos": demos}, indent=2)

    if dry_run:
        Path("index.html").write_text(page)
        Path("index.json").write_text(index)
        print(f"dry run: wrote ./index.html and ./index.json ({sum(len(d['files']) for d in demos)} files)")
        return
    for key, body, ctype in [
        ("index.html", page, "text/html; charset=utf-8"),
        ("index.json", index, "application/json"),
    ]:
        s3.put_object(
            Bucket=bucket, Key=key, Body=body.encode(), ContentType=ctype, CacheControl="public, max-age=300"
        )
    print(f"uploaded index.html + index.json ({sum(len(d['files']) for d in demos)} files)")


if __name__ == "__main__":
    main("--dry-run" in sys.argv[1:])
