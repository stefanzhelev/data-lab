---
title: Example
sidebar_position: 3
---

The Evidence version of the barnacles starter notebook. Moving a slider re-runs the query in your
browser (DuckDB-WASM), like the [marimo version](https://lab.stefanzhelev.com/notebooks/example/)
re-runs its Python cell.

<Slider name=points title="Points" min=1 max=20 defaultValue=8/>
<Slider name=amplitude title="Amplitude" min=1 max=10 defaultValue=5/>

```sql wave
SELECT i AS x, round(${inputs.amplitude} * sin(i / 2), 3) AS y
FROM range(${inputs.points}) AS t(i)
```

<DataTable data={wave} rows=20>
    <Column id=x/>
    <Column id=y fmt='0.000'/>
</DataTable>
