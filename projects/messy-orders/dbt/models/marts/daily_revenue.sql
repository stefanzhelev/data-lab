select
    order_date,
    country,
    sum(amount)              as revenue,
    count(distinct order_id) as orders
from {{ ref('orders_enriched') }}
where status <> 'cancelled'
group by order_date, country
order by order_date, country nulls last
