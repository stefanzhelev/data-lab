---
title: Example
---

# Example

The Observable Framework version of the barnacles starter notebook. Moving a slider re-runs the
query in your browser (DuckDB-WASM), like the
[marimo version](https://lab.stefanzhelev.com/notebooks/example/) re-runs its Python cell.

```js
const points = view(Inputs.range([1, 20], {step: 1, value: 8, label: "Points"}));
const amplitude = view(Inputs.range([1, 10], {step: 1, value: 5, label: "Amplitude"}));
```

```sql id=wave
SELECT i::INTEGER AS x, round(${amplitude} * sin(i / 2), 3) AS y
FROM range(${points}::INTEGER) AS t(i)  -- slider values arrive as decimals
```

```js
Inputs.table(wave, {select: false, format: {y: (d) => d.toFixed(3)}})
```
