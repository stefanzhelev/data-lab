---
title: Customer orders
sidebar_position: 1
---

**From raw CSV to trusted revenue.** Two small CSV drops (`data/input/customers.csv`, `data/input/orders.csv`) with about 15 planted
defects: padded IDs, `£1,200.00` amounts, impossible dates, conflicting duplicates, unknown
customers. The SQL below cleans what it can, **quarantines what it can't, with a reason**, and
reconciles every input row. Same file and same SQL as the
[marimo version](https://lab.stefanzhelev.com/notebooks/customer-orders/).

```sql stg_customers
SELECT *,
    try_strptime(signup_date_raw, '%Y-%m-%d')::date   AS signup_date,
    try_strptime(updated_at_raw, '%Y-%m-%dT%H:%M:%S') AS updated_at
FROM (
    SELECT source_row,
        nullif(trim(customer_id), '')    AS customer_id,
        nullif(trim(name), '')           AS name,
        nullif(lower(trim(email)), '')   AS email,
        nullif(upper(trim(country)), '') AS country,
        nullif(trim(signup_date), '')    AS signup_date_raw,
        nullif(trim(updated_at), '')     AS updated_at_raw
    FROM orders.customers_raw
)
```

```sql stg_orders
SELECT *,
    try_strptime(order_date_raw, '%Y-%m-%d')::date                                     AS order_date,
    try_cast(regexp_replace(amount_raw, '[£$€,]', '', 'g') AS decimal(12, 2))          AS amount,
    CASE WHEN regexp_full_match(quantity_raw, '[0-9]+') THEN quantity_raw::integer END AS quantity
FROM (
    SELECT source_row,
        nullif(trim(order_id), '')      AS order_id,
        nullif(trim(customer_id), '')   AS customer_id,
        nullif(trim(order_date), '')    AS order_date_raw,
        nullif(trim(amount), '')        AS amount_raw,
        nullif(trim(quantity), '')      AS quantity_raw,
        nullif(lower(trim(status)), '') AS status,
        nullif(trim(notes), '')         AS notes
    FROM orders.orders_raw
)
```

```sql customers_clean
-- Latest version per customer wins, then rule checks.
SELECT customer_id, name, email, country, signup_date, updated_at
FROM (
    SELECT *, concat_ws(';', CASE WHEN customer_id IS NULL THEN 'missing_customer_id' END) AS reject_reason
    FROM ${stg_customers}
    QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY updated_at DESC NULLS LAST, source_row DESC) = 1
)
WHERE reject_reason = ''
ORDER BY customer_id
```

```sql orders_deduped
-- Exact duplicate lines are dropped; same order_id with different values is a conflict.
SELECT * FROM ${stg_orders}
QUALIFY row_number() OVER (
    PARTITION BY order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes
    ORDER BY source_row
) = 1
```

```sql orders_checked
SELECT o.*, concat_ws(';',
    CASE WHEN count(*) OVER (PARTITION BY o.order_id) > 1          THEN 'conflicting_duplicate_order_id' END,
    CASE WHEN o.order_date_raw IS NULL                              THEN 'missing_order_date' END,
    CASE WHEN o.order_date_raw IS NOT NULL AND o.order_date IS NULL THEN 'unparseable_order_date' END,
    CASE WHEN o.amount IS NULL                                      THEN 'unparseable_amount' END,
    CASE WHEN o.amount < 0 AND o.status IS DISTINCT FROM 'refunded' THEN 'negative_amount' END,
    CASE WHEN o.quantity_raw IS NULL                                THEN 'missing_quantity' END,
    CASE WHEN o.quantity_raw IS NOT NULL AND o.quantity IS NULL     THEN 'unparseable_quantity' END,
    CASE WHEN o.status IS NULL OR o.status NOT IN ('shipped', 'delivered', 'refunded', 'cancelled')
                                                                    THEN 'invalid_status' END,
    CASE WHEN NOT EXISTS (SELECT 1 FROM ${customers_clean} AS k WHERE k.customer_id = o.customer_id)
                                                                    THEN 'unknown_customer' END
) AS reject_reason
FROM ${orders_deduped} AS o
```

```sql orders_enriched
SELECT o.order_id, o.customer_id, c.country, o.order_date, o.amount, o.quantity, o.status, o.notes, o.source_row
FROM ${orders_checked} AS o LEFT JOIN ${customers_clean} AS c USING (customer_id)
WHERE o.reject_reason = '' ORDER BY o.order_id
```

```sql orders_quarantine
SELECT source_row, order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes, reject_reason
FROM ${orders_checked} WHERE reject_reason <> '' ORDER BY source_row
```

```sql daily_revenue
SELECT order_date, country, sum(amount) AS revenue, count(DISTINCT order_id) AS orders
FROM ${orders_enriched} WHERE status <> 'cancelled'
GROUP BY order_date, country ORDER BY order_date, country NULLS LAST
```

```sql counts
-- Reconciliation: every raw line is valid, quarantined or a dropped exact duplicate.
SELECT (SELECT count(*) FROM ${stg_orders})                                              AS rows_in,
       (SELECT count(*) FROM ${orders_enriched})                                         AS valid,
       (SELECT count(*) FROM ${orders_quarantine})                                       AS quarantined,
       (SELECT count(*) FROM ${stg_orders}) - (SELECT count(*) FROM ${orders_deduped})   AS duplicates,
       (SELECT sum(revenue) FROM ${daily_revenue})                                       AS revenue
```

<BigValue data={counts} value=rows_in title="Order lines in"/>
<BigValue data={counts} value=valid title="Valid"/>
<BigValue data={counts} value=quarantined title="Quarantined"/>
<BigValue data={counts} value=duplicates title="Exact duplicates dropped"/>
<BigValue data={counts} value=revenue title="Revenue (excl. cancelled)" fmt='"£"#,##0.00'/>

{#if counts[0].rows_in === counts[0].valid + counts[0].quarantined + counts[0].duplicates}

✅ Reconciled: {counts[0].rows_in} lines in = {counts[0].valid} valid + {counts[0].quarantined} quarantined + {counts[0].duplicates} exact duplicates.

{:else}

❌ Reconciliation failed: {counts[0].rows_in} lines in, but {counts[0].valid} valid + {counts[0].quarantined} quarantined + {counts[0].duplicates} duplicates.

{/if}

## Why rows were rejected

A line can fail several rules; each reason is counted.

```sql reasons
SELECT reason, count(*) AS lines
FROM (SELECT unnest(string_split(reject_reason, ';')) AS reason FROM ${orders_quarantine})
GROUP BY reason ORDER BY lines DESC, reason
```

<BarChart data={reasons} x=reason y=lines swapXY=true sort=false yAxisTitle="Order lines"
    echartsOptions={{ xAxis: { minInterval: 1 } }}/>

## Revenue by day and country

```sql daily
-- A text label per day, so the bars sit on evenly spaced categories in date order.
SELECT order_date, strftime(order_date, '%d %b') AS day, coalesce(country, 'unknown') AS country,
       revenue::double AS revenue, orders
FROM ${daily_revenue} ORDER BY order_date, country
```

<BarChart data={daily} x=day y=revenue series=country sort=false yFmt='"£"#,##0' yAxisTitle="Revenue (£)"/>

## Quarantine

The raw text is kept exactly as it arrived, so every rejection can be checked.

<DataTable data={orders_quarantine} rows=15/>
