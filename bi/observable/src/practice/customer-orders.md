---
title: Customer orders
---

# Customer orders

**From raw CSV to trusted revenue.** Two small CSV drops (`data/input/customers.csv`,
`data/input/orders.csv`) with about 15 planted defects: padded IDs, `£1,200.00` amounts, impossible
dates, conflicting duplicates, unknown customers. The SQL below cleans what it can, **quarantines
what it can't, with a reason**, and reconciles every input row. Same files and same SQL as the
[marimo](https://lab.stefanzhelev.com/notebooks/practice/customer-orders/) and
[Evidence](https://lab.stefanzhelev.com/evidence/practice/customer-orders/) versions.

```js
// The cleaning steps as views (the same SQL as the marimo notebook), in this page's own database.
// Defining `sql` here makes every ```sql block below query it.
const db = await DuckDBClient.of({
  orders_raw: FileAttachment("../data/orders_raw.parquet"),
  customers_raw: FileAttachment("../data/customers_raw.parquet")
});
for (const view of [
  `CREATE VIEW stg_customers AS
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
       FROM customers_raw
   )`,
  `CREATE VIEW stg_orders AS
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
       FROM orders_raw
   )`,
  // Latest version per customer wins, then rule checks.
  `CREATE VIEW customers_clean AS
   SELECT customer_id, name, email, country, signup_date, updated_at
   FROM (
       SELECT *, concat_ws(';', CASE WHEN customer_id IS NULL THEN 'missing_customer_id' END) AS reject_reason
       FROM stg_customers
       QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY updated_at DESC NULLS LAST, source_row DESC) = 1
   )
   WHERE reject_reason = ''
   ORDER BY customer_id`,
  // Exact duplicate lines are dropped; same order_id with different values is a conflict.
  `CREATE VIEW orders_deduped AS
   SELECT * FROM stg_orders
   QUALIFY row_number() OVER (
       PARTITION BY order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes
       ORDER BY source_row
   ) = 1`,
  `CREATE VIEW orders_checked AS
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
       CASE WHEN NOT EXISTS (SELECT 1 FROM customers_clean AS k WHERE k.customer_id = o.customer_id)
                                                                       THEN 'unknown_customer' END
   ) AS reject_reason
   FROM orders_deduped AS o`,
  `CREATE VIEW orders_enriched AS
   SELECT o.order_id, o.customer_id, c.country, o.order_date, o.amount, o.quantity, o.status, o.notes, o.source_row
   FROM orders_checked AS o LEFT JOIN customers_clean AS c USING (customer_id)
   WHERE o.reject_reason = '' ORDER BY o.order_id`,
  `CREATE VIEW orders_quarantine AS
   SELECT source_row, order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes, reject_reason
   FROM orders_checked WHERE reject_reason <> '' ORDER BY source_row`,
  `CREATE VIEW daily_revenue AS
   SELECT order_date, country, sum(amount) AS revenue, count(DISTINCT order_id) AS orders
   FROM orders_enriched WHERE status <> 'cancelled'
   GROUP BY order_date, country ORDER BY order_date, country NULLS LAST`
]) await db.query(view);
const sql = db.sql.bind(db);
```

```sql id=counts
-- Reconciliation: every raw line is valid, quarantined or a dropped exact duplicate.
SELECT (SELECT count(*) FROM stg_orders)                                          AS rows_in,
       (SELECT count(*) FROM orders_enriched)                                     AS valid,
       (SELECT count(*) FROM orders_quarantine)                                   AS quarantined,
       (SELECT count(*) FROM stg_orders) - (SELECT count(*) FROM orders_deduped)  AS duplicates,
       (SELECT sum(revenue) FROM daily_revenue)::DOUBLE                           AS revenue
```

```js
const c = counts.get(0);
const reconciled = c.rows_in === c.valid + c.quarantined + c.duplicates;
```

<div class="grid grid-cols-4">
  <div class="card"><h2>Order lines in</h2><span class="big">${c.rows_in}</span></div>
  <div class="card"><h2>Valid</h2><span class="big">${c.valid}</span></div>
  <div class="card"><h2>Quarantined</h2><span class="big">${c.quarantined}</span></div>
  <div class="card"><h2>Exact duplicates dropped</h2><span class="big">${c.duplicates}</span></div>
</div>
<div class="grid grid-cols-4">
  <div class="card"><h2>Revenue (excl. cancelled)</h2><span class="big">£${c.revenue.toLocaleString("en-GB", {minimumFractionDigits: 2})}</span></div>
</div>

${reconciled
  ? html`<p>✅ Reconciled: ${c.rows_in} lines in = ${c.valid} valid + ${c.quarantined} quarantined + ${c.duplicates} exact duplicates.</p>`
  : html`<p>❌ Reconciliation failed: ${c.rows_in} lines in, but ${c.valid} valid + ${c.quarantined} quarantined + ${c.duplicates} duplicates.</p>`}

## Why rows were rejected

A line can fail several rules; each reason is counted.

```sql id=reasons
SELECT reason, count(*) AS lines
FROM (SELECT unnest(string_split(reject_reason, ';')) AS reason FROM orders_quarantine)
GROUP BY reason ORDER BY lines DESC, reason
```

```js
Plot.plot({
  width, marginLeft: 210, x: {label: "Order lines", grid: true, ticks: 2, tickFormat: "d"}, y: {label: null},
  marks: [Plot.barX(reasons, {x: "lines", y: "reason", sort: {y: "-x"}, fill: "var(--theme-foreground-focus)", tip: true})]
})
```

## Revenue by day and country

```sql id=daily
-- A text label per day, so the bars sit on evenly spaced categories in date order.
SELECT order_date, strftime(order_date, '%d %b') AS day, coalesce(country, 'unknown') AS country,
       revenue::double AS revenue, orders
FROM daily_revenue ORDER BY order_date, country
```

```js
Plot.plot({
  width, height: 280, color: {legend: true}, x: {label: null}, y: {label: "Revenue (£)", grid: true},
  marks: [Plot.barY(daily, {x: "day", y: "revenue", fill: "country", tip: true}), Plot.ruleY([0])]
})
```

## Quarantine

The raw text is kept exactly as it arrived, so every rejection can be checked.

```sql id=quarantine display
SELECT * FROM orders_quarantine
```
