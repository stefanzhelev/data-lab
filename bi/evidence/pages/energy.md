---
title: Electricity transition
sidebar_position: 2
---

**Who is moving off fossil electricity?** Electricity generation by source for every country since 1985, from
[Our World in Data](https://github.com/owid/energy-data) (CC BY 4.0). The same file
(`data/input/owid_energy.csv`) and the same SQL drive the
[marimo version](https://lab.stefanzhelev.com/notebooks/energy/) of this page, so the two can be compared chart by chart.

```sql latest
-- The latest year most countries have reported (the newest year is usually incomplete).
SELECT max(year) AS latest_year FROM (
    SELECT year FROM energy.owid_energy
    WHERE country <> 'World' AND electricity_generation IS NOT NULL
    GROUP BY year HAVING count(*) >= 150
)
```

```sql kpi
SELECT
    w.year,
    w.electricity_generation                                          AS generation_twh,
    w.low_carbon_share_elec / 100                                     AS low_carbon_share,
    (w.low_carbon_share_elec - w10.low_carbon_share_elec) / 100       AS low_carbon_change_10y,
    (w.wind_electricity + w.solar_electricity) / w.electricity_generation AS wind_solar_share,
    w.carbon_intensity_elec                                           AS carbon_intensity
FROM ${latest} AS latest
JOIN energy.owid_energy AS w   ON w.country = 'World'   AND w.year = latest.latest_year
JOIN energy.owid_energy AS w10 ON w10.country = 'World' AND w10.year = latest.latest_year - 10
```

<BigValue data={kpi} value=generation_twh title="World electricity, {kpi[0].year}" fmt='#,##0" TWh"'/>
<BigValue data={kpi} value=low_carbon_share title="Low-carbon share" fmt=pct1 comparison=low_carbon_change_10y comparisonFmt='+0.0%;-0.0%' comparisonTitle="in 10 years"/>
<BigValue data={kpi} value=wind_solar_share title="Wind + solar share" fmt=pct1/>
<BigValue data={kpi} value=carbon_intensity title="Carbon intensity" fmt='#,##0" g/kWh"'/>

## 1 · World electricity by source

Solar and wind take off after 2010; coal still grows in absolute terms.

```sql by_source
SELECT year, source, twh FROM (
    UNPIVOT (
        SELECT year,
               coal_electricity AS "Coal", gas_electricity AS "Gas", oil_electricity AS "Oil",
               nuclear_electricity AS "Nuclear", hydro_electricity AS "Hydro",
               wind_electricity AS "Wind", solar_electricity AS "Solar",
               other_renewable_electricity AS "Other renewables"
        FROM energy.owid_energy WHERE country = 'World'
    ) ON COLUMNS(* EXCLUDE (year)) INTO NAME source VALUE twh
)
WHERE year <= (SELECT latest_year FROM ${latest})
ORDER BY year, source
```

<LineChart data={by_source} x=year y=twh series=source xFmt='0' yFmt='#,##0' yAxisTitle="TWh"/>

## 2 · How one country's mix changed

Pick a country: the UK swapped coal for gas and then wind; France has been nuclear since the 1980s.

```sql countries
SELECT country FROM energy.owid_energy
WHERE country <> 'World' AND electricity_generation IS NOT NULL
GROUP BY country ORDER BY country
```

<Dropdown data={countries} name=country value=country title="Country" defaultValue="United Kingdom"/>

```sql mix
SELECT year, source, twh / electricity_generation * 100 AS share FROM (
    UNPIVOT (
        SELECT year, electricity_generation,
               coal_electricity AS "Coal", gas_electricity AS "Gas", oil_electricity AS "Oil",
               nuclear_electricity AS "Nuclear", hydro_electricity AS "Hydro",
               wind_electricity AS "Wind", solar_electricity AS "Solar",
               other_renewable_electricity AS "Other renewables"
        FROM energy.owid_energy WHERE country = '${inputs.country.value}' AND electricity_generation > 0
    ) ON COLUMNS(* EXCLUDE (year, electricity_generation)) INTO NAME source VALUE twh
)
WHERE year <= (SELECT latest_year FROM ${latest})
ORDER BY year, source
```

<AreaChart data={mix} x=year y=share series=source type=stacked xFmt='0' yFmt='0.0' yMax=100 yAxisTitle="Share of generation (%)" title={inputs.country.value}/>

## 3 · Wind and solar leaders

Countries generating at least 10 TWh a year. The leaders are small and windy or sunny, not the largest economies.

```sql leaders
SELECT country, region,
       (wind_electricity + solar_electricity) / electricity_generation * 100 AS wind_solar_share
FROM energy.owid_energy
WHERE year = (SELECT latest_year FROM ${latest}) AND country <> 'World' AND electricity_generation >= 10
ORDER BY wind_solar_share DESC
LIMIT 15
```

<BarChart data={leaders} x=country y=wind_solar_share series=region swapXY=true sort=false yFmt='0.0' yAxisTitle="Wind + solar share of electricity, {kpi[0].year} (%)"/>

## 4 · Energy use rises with wealth

Primary energy per person against GDP per person (log scales), sized by population.
GDP data ends earlier than energy data, so this uses the latest year with GDP.

```sql wealth
WITH g AS (SELECT max(year) AS gdp_year FROM energy.owid_energy WHERE gdp IS NOT NULL)
SELECT country, region, year,
       gdp / population  AS gdp_per_capita,
       energy_per_capita,
       population
FROM energy.owid_energy, g
WHERE year = g.gdp_year AND country <> 'World'
  AND gdp IS NOT NULL AND population IS NOT NULL AND energy_per_capita > 0
ORDER BY population DESC
```

<BubbleChart data={wealth} x=gdp_per_capita y=energy_per_capita size=population series=region tooltipTitle=country
    xType=value xFmt='#,##0' yFmt='#,##0' sizeFmt='#,##0'
    xAxisTitle="GDP per person ($)" yAxisTitle="Energy per person (kWh)"
    echartsOptions={{ xAxis: { type: 'log' }, yAxis: { type: 'log' } }}/>

## 5 · Who decarbonised, and when

Average low-carbon share of electricity (nuclear + renewables) per decade, for the 20 largest producers.
The 1980s cover 1985–89; the 2020s are incomplete.

```sql decades
WITH top AS (
    SELECT country FROM energy.owid_energy
    WHERE year = (SELECT latest_year FROM ${latest}) AND country <> 'World'
    ORDER BY electricity_generation DESC LIMIT 20
)
SELECT country, (floor(year / 10) * 10)::INTEGER::VARCHAR || 's' AS decade,
       avg(low_carbon_share_elec) AS low_carbon_share
FROM energy.owid_energy
WHERE country IN (SELECT country FROM top) AND year <= (SELECT latest_year FROM ${latest})
GROUP BY ALL
ORDER BY country, decade
```

<Heatmap data={decades} x=decade y=country value=low_carbon_share valueFmt='0' min=0 max=100 colorScale={['#f7fcf5', '#00441b']} xAxisPosition=bottom/>

## 6 · The data behind it

Latest year, every country: generation, low-carbon share and carbon intensity.

```sql latest_table
SELECT country, region,
       round(electricity_generation, 1) AS generation_twh,
       round(low_carbon_share_elec, 1)  AS low_carbon_share,
       round(carbon_intensity_elec)     AS carbon_intensity
FROM energy.owid_energy
WHERE year = (SELECT latest_year FROM ${latest}) AND country <> 'World' AND electricity_generation IS NOT NULL
ORDER BY generation_twh DESC
```

<DataTable data={latest_table} rows=10 search=true/>
