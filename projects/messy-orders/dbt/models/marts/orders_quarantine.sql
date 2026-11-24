-- Raw text is kept so anyone can see exactly what arrived and why it was rejected.
select source_row, order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes, reject_reason
from {{ ref('int_orders_checked') }}
where reject_reason <> ''
order by source_row
