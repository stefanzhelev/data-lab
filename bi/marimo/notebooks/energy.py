# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "duckdb", "pandas", "altair", "sqlglot"]
# ///

import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium", app_title="Who is moving off fossil electricity?")


@app.cell
def _():
    import sys

    import altair as alt
    import duckdb
    import marimo as mo
    import pandas as pd

    # One copy of the data: data/input/owid_energy.csv. Locally it's read from disk; in the
    # browser (WASM export) there's no repo, so the same committed file is fetched from GitHub.
    _name = "owid_energy.csv"
    if sys.platform == "emscripten":
        SOURCE = f"https://raw.githubusercontent.com/stefanzhelev/data-lab/main/data/input/{_name}"
    else:
        SOURCE = str(mo.notebook_dir().parents[2] / "data" / "input" / _name)

    # pandas does the download (DuckDB has no network access in the browser), then DuckDB owns the table.
    duckdb.register("energy_csv", pd.read_csv(SOURCE))
    duckdb.sql("CREATE OR REPLACE TABLE energy AS SELECT * FROM energy_csv")
    return alt, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Who is moving off fossil electricity?

    Electricity generation by source for every country since 1985, from
    [Our World in Data](https://github.com/owid/energy-data) (CC BY 4.0). The same file and the
    same SQL drive the [Evidence version](../../evidence/) of this page, so the two can be
    compared chart by chart.
    """)
    return


@app.cell
def _(mo):
    # The latest year most countries have reported (the newest year is usually incomplete).
    kpi = mo.sql(
        """
        WITH latest AS (
            SELECT max(year) AS latest_year FROM (
                SELECT year FROM energy
                WHERE country <> 'World' AND electricity_generation IS NOT NULL
                GROUP BY year HAVING count(*) >= 150
            )
        )
        SELECT
            w.year,
            w.electricity_generation                                          AS generation_twh,
            w.low_carbon_share_elec                                           AS low_carbon_share,
            w.low_carbon_share_elec - w10.low_carbon_share_elec               AS low_carbon_change_10y,
            (w.wind_electricity + w.solar_electricity) / w.electricity_generation * 100 AS wind_solar_share,
            w.carbon_intensity_elec                                           AS carbon_intensity
        FROM latest
        JOIN energy AS w   ON w.country = 'World'   AND w.year = latest.latest_year
        JOIN energy AS w10 ON w10.country = 'World' AND w10.year = latest.latest_year - 10
        """,
        output=False,
    )
    k = {c: kpi[c][0] for c in kpi.columns}
    LATEST_YEAR = int(k["year"])
    mo.hstack(
        [
            mo.stat(f"{k['generation_twh']:,.0f} TWh", label=f"World electricity, {LATEST_YEAR}"),
            mo.stat(
                f"{k['low_carbon_share']:.1f}%",
                label="Low-carbon share",
                caption=f"{k['low_carbon_change_10y']:+.1f} pts in 10 years",
                direction="increase" if k["low_carbon_change_10y"] > 0 else "decrease",
                bordered=True,
            ),
            mo.stat(f"{k['wind_solar_share']:.1f}%", label="Wind + solar share", bordered=True),
            mo.stat(f"{k['carbon_intensity']:.0f} g/kWh", label="Carbon intensity", bordered=True),
        ],
        widths="equal",
    )
    return (LATEST_YEAR,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1 · World electricity by source
    Solar and wind take off after 2010; coal still grows in absolute terms.
    """)
    return


@app.cell
def _(LATEST_YEAR, alt, mo):
    by_source = mo.sql(
        f"""
        SELECT year, source, twh FROM (
            UNPIVOT (
                SELECT year,
                       coal_electricity AS "Coal", gas_electricity AS "Gas", oil_electricity AS "Oil",
                       nuclear_electricity AS "Nuclear", hydro_electricity AS "Hydro",
                       wind_electricity AS "Wind", solar_electricity AS "Solar",
                       other_renewable_electricity AS "Other renewables"
                FROM energy WHERE country = 'World'
            ) ON COLUMNS(* EXCLUDE (year)) INTO NAME source VALUE twh
        )
        WHERE year <= {LATEST_YEAR}
        ORDER BY year, source
        """,
        output=False,
    )
    (
        alt.Chart(by_source)
        .mark_line()
        .encode(
            x=alt.X("year:Q", title=None, axis=alt.Axis(format="d")),
            y=alt.Y("twh:Q", title="TWh"),
            color=alt.Color("source:N", title="Source"),
            tooltip=["year:Q", "source:N", alt.Tooltip("twh:Q", format=",.0f")],
        )
        .properties(height=300, width="container")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2 · How one country's mix changed
    Pick a country: the UK swapped coal for gas and then wind; France has been nuclear since the 1980s.
    """)
    return


@app.cell
def _(mo):
    _countries = mo.sql(
        """
        SELECT country FROM energy
        WHERE country <> 'World' AND electricity_generation IS NOT NULL
        GROUP BY country ORDER BY country
        """,
        output=False,
    )
    country = mo.ui.dropdown(
        options=list(_countries["country"]), value="United Kingdom", label="Country", searchable=True
    )
    country
    return (country,)


@app.cell
def _(LATEST_YEAR, alt, country, mo):
    _name = country.value.replace("'", "''")
    mix = mo.sql(
        f"""
        SELECT year, source, twh / electricity_generation * 100 AS share FROM (
            UNPIVOT (
                SELECT year, electricity_generation,
                       coal_electricity AS "Coal", gas_electricity AS "Gas", oil_electricity AS "Oil",
                       nuclear_electricity AS "Nuclear", hydro_electricity AS "Hydro",
                       wind_electricity AS "Wind", solar_electricity AS "Solar",
                       other_renewable_electricity AS "Other renewables"
                FROM energy WHERE country = '{_name}' AND electricity_generation > 0
            ) ON COLUMNS(* EXCLUDE (year, electricity_generation)) INTO NAME source VALUE twh
        )
        WHERE year <= {LATEST_YEAR}
        ORDER BY year, source
        """,
        output=False,
    )
    (
        alt.Chart(mix)
        .mark_area()
        .encode(
            x=alt.X("year:Q", title=None, axis=alt.Axis(format="d")),
            y=alt.Y("share:Q", title="Share of generation (%)", stack="zero", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("source:N", title="Source"),
            tooltip=["year:Q", "source:N", alt.Tooltip("share:Q", format=".1f")],
        )
        .properties(height=300, width="container", title=country.value)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3 · Wind and solar leaders
    Countries generating at least 10 TWh a year. The leaders are small and windy or sunny, not the largest economies.
    """)
    return


