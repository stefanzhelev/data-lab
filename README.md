# Data Lab

Small data projects built in several BI tools side by side (marimo, Evidence, Jupyter, Observable),
from the same files in `data/input/`. The marimo notebooks are published as a static gallery with
[barnacles](https://github.com/stefanzhelev/barnacles), with the Evidence site next to it.

| Path | Purpose |
|---|---|
| `bi/` | One folder per BI tool, so the same data can be built and compared in each |
| `bi/marimo/` | The barnacles gallery: `marimo.yaml` and `notebooks/` (sub-folders `practice/` and `energy/` become gallery sections; as if created with `cd bi && barnacles init marimo`) |
| `bi/evidence/` | [Evidence](https://github.com/evidence-dev/evidence) (open-source, v40) versions of the three marimo dashboards (same files, same SQL), dark by default, published at [`/evidence/`](https://lab.stefanzhelev.com/evidence/). The index page is a card gallery (`components/GalleryCard.svelte`) whose images `bi/thumbnails.py` screenshots in CI |
| `bi/jupyter/` | Jupyter notebooks (not in the gallery): the orders pipeline in pandas (`practice_pandas`) and DuckDB (`practice_duckdb`), a timed `pipeline` exercise with its tests in `test_pipeline.py`, and `test_unittest`, a scratch test of `unittest` |
| `bi/observable/` | [Observable Framework](https://observablehq.com/framework/) (v1.13) versions of the same three dashboards (same files, same SQL), dark, published at [`/observable/`](https://lab.stefanzhelev.com/observable/); see [`bi/observable/README.md`](bi/observable/README.md) |
| `bi/thumbnails.py` | Screenshots each page of the Evidence or Observable build for its index-page cards (run in CI) |
| `data/input/` | Small source files (CSV etc.) the notebooks read; sources and licences in [`data/input/README.md`](data/input/README.md) |
| `data/output/` | Small files the notebooks produce |
| `infra/` | OpenTofu for Cloudflare and GitHub (see [`infra/README.md`](infra/README.md)) |

Each notebook also has an Evidence version at the same path under `/evidence/`, built from the matching
`bi/evidence/pages/<folder>/<slug>.md`, and an Observable Framework version under `/observable/`, built
from `bi/observable/src/<folder>/<slug>.md` (folders mirror `bi/marimo/notebooks/`).

| Notebook | What it shows | Mode |
|---|---|---|
| [Customer orders](bi/marimo/notebooks/practice/customer_orders.py) (`practice/`) | Cleaning, quarantining and reconciling a deliberately messy orders feed with DuckDB | `html` (runs at build time) |
| [Electricity transition](bi/marimo/notebooks/energy/energy.py) (`energy/`) | Who is moving off fossil electricity? OWID energy data in 6 charts | `html-wasm` (runs in the browser) |
| [Example](bi/marimo/notebooks/example.py) | The barnacles starter notebook | `html-wasm` (runs in the browser) |

Notebooks that read from `data/` use `mode: html` in `marimo.yaml`: they run once at build time
on your machine. A `html-wasm` notebook runs in the browser and only gets files placed in a
`public/` folder next to it, so `energy.py` reads `data/input/` locally and fetches the same file
from GitHub (`main`) in the browser.

## Run locally

```bash
uv sync                               # barnacles, marimo, duckdb, ruff
uv run barnacles serve bi/marimo      # build and serve the gallery at http://127.0.0.1:8000
uv run barnacles edit bi/marimo       # open the notebooks in the marimo editor
uv run barnacles build bi/marimo      # build into bi/marimo/dist/

cd bi/evidence && npm ci && npm run sources && npm run dev   # the Evidence site (http://localhost:3000/evidence/)
cd bi/observable && npm ci && npm run dev                    # the Observable site (http://127.0.0.1:3000/observable/)

uv run --group jupyter jupyter lab    # the notebooks in bi/jupyter/
uv run --group jupyter jupyter execute bi/jupyter/practice_pandas.ipynb   # run one top to bottom
```

The Jupyter notebooks read `data/input/` and write to `data/output/<notebook>/`, wherever they're started from.

Barnacles exports notebooks in this environment, so a package a notebook imports also goes in
`pyproject.toml`'s `dev` group (as well as the notebook's own `# /// script` header).

## CI/CD

| Workflow | Runs on | Does |
|---|---|---|
| [`ci.yml`](.github/workflows/ci.yml) | every pull request and push to `main` | ruff; `marimo check` on `bi/marimo/notebooks`; runs the Jupyter notebooks in `bi/jupyter` (their tests must pass); builds the barnacles gallery from `bi/marimo`, the Evidence site from `bi/evidence` and the Observable Framework site from `bi/observable`, with card screenshots (`bi/thumbnails.py`) |
| | push to `main` only | deploys the result to Cloudflare Pages (`stefanzhelev-datalab`) at [lab.stefanzhelev.com](https://lab.stefanzhelev.com) |
| [`infra.yml`](.github/workflows/infra.yml) | changes under `infra/` | `tofu fmt` and `tofu validate` only; `tofu apply` runs locally (see [`infra/README.md`](infra/README.md)) |

What ends up where on lab.stefanzhelev.com:

| Path | From |
|---|---|
| `/` | the barnacles gallery (`bi/marimo/marimo.yaml`) |
| `/notebooks/[<folder>/]<slug>/` | each notebook in `bi/marimo/notebooks/`, e.g. `/notebooks/practice/customer-orders/` |
| `/evidence/` | the Evidence site (`bi/evidence`, `basePath: /evidence`): an index page |
| `/evidence/[<folder>/]<slug>/` | one Evidence page per marimo notebook (`bi/evidence/pages/`, same folders and slugs as the gallery) |
| `/observable/` | the Observable Framework site (`bi/observable`, `base: /observable/`): an index page |
| `/observable/[<folder>/]<slug>` | one Observable page per marimo notebook (`bi/observable/src/`, same folders and slugs) |

Cloudflare Pages rejects files over 25 MiB, so the deploy job moves the DuckDB-WASM files that
Evidence and Observable Framework bundle to `data.stefanzhelev.com/lab-assets/<path>` (R2) and points
the sites at them. `bi/jupyter` is not published.

## Licence

Code: [MIT](LICENSE). Data: see [`data/input/README.md`](data/input/README.md) (synthetic orders data and Our World in Data, both CC BY 4.0).
