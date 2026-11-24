# Messy orders

**Question:** how much revenue can we trust from a feed that arrives broken?

**Live:** [dashboard](https://lab.stefanzhelev.com/messy-orders/overview/) ·
[dbt docs](https://lab.stefanzhelev.com/messy-orders/dbt-docs/) ·
[data](https://data.stefanzhelev.com/)

Two CSVs (8 customer rows, 20 order lines) with planted defects: padded and
mixed-case values, `£1,200.00` amounts, `N/A`, `two`, impossible and non-ISO
dates, exact and conflicting duplicates, unknown customers, invalid statuses.

## Approach (dbt on DuckDB)

| Layer | Models | Does |
|---|---|---|
| staging | `stg_customers`, `stg_orders` | read raw as text, trim, normalise case, `try_*` typing; keep `source_row` |
| intermediate | `int_customers_checked`, `int_orders_deduped`, `int_orders_checked` | latest customer wins; drop exact duplicates; tag every rule a line breaks |
| marts | `customers_clean`, `customers_quarantine`, `orders_enriched`, `orders_quarantine`, `daily_revenue` | publish clean data and the rejects, with the raw text and reasons |

`tests/assert_orders_reconcile.sql` fails the build unless every input line is
valid, quarantined or a dropped exact duplicate. Result: 8 valid, 11 quarantined,
1 duplicate dropped, £1,293.75 revenue.

## Run

```bash
cd dbt && uv run dbt build --profiles-dir .      # writes publish/*.parquet
uvx marimo edit --sandbox ../dashboards/overview.py
```

Data is synthetic (example.com addresses), licensed CC-BY-4.0.
