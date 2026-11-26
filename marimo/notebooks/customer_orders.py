# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "duckdb", "pandas", "altair"]
# ///

import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium", app_title="Customer orders: from raw CSV to trusted revenue")


@app.cell
def _():
    import altair as alt
    import duckdb
    import marimo as mo

    # <repo>/marimo/notebooks/this.py -> <repo>/data/input
    INPUT = mo.notebook_dir().parents[1] / "data" / "input"
    return INPUT, alt, duckdb, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Customer orders: from raw CSV to trusted revenue

    Two small CSV drops (`data/input/customers.csv`, `data/input/orders.csv`) with about
    15 planted defects: padded IDs, `£1,200.00` amounts, impossible dates, conflicting
    duplicates, unknown customers. The SQL below cleans what it can, **quarantines what it
    can't, with a reason**, and reconciles every input row.
    """)
    return


@app.cell
def _(INPUT, duckdb):
    VALID_STATUSES = ("shipped", "delivered", "refunded", "cancelled")

    def _csv(name):
        path = (INPUT / f"{name}.csv").as_posix().replace("'", "''")
        return f"read_csv('{path}', header = true, all_varchar = true)"

    # Raw text in, nothing coerced; source_row is the CSV line number.
    duckdb.sql(f"CREATE OR REPLACE TABLE orders_raw AS SELECT * FROM {_csv('orders')}")
    duckdb.sql(f"""
    CREATE OR REPLACE TABLE stg_customers AS
    WITH raw AS (SELECT row_number() OVER () + 1 AS source_row, * FROM {_csv("customers")}),
    tidy AS (
        SELECT source_row,
            nullif(trim(customer_id), '')    AS customer_id,
            nullif(trim(name), '')           AS name,
            nullif(lower(trim(email)), '')   AS email,
            nullif(upper(trim(country)), '') AS country,
            nullif(trim(signup_date), '')    AS signup_date_raw,
            nullif(trim(updated_at), '')     AS updated_at_raw
        FROM raw
    )
    SELECT *,
        try_strptime(signup_date_raw, '%Y-%m-%d')::date   AS signup_date,
        try_strptime(updated_at_raw, '%Y-%m-%dT%H:%M:%S') AS updated_at
    FROM tidy
    """)
    duckdb.sql("""
    CREATE OR REPLACE TABLE stg_orders AS
    WITH raw AS (SELECT row_number() OVER () + 1 AS source_row, * FROM orders_raw),
    tidy AS (
        SELECT source_row,
            nullif(trim(order_id), '')      AS order_id,
            nullif(trim(customer_id), '')   AS customer_id,
            nullif(trim(order_date), '')    AS order_date_raw,
            nullif(trim(amount), '')        AS amount_raw,
            nullif(trim(quantity), '')      AS quantity_raw,
            nullif(lower(trim(status)), '') AS status,
            nullif(trim(notes), '')         AS notes
        FROM raw
    )
    SELECT *,
        try_strptime(order_date_raw, '%Y-%m-%d')::date                                     AS order_date,
        try_cast(regexp_replace(amount_raw, '[£$€,]', '', 'g') AS decimal(12, 2))          AS amount,
        CASE WHEN regexp_full_match(quantity_raw, '[0-9]+') THEN quantity_raw::integer END AS quantity
    FROM tidy
    """)

    # Latest version per customer wins, then rule checks.
    duckdb.sql("""
    CREATE OR REPLACE TABLE customers_checked AS
    SELECT *, concat_ws(';', CASE WHEN customer_id IS NULL THEN 'missing_customer_id' END) AS reject_reason
    FROM stg_customers
    QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY updated_at DESC NULLS LAST, source_row DESC) = 1
    """)
    duckdb.sql("""
    CREATE OR REPLACE TABLE customers_clean AS
    SELECT customer_id, name, email, country, signup_date, updated_at
    FROM customers_checked WHERE reject_reason = '' ORDER BY customer_id
    """)

    # Exact duplicate lines are dropped; same order_id with different values is a conflict.
    duckdb.sql("""
    CREATE OR REPLACE TABLE orders_deduped AS
    SELECT * FROM stg_orders
    QUALIFY row_number() OVER (
        PARTITION BY order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes
        ORDER BY source_row
    ) = 1
    """)
    _statuses = ", ".join(f"'{s}'" for s in VALID_STATUSES)
    duckdb.sql(f"""
    CREATE OR REPLACE TABLE orders_checked AS
    SELECT o.*, concat_ws(';',
        CASE WHEN count(*) OVER (PARTITION BY o.order_id) > 1          THEN 'conflicting_duplicate_order_id' END,
        CASE WHEN o.order_date_raw IS NULL                              THEN 'missing_order_date' END,
        CASE WHEN o.order_date_raw IS NOT NULL AND o.order_date IS NULL THEN 'unparseable_order_date' END,
        CASE WHEN o.amount IS NULL                                      THEN 'unparseable_amount' END,
        CASE WHEN o.amount < 0 AND o.status IS DISTINCT FROM 'refunded' THEN 'negative_amount' END,
        CASE WHEN o.quantity_raw IS NULL                                THEN 'missing_quantity' END,
        CASE WHEN o.quantity_raw IS NOT NULL AND o.quantity IS NULL     THEN 'unparseable_quantity' END,
        CASE WHEN o.status IS NULL OR o.status NOT IN ({_statuses})    THEN 'invalid_status' END,
        CASE WHEN NOT EXISTS (SELECT 1 FROM customers_clean AS k WHERE k.customer_id = o.customer_id)
                                                                        THEN 'unknown_customer' END
    ) AS reject_reason
    FROM orders_deduped AS o
    """)
    duckdb.sql("""
    CREATE OR REPLACE TABLE orders_enriched AS
    SELECT o.order_id, o.customer_id, c.country, o.order_date, o.amount, o.quantity, o.status, o.notes, o.source_row
    FROM orders_checked AS o LEFT JOIN customers_clean AS c USING (customer_id)
    WHERE o.reject_reason = '' ORDER BY o.order_id
    """)
    duckdb.sql("""
    CREATE OR REPLACE TABLE orders_quarantine AS
    SELECT source_row, order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes, reject_reason
    FROM orders_checked WHERE reject_reason <> '' ORDER BY source_row
    """)
    duckdb.sql("""
    CREATE OR REPLACE TABLE daily_revenue AS
    SELECT order_date, country, sum(amount) AS revenue, count(DISTINCT order_id) AS orders
    FROM orders_enriched WHERE status <> 'cancelled'
    GROUP BY order_date, country ORDER BY order_date, country NULLS LAST
    """)

    # Reconciliation: every raw line is valid, quarantined or a dropped exact duplicate.
    counts = dict(
        zip(
            ["rows_in", "valid", "quarantined", "duplicates", "revenue"],
            duckdb.sql("""
            SELECT (SELECT count(*) FROM stg_orders),
                   (SELECT count(*) FROM orders_enriched),
                   (SELECT count(*) FROM orders_quarantine),
                   (SELECT count(*) FROM stg_orders) - (SELECT count(*) FROM orders_deduped),
                   (SELECT sum(revenue) FROM daily_revenue)
            """).fetchall()[0],
            strict=True,
        )
    )
    assert counts["rows_in"] == counts["valid"] + counts["quarantined"] + counts["duplicates"], counts
    return (counts,)


@app.cell
def _(counts, mo):
    mo.hstack(
        [
            mo.stat(counts["rows_in"], label="Order lines in"),
            mo.stat(counts["valid"], label="Valid", bordered=True),
            mo.stat(counts["quarantined"], label="Quarantined", bordered=True),
            mo.stat(counts["duplicates"], label="Exact duplicates dropped", bordered=True),
            mo.stat(f"£{counts['revenue']:,.2f}", label="Revenue (excl. cancelled)", bordered=True),
        ],
        widths="equal",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Why rows were rejected
    A line can fail several rules; each reason is counted.
    """)
    return


