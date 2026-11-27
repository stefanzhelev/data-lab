---
title: Electricity transition
sql:
  energy: ../data/owid_energy.parquet
---

# Electricity transition

**Who is moving off fossil electricity?** Electricity generation by source for every country since
1985, from [Our World in Data](https://github.com/owid/energy-data) (CC BY 4.0). The same file
(`data/input/owid_energy.csv`) and the same SQL drive the
[marimo](https://lab.stefanzhelev.com/notebooks/energy/energy/) and
[Evidence](https://lab.stefanzhelev.com/evidence/energy/energy/) versions.

```sql id=latest
-- The latest year most countries have reported (the newest year is usually incomplete).
SELECT max(year) AS latest_year FROM (
    SELECT year FROM energy
    WHERE country <> 'World' AND electricity_generation IS NOT NULL
    GROUP BY year HAVING count(*) >= 150
)
```

```js
const latestYear = latest.get(0).latest_year;
```

```sql id=kpi
SELECT
    w.year,
    w.electricity_generation                                          AS generation_twh,
    w.low_carbon_share_elec                                           AS low_carbon_share,
    w.low_carbon_share_elec - w10.low_carbon_share_elec               AS low_carbon_change_10y,
    (w.wind_electricity + w.solar_electricity) / w.electricity_generation * 100 AS wind_solar_share,
    w.carbon_intensity_elec                                           AS carbon_intensity
FROM energy AS w
JOIN energy AS w10 ON w10.country = 'World' AND w10.year = w.year - 10
WHERE w.country = 'World' AND w.year = ${latestYear}
```

```js
const k = kpi.get(0);
const fmt = (x, d = 0) => x.toLocaleString("en-GB", {minimumFractionDigits: d, maximumFractionDigits: d});
```

<div class="grid grid-cols-4">
  <div class="card"><h2>World electricity, ${k.year}</h2><span class="big">${fmt(k.generation_twh)} TWh</span></div>
  <div class="card"><h2>Low-carbon share</h2><span class="big">${fmt(k.low_carbon_share, 1)}%</span>
    <div class="green">▲ ${fmt(k.low_carbon_change_10y, 1)} pts in 10 years</div></div>
  <div class="card"><h2>Wind + solar share</h2><span class="big">${fmt(k.wind_solar_share, 1)}%</span></div>
  <div class="card"><h2>Carbon intensity</h2><span class="big">${fmt(k.carbon_intensity)} g/kWh</span></div>
</div>

## 1 · World electricity by source

Solar and wind take off after 2010; coal still grows in absolute terms.

```sql id=by_source
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
WHERE year <= ${latestYear}
ORDER BY year, source
```

```js
Plot.plot({
  width, height: 320, color: {legend: true}, x: {label: null, tickFormat: "d"}, y: {label: "TWh", grid: true},
  marks: [Plot.lineY(by_source, {x: "year", y: "twh", stroke: "source", tip: true})]
})
```

## 2 · How one country's mix changed

Pick a country: the UK swapped coal for gas and then wind; France has been nuclear since the 1980s.

```sql id=countries
SELECT country FROM energy
WHERE country <> 'World' AND electricity_generation IS NOT NULL
GROUP BY country ORDER BY country
```

```js
const country = view(Inputs.select(Array.from(countries, (d) => d.country), {value: "United Kingdom", label: "Country"}));
```

```sql id=mix
SELECT year, source, twh / electricity_generation * 100 AS share FROM (
    UNPIVOT (
        SELECT year, electricity_generation,
               coal_electricity AS "Coal", gas_electricity AS "Gas", oil_electricity AS "Oil",
               nuclear_electricity AS "Nuclear", hydro_electricity AS "Hydro",
               wind_electricity AS "Wind", solar_electricity AS "Solar",
               other_renewable_electricity AS "Other renewables"
        FROM energy WHERE country = ${country} AND electricity_generation > 0
    ) ON COLUMNS(* EXCLUDE (year, electricity_generation)) INTO NAME source VALUE twh
)
WHERE year <= ${latestYear}
ORDER BY year, source
```

```js
Plot.plot({
  width, height: 320, title: country, color: {legend: true},
  x: {label: null, tickFormat: "d"}, y: {label: "Share of generation (%)", domain: [0, 100], grid: true},
  marks: [Plot.areaY(mix, {x: "year", y: "share", fill: "source", tip: true}), Plot.ruleY([0])]
})
```

## 3 · Wind and solar leaders

Countries generating at least 10 TWh a year. The leaders are small and windy or sunny, not the largest economies.

```sql id=leaders
SELECT country, region,
       (wind_electricity + solar_electricity) / electricity_generation * 100 AS wind_solar_share
FROM energy
WHERE year = ${latestYear} AND country <> 'World' AND electricity_generation >= 10
ORDER BY wind_solar_share DESC
LIMIT 15
```

```js
Plot.plot({
  width, marginLeft: 110, color: {legend: true},
  x: {label: `Wind + solar share of electricity, ${latestYear} (%)`, grid: true}, y: {label: null},
  marks: [Plot.barX(leaders, {x: "wind_solar_share", y: "country", fill: "region", sort: {y: "-x"}, tip: true})]
})
```

## 4 · Energy use rises with wealth

Primary energy per person against GDP per person (log scales), sized by population.
GDP data ends earlier than energy data, so this uses the latest year with GDP.

```sql id=wealth
WITH g AS (SELECT max(year) AS gdp_year FROM energy WHERE gdp IS NOT NULL)
SELECT country, region, year,
       gdp / population  AS gdp_per_capita,
       energy_per_capita,
       population
FROM energy, g
WHERE year = g.gdp_year AND country <> 'World'
  AND gdp IS NOT NULL AND population IS NOT NULL AND energy_per_capita > 0
ORDER BY population DESC
```

```js
Plot.plot({
  width, height: 400, color: {legend: true}, r: {range: [1, 30]},
  x: {type: "log", label: "GDP per person ($)", grid: true}, y: {type: "log", label: "Energy per person (kWh)", grid: true},
  marks: [Plot.dot(wealth, {x: "gdp_per_capita", y: "energy_per_capita", r: "population", fill: "region", fillOpacity: 0.7, title: "country", tip: true})]
})
```

## 5 · Who decarbonised, and when

Average low-carbon share of electricity (nuclear + renewables) per decade, for the 20 largest producers.
The 1980s cover 1985–89; the 2020s are incomplete.

```sql id=decades
WITH top AS (
    SELECT country FROM energy
    WHERE year = ${latestYear} AND country <> 'World'
    ORDER BY electricity_generation DESC LIMIT 20
)
SELECT country, (floor(year / 10) * 10)::INTEGER::VARCHAR || 's' AS decade,
       avg(low_carbon_share_elec) AS low_carbon_share
FROM energy
WHERE country IN (SELECT country FROM top) AND year <= ${latestYear}
GROUP BY ALL
ORDER BY country, decade
```

```js
Plot.plot({
  width, marginLeft: 100, padding: 0.05, x: {label: null}, y: {label: null},
  color: {scheme: "greens", domain: [0, 100], legend: true, label: "Low-carbon %"},
  marks: [
    Plot.cell(decades, {x: "decade", y: "country", fill: "low_carbon_share", tip: true}),
    Plot.text(decades, {x: "decade", y: "country", text: (d) => d.low_carbon_share?.toFixed(0), fill: (d) => d.low_carbon_share > 50 ? "white" : "black"})
  ]
})
```

## 6 · The data behind it

Latest year, every country: generation, low-carbon share and carbon intensity.

```sql id=latest_table display
SELECT country, region,
       round(electricity_generation, 1) AS generation_twh,
       round(low_carbon_share_elec, 1)  AS low_carbon_share,
       round(carbon_intensity_elec)     AS carbon_intensity
FROM energy
WHERE year = ${latestYear} AND country <> 'World' AND electricity_generation IS NOT NULL
ORDER BY generation_twh DESC
```