@app.cell
def _(LATEST_YEAR, alt, mo):
    leaders = mo.sql(
        f"""
        SELECT country, region,
               (wind_electricity + solar_electricity) / electricity_generation * 100 AS wind_solar_share
        FROM energy
        WHERE year = {LATEST_YEAR} AND country <> 'World' AND electricity_generation >= 10
        ORDER BY wind_solar_share DESC
        LIMIT 15
        """,
        output=False,
    )
    (
        alt.Chart(leaders)
        .mark_bar()
        .encode(
            x=alt.X("wind_solar_share:Q", title=f"Wind + solar share of electricity, {LATEST_YEAR} (%)"),
            y=alt.Y("country:N", sort="-x", title=None),
            color=alt.Color("region:N", title="Region"),
            tooltip=["country:N", "region:N", alt.Tooltip("wind_solar_share:Q", format=".1f")],
        )
        .properties(height=360, width="container")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 4 · Energy use rises with wealth
    Primary energy per person against GDP per person (log scales), sized by population.
    GDP data ends earlier than energy data, so this uses the latest year with GDP.
    """)
    return


@app.cell
def _(alt, mo):
    wealth = mo.sql(
        """
        WITH g AS (SELECT max(year) AS gdp_year FROM energy WHERE gdp IS NOT NULL)
        SELECT country, region, year,
               gdp / population  AS gdp_per_capita,
               energy_per_capita,
               population
        FROM energy, g
        WHERE year = g.gdp_year AND country <> 'World'
          AND gdp IS NOT NULL AND population IS NOT NULL AND energy_per_capita > 0
        ORDER BY population DESC
        """,
        output=False,
    )
    (
        alt.Chart(wealth)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X("gdp_per_capita:Q", title="GDP per person ($)", scale=alt.Scale(type="log")),
            y=alt.Y("energy_per_capita:Q", title="Energy per person (kWh)", scale=alt.Scale(type="log")),
            size=alt.Size("population:Q", legend=None, scale=alt.Scale(range=[15, 1500])),
            color=alt.Color("region:N", title="Region"),
            tooltip=[
                "country:N",
                "year:Q",
                alt.Tooltip("gdp_per_capita:Q", format=",.0f"),
                alt.Tooltip("energy_per_capita:Q", format=",.0f"),
                alt.Tooltip("population:Q", format=",.0f"),
            ],
        )
        .properties(height=380, width="container")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 5 · Who decarbonised, and when
    Average low-carbon share of electricity (nuclear + renewables) per decade, for the 20 largest producers.
    The 1980s cover 1985–89; the 2020s are incomplete.
    """)
    return


@app.cell
def _(LATEST_YEAR, alt, mo):
    decades = mo.sql(
        f"""
        WITH top AS (
            SELECT country FROM energy
            WHERE year = {LATEST_YEAR} AND country <> 'World'
            ORDER BY electricity_generation DESC LIMIT 20
        )
        SELECT country, (floor(year / 10) * 10)::INTEGER::VARCHAR || 's' AS decade,
               avg(low_carbon_share_elec) AS low_carbon_share
        FROM energy
        WHERE country IN (SELECT country FROM top) AND year <= {LATEST_YEAR}
        GROUP BY ALL
        ORDER BY country, decade
        """,
        output=False,
    )
    (
        alt.Chart(decades)
        .mark_rect()
        .encode(
            x=alt.X("decade:O", title=None),
            y=alt.Y("country:N", title=None),
            color=alt.Color(
                "low_carbon_share:Q", title="Low-carbon %", scale=alt.Scale(scheme="greens", domain=[0, 100])
            ),
            tooltip=["country:N", "decade:O", alt.Tooltip("low_carbon_share:Q", format=".1f")],
        )
        .properties(height=440, width="container")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 6 · The data behind it
    Latest year, every country: generation, low-carbon share and carbon intensity.
    """)
    return


@app.cell
def _(LATEST_YEAR, mo):
    mo.ui.table(
        mo.sql(
            f"""
            SELECT country, region,
                   round(electricity_generation, 1) AS generation_twh,
                   round(low_carbon_share_elec, 1)  AS low_carbon_share,
                   round(carbon_intensity_elec)     AS carbon_intensity
            FROM energy
            WHERE year = {LATEST_YEAR} AND country <> 'World' AND electricity_generation IS NOT NULL
            ORDER BY generation_twh DESC
            """,
            output=False,
        ),
        selection=None,
        page_size=10,
    )
    return


if __name__ == "__main__":
    app.run()