@app.cell
def _(alt, counts, duckdb):
    _reasons = duckdb.sql("""
        SELECT reason, count(*) AS lines
        FROM (SELECT unnest(string_split(reject_reason, ';')) AS reason FROM orders_quarantine)
        GROUP BY reason ORDER BY lines DESC, reason
    """).df()
    (
        alt.Chart(_reasons)
        .mark_bar()
        .encode(
            x=alt.X("lines:Q", title="Order lines", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("reason:N", sort="-x", title=None),
            tooltip=["reason", "lines"],
        )
        .properties(height=220, width="container")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Revenue by day and country
    """)
    return


@app.cell
def _(alt, counts, duckdb):
    _daily = duckdb.sql("""
        SELECT order_date, coalesce(country, 'unknown') AS country, revenue::double AS revenue, orders
        FROM daily_revenue ORDER BY order_date
    """).df()
    (
        alt.Chart(_daily)
        .mark_bar()
        .encode(
            x=alt.X("order_date:T", title=None, timeUnit="yearmonthdate"),
            y=alt.Y("revenue:Q", title="Revenue (£)"),
            color=alt.Color("country:N", title="Country"),
            tooltip=["order_date:T", "country:N", "revenue:Q", "orders:Q"],
        )
        .properties(height=240, width="container")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Quarantine
    The raw text is kept exactly as it arrived, so every rejection can be checked.
    """)
    return


@app.cell
def _(counts, duckdb, mo):
    mo.ui.table(
        duckdb.sql("SELECT * FROM orders_quarantine ORDER BY source_row").df(),
        selection=None,
        page_size=15,
    )
    return


if __name__ == "__main__":
    app.run()
