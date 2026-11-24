# Data Lab

Small, end-to-end data projects. Each demo goes from raw files to a tested model
to a live dashboard that runs entirely in your browser.

**Live:** [lab.stefanzhelev.com](https://lab.stefanzhelev.com) · **Data:** [data.stefanzhelev.com](https://data.stefanzhelev.com)

| Demo | What it shows | Stack |
|---|---|---|
| [Messy orders](projects/messy-orders) | Cleaning, quarantining and reconciling a deliberately messy orders feed | dbt, DuckDB, marimo |

## How it fits together

```
projects/<demo>/data, dbt, dagster   ──(GitHub Actions)──►  parquet on R2 (data.stefanzhelev.com/<demo>/)
projects/<demo>/dashboards/*.py      ──(marimo islands)──►  SvelteKit site on Cloudflare Pages (lab.stefanzhelev.com)
                                                            dashboards fetch the parquet and query it with DuckDB-in-WASM
```

| Path | Purpose |
|---|---|
| `projects/<demo>/` | One self-contained demo: `demo.yml`, `data/`, optional `dbt/` and `dagster/`, `dashboards/` |
| `libs/datalab/` | [`stefanzhelev-datalab`](https://pypi.org/project/stefanzhelev-datalab/) on PyPI: loads remote files into DuckDB, in the browser and locally |
| `site/` | SvelteKit + shadcn-svelte site that hosts the dashboards as marimo islands |
| `scripts/` | `build_islands.py` (notebooks → site fragments), `build_data_index.py` (bucket index page) |
| `infra/` | OpenTofu, one file per provider: Cloudflare (bucket, CORS, index rewrite, Pages, CI tokens) and GitHub (Actions secrets, PyPI environments) |
| `.github/workflows/` | CI, per-demo pipelines, data index, site deploy, PyPI release |

Every demo has its own environment: notebooks declare dependencies inline (PEP 723),
pipelines have their own `pyproject.toml` and `uv.lock`. Nothing is shared at the root.

## Run locally

```bash
# a pipeline
cd projects/messy-orders/dbt && uv run dbt build --profiles-dir .

# a dashboard (editable notebook, isolated env)
uvx marimo edit --sandbox projects/messy-orders/dashboards/overview.py

# the site
uv run scripts/build_islands.py && cd site && npm ci && npm run dev
```

## Licence

Code: [MIT](LICENSE). Data: see each demo's `demo.yml`.
