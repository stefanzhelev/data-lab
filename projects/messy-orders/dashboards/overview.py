# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.25",
#     "duckdb",
#     "sqlglot",
#     "pandas",
#     "altair",
#     # Not on PyPI: the browser installs the wheel the site serves (built by
#     # deploy-pages.yml, which fails if this file is missing). Keep the version
#     # in sync with libs/datalab/pyproject.toml.
#     "stefanzhelev-datalab @ https://lab.stefanzhelev.com/wheels/stefanzhelev_datalab-0.1.0-py3-none-any.whl",
# ]
#
# # Locally (and when CI pre-renders) uv uses the repo copy instead of the URL.
# [tool.uv.sources]
# stefanzhelev-datalab = { path = "../../../libs/datalab", editable = true }
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="medium",
    app_title="Messy orders: from raw CSV to trusted revenue",
)


@app.cell
async def _():
    import os
    import sys

    if sys.platform == "emscripten":
        # In the browser the library isn't on PyPI: the site serves the wheel
        # it was built with (deploy-pages.yml). Keep the version in sync with
        # libs/datalab/pyproject.toml; the deploy fails if this file is missing.
        import micropip

        await micropip.install(
            "https://lab.stefanzhelev.com/wheels/stefanzhelev_datalab-0.1.0-py3-none-any.whl"
        )

    import altair as alt
    import marimo as mo
    from stefanzhelev_datalab import load, sidebar

    # Override locally to test against a dev bucket or a local http.server.
    DATA_URL = os.environ.get("DATA_URL", "https://data.stefanzhelev.com/messy-orders")
    return DATA_URL, alt, load, mo, sidebar


@app.cell(hide_code=True)
def _(sidebar):
    sidebar("messy-orders")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Messy orders: from raw CSV to trusted revenue

    Two small CSV drops with about 15 planted defects (padded IDs, `£1,200.00`
    amounts, impossible dates, conflicting duplicates, unknown customers). A dbt
    pipeline on DuckDB cleans what it can, **quarantines what it can't, with a
    reason**, and reconciles every input row before publishing. Everything below
    runs in your browser.
    """)
    return


@app.cell
async def _(DATA_URL, load):
    for _table in ["customers_clean", "orders_enriched", "orders_quarantine", "daily_revenue"]:
        await load(f"{DATA_URL}/{_table}.parquet", _table)
    _ = await load(f"{DATA_URL}/raw/orders.csv", "orders_raw", all_varchar=True)  # no output
    return


@app.cell
def _(mo):
    _counts = mo.sql(
        """
        SELECT
            (SELECT count(*) FROM orders_raw)        AS rows_in,
            (SELECT count(*) FROM orders_enriched)   AS valid,
            (SELECT count(*) FROM orders_quarantine) AS quarantined,
            (SELECT sum(revenue) FROM daily_revenue) AS revenue
        """,
        output=False,
    ).iloc[0]
    _dropped = int(_counts.rows_in - _counts.valid - _counts.quarantined)
    mo.hstack(
        [
            mo.stat(int(_counts.rows_in), label="Order lines in"),
            mo.stat(int(_counts.valid), label="Valid", bordered=True),
            mo.stat(int(_counts.quarantined), label="Quarantined", bordered=True),
            mo.stat(_dropped, label="Exact duplicates dropped", bordered=True),
            mo.stat(f"£{_counts.revenue:,.2f}", label="Revenue (excl. cancelled)", bordered=True),
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
def _(alt, mo):
    _reasons = mo.sql(
        """
        SELECT reason, count(*) AS lines
        FROM (SELECT unnest(string_split(reject_reason, ';')) AS reason FROM orders_quarantine)
        GROUP BY reason
        ORDER BY lines DESC, reason
        """,
        output=False,
    )
    mo.ui.altair_chart(
        alt.Chart(_reasons)
        .mark_bar()
        .encode(
            x=alt.X("lines:Q", title="Order lines", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("reason:N", sort="-x", title=None),
            tooltip=["reason", "lines"],
        )
        .properties(height=220)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Revenue by day
    """)
    return


@app.cell
def _(mo):
    _countries = mo.sql(
        "SELECT DISTINCT coalesce(country, 'unknown') AS c FROM daily_revenue ORDER BY c",
        output=False,
    )["c"].tolist()
    country = mo.ui.dropdown(options=["All", *_countries], value="All", label="Country")
    country
    return (country,)


@app.cell
def _(alt, country, mo):
    _where = "" if country.value == "All" else f"WHERE coalesce(country, 'unknown') = '{country.value}'"
    _daily = mo.sql(
        f"""
        SELECT order_date, sum(revenue) AS revenue, sum(orders) AS orders
        FROM daily_revenue {_where}
        GROUP BY order_date
        ORDER BY order_date
        """,
        output=False,
    )
    mo.ui.altair_chart(
        alt.Chart(_daily)
        .mark_bar()
        .encode(
            x=alt.X("order_date:T", title=None, timeUnit="yearmonthdate"),
            y=alt.Y("revenue:Q", title="Revenue (£)"),
            tooltip=["order_date:T", "revenue:Q", "orders:Q"],
        )
        .properties(height=240)
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
def _(mo):
    mo.ui.table(
        mo.sql("SELECT * FROM orders_quarantine ORDER BY source_row", output=False),
        selection=None,
        page_size=15,
    )
    return


if __name__ == "__main__":
    app.run()
