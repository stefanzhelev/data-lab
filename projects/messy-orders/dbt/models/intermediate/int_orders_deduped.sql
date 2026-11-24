-- Drop exact duplicate lines (same values in every column). Lines that share an
-- order_id but differ are NOT dropped here: they are a conflict, quarantined later.
select *
from {{ ref('stg_orders') }}
qualify row_number() over (
    partition by order_id, customer_id, order_date_raw, amount_raw, quantity_raw, status, notes
    order by source_row
) = 1
