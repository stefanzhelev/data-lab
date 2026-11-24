"""Load remote data into DuckDB, the same way in the browser (Pyodide) and locally.

In a marimo WASM page there are no sockets, so DuckDB can't read ``https://`` paths
itself. ``load`` downloads the file first (browser ``fetch`` under Pyodide,
``urllib`` elsewhere) and materialises it as a DuckDB table, so later cells can
query it by name, including from ``mo.sql``.

    from stefanzhelev_datalab import load
    await load("https://data.stefanzhelev.com/messy-orders/daily_revenue.parquet", "daily_revenue")
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

__all__ = ["fetch", "in_browser", "load"]

_READERS = {
    ".parquet": "read_parquet('{path}')",
    ".csv": "read_csv('{path}', header = true, all_varchar = {all_varchar})",
    ".json": "read_json_auto('{path}')",
}
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_USER_AGENT = "stefanzhelev-datalab (+https://github.com/stefanzhelev/data-lab)"


def in_browser() -> bool:
    """True when running under Pyodide (marimo WASM / islands)."""
    return sys.platform == "emscripten"


async def fetch(url: str, dest_dir: str | Path | None = None) -> Path:
    """Download ``url`` to a local file and return its path."""
    name = Path(urlparse(url).path).name or "download"
    dest = Path(dest_dir or tempfile.gettempdir()) / name

    if in_browser():
        from pyodide.http import pyfetch  # only importable under Pyodide

        response = await pyfetch(url)
        if not response.ok:
            raise OSError(f"GET {url} -> HTTP {response.status}")
        dest.write_bytes(await response.bytes())
    else:
        import urllib.request

        # Cloudflare's Browser Integrity Check rejects urllib's default
        # "Python-urllib/x.y" User-Agent (error 1010), so name ourselves.
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})  # noqa: S310
        with urllib.request.urlopen(request) as response:  # noqa: S310 (caller-supplied URL by design)
            dest.write_bytes(response.read())
    return dest


async def load(url: str, table: str, *, con=None, all_varchar: bool = False):
    """Download ``url`` and (re)create it as DuckDB table ``table``.

    ``all_varchar`` applies to CSV only: keep every column as text, which is what
    you want when showing raw, untrusted data. Returns the table as a relation.
    """
    import duckdb

    if not _IDENTIFIER.match(table):
        raise ValueError(f"invalid table name: {table!r}")
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix not in _READERS:
        raise ValueError(f"unsupported file type {suffix!r}; expected one of {sorted(_READERS)}")

    path = (await fetch(url)).as_posix().replace("'", "''")
    reader = _READERS[suffix].format(path=path, all_varchar=str(all_varchar).lower())
    db = con or duckdb
    db.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM {reader}")
    return db.table(table)
