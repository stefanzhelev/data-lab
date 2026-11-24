with known_customers as (
    select customer_id from {{ ref('int_customers_checked') }} where reject_reason = ''
)

select
    o.*,
    concat_ws(';',
        case when count(*) over (partition by o.order_id) > 1               then 'conflicting_duplicate_order_id' end,
        case when o.order_date_raw is null                                   then 'missing_order_date' end,
        case when o.order_date_raw is not null and o.order_date is null      then 'unparseable_order_date' end,
        case when o.amount is null                                           then 'unparseable_amount' end,
        case when o.amount < 0 and o.status is distinct from 'refunded'      then 'negative_amount' end,
        case when o.quantity_raw is null                                     then 'missing_quantity' end,
        case when o.quantity_raw is not null and o.quantity is null          then 'unparseable_quantity' end,
        case when o.status is null
               or o.status not in {{ "('" ~ var('valid_statuses') | join("', '") ~ "')" }} then 'invalid_status' end,
        case when not exists (select 1 from known_customers k where k.customer_id = o.customer_id)
                                                                             then 'unknown_customer' end
    ) as reject_reason
from {{ ref('int_orders_deduped') }} as o
