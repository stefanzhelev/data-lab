# Data Lab

Small data projects as [marimo](https://marimo.io) notebooks, published as a static gallery with
[barnacles](https://github.com/stefanzhelev/barnacles).

| Path | Purpose |
|---|---|
| `marimo/` | The barnacles project: `barnacles.yaml` and `notebooks/*.py` (created with `barnacles init marimo`) |
| `data/input/` | Small source files (CSV etc.) the notebooks read |
| `data/output/` | Small files the notebooks produce |
| `infra/` | OpenTofu for Cloudflare and GitHub (see [`infra/README.md`](infra/README.md)) |

| Notebook | What it shows | Mode |
|---|---|---|
| [Customer orders](marimo/notebooks/customer_orders.py) | Cleaning, quarantining and reconciling a deliberately messy orders feed with DuckDB | `html` (runs at build time) |
| [Example](marimo/notebooks/example.py) | The barnacles starter notebook | `html-wasm` (runs in the browser) |

Notebooks that read from `data/` use `mode: html` in `barnacles.yaml`: they run once at build time
on your machine. A `html-wasm` notebook runs in the browser and only gets files placed in a
`public/` folder next to it.

## Run locally

```bash
uv sync                               # barnacles, marimo, duckdb, ruff
uv run barnacles serve marimo         # build and serve the gallery at http://127.0.0.1:8000
uv run barnacles edit marimo          # open the notebooks in the marimo editor
uv run barnacles build marimo         # build into marimo/dist/
```

Barnacles exports notebooks in this environment, so a package a notebook imports also goes in
`pyproject.toml`'s `dev` group (as well as the notebook's own `# /// script` header).

## Licence

Code: [MIT](LICENSE). Data in `data/` is synthetic (example.com addresses), CC-BY-4.0.
