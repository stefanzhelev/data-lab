# stefanzhelev-datalab

Load remote CSV/Parquet/JSON into DuckDB with one call that behaves the same in a
[marimo](https://marimo.io) WASM page (Pyodide, no sockets) and in local Python.

```python
from stefanzhelev_datalab import load

await load("https://data.stefanzhelev.com/messy-orders/daily_revenue.parquet", "daily_revenue")
```

The table is then queryable by name, including from `mo.sql` cells. Bring your own
`duckdb` (Pyodide provides it in the browser; `pip install stefanzhelev-datalab[local]` locally).

Part of [data-lab](https://github.com/stefanzhelev/data-lab). MIT licensed.
