"""Shared by the data loaders in this folder: run a DuckDB query and write it to stdout as Parquet.

Framework runs each loader at build time and serves its stdout as the file named by the loader
(owid_energy.parquet.py -> owid_energy.parquet). Paths are resolved from this file, so the
loaders work whatever folder `observable build` runs in.
"""

import sys
import tempfile
from pathlib import Path

import duckdb

INPUT = Path(__file__).resolve().parents[4] / "data" / "input"  # <repo>/bi/observable/src/data -> <repo>/data/input


def csv(name: str, *, all_varchar: bool = False) -> str:
    path = (INPUT / f"{name}.csv").as_posix().replace("'", "''")
    return f"read_csv('{path}', header = true{', all_varchar = true' if all_varchar else ''})"


def write_parquet(query: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.parquet"
        duckdb.sql(f"COPY ({query}) TO '{out.as_posix()}' (FORMAT parquet)")
        sys.stdout.buffer.write(out.read_bytes())
