# Observable

[Observable Framework](https://observablehq.com/framework/) (v1.13) versions of the marimo
dashboards, published at [lab.stefanzhelev.com/observable/](https://lab.stefanzhelev.com/observable/).
Same files (`data/input/`) and the same SQL as `bi/marimo` and `bi/evidence`.

| Path | What |
|---|---|
| `observablehq.config.js` | base `/observable/`, dark theme, Data Lab header, sidebar, no footer; `.py` loaders run with the repo's uv environment |
| `src/data/*.parquet.py` | data loaders: DuckDB reads `data/input/*.csv` at build time (orders and customers as raw text, like `bi/evidence/sources`) |
| `src/index.md` | card gallery; images from `bi/thumbnails.py observable` in CI |
| `src/practice/customer-orders.md` | the cleaning SQL as DuckDB views, queried by ```` ```sql ```` blocks |
| `src/energy/energy.md`, `src/example.md` | the other two dashboards |

```bash
npm ci
npm run dev      # http://127.0.0.1:3000/observable/ (cards show a letter: thumbnails are made in CI)
npm run build    # dist/
```
