import asyncio
import http.server
import threading
from functools import partial

import duckdb
import pytest
from stefanzhelev_datalab import in_browser, load


@pytest.fixture
def server(tmp_path):
    (tmp_path / "people.csv").write_text("id,name\n001, Ada \n002,Bob\n")
    duckdb.sql(f"COPY (SELECT 1 AS x UNION ALL SELECT 2) TO '{tmp_path / 'nums.parquet'}'")
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_not_in_browser():
    assert in_browser() is False


def test_csv_all_varchar_keeps_raw_text(server):
    con = duckdb.connect()
    rel = asyncio.run(load(f"{server}/people.csv", "people", con=con, all_varchar=True))
    assert rel.fetchall() == [("001", " Ada "), ("002", "Bob")]


def test_parquet(server):
    con = duckdb.connect()
    asyncio.run(load(f"{server}/nums.parquet", "nums", con=con))
    assert con.sql("SELECT sum(x) FROM nums").fetchall() == [(3,)]


def test_rejects_bad_table_name(server):
    with pytest.raises(ValueError):
        asyncio.run(load(f"{server}/nums.parquet", "x; DROP TABLE y"))
