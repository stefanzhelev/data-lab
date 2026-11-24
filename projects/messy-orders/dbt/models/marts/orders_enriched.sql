select
    o.order_id,
    o.customer_id,
    c.country,
    o.order_date,
    o.amount,
    o.quantity,
    o.status,
    o.notes,
    o.source_row
from {{ ref('int_orders_checked') }} as o
left join {{ ref('customers_clean') }} as c using (customer_id)
where o.reject_reason = ''
order by o.order_id
