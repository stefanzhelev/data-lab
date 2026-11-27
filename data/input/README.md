# data/input

| File | Source | Licence |
|---|---|---|
| `orders.csv`, `customers.csv` | Synthetic practice data written for this repo (example.com addresses only) | CC BY 4.0 |
| `owid_energy.csv` | [Our World in Data – Energy](https://github.com/owid/energy-data) (`owid-energy-data.csv`), with each country's continent from [OWID's region list](https://ourworldindata.org/grapher/continents-according-to-our-world-in-data) | CC BY 4.0, © Our World in Data |

## owid_energy.csv

A trimmed copy: countries plus `World`, 1985 onwards, 19 of the 130 columns. Units: electricity in
TWh, `primary_energy_consumption` in TWh, `energy_per_capita` in kWh per person,
`low_carbon_share_elec` in %, `carbon_intensity_elec` in gCO₂ per kWh, `gdp` in international $ (2011 prices).
The latest year is incomplete (fewer countries report), and `gdp` ends in 2022.

Refresh it from the repo root:

```bash
curl -sSLo /tmp/energy.csv https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv
curl -sSLo /tmp/continents.csv "https://ourworldindata.org/grapher/continents-according-to-our-world-in-data.csv?v=1&csvType=full&useColumnShortNames=true"
uv run python - <<'EOF'
import duckdb
duckdb.sql("""
COPY (
  SELECT e.country, e.iso_code, coalesce(r.owid_region, CASE WHEN e.country = 'World' THEN 'World' END) AS region,
         e.year, e.population, e.gdp, e.primary_energy_consumption, e.energy_per_capita,
         e.electricity_generation, e.coal_electricity, e.gas_electricity, e.oil_electricity,
         e.nuclear_electricity, e.hydro_electricity, e.wind_electricity, e.solar_electricity,
         e.other_renewable_electricity, e.low_carbon_share_elec, e.carbon_intensity_elec
  FROM read_csv('/tmp/energy.csv') AS e
  LEFT JOIN read_csv('/tmp/continents.csv') AS r ON r.code = e.iso_code
  WHERE e.year >= 1985 AND e.country <> 'Antarctica'
    AND (e.iso_code IS NOT NULL AND NOT starts_with(e.iso_code, 'OWID_') OR e.country = 'World')
  ORDER BY e.country, e.year
) TO 'data/input/owid_energy.csv' (HEADER)
""")
EOF
```
