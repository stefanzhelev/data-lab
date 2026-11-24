-- Tidy and type order lines. Typing uses try_* so bad values become NULL here and
-- are classified (not silently dropped) in int_orders_checked.
with raw as (
    select row_number() over () + 1 as source_row, *
    from {{ source('raw', 'orders') }}
),

tidy as (
    select
        source_row,
        nullif(trim(order_id), '')           as order_id,
        nullif(trim(customer_id), '')        as customer_id,
        nullif(trim(order_date), '')         as order_date_raw,
        nullif(trim(amount), '')             as amount_raw,
        nullif(trim(quantity), '')           as quantity_raw,
        nullif(lower(trim(status)), '')      as status,
        nullif(trim(notes), '')              as notes
    from raw
)

select
    *,
    try_strptime(order_date_raw, '%Y-%m-%d')::date                                   as order_date,
    try_cast(regexp_replace(amount_raw, '[£$€,]', '', 'g') as decimal(12, 2))        as amount,
    case when regexp_full_match(quantity_raw, '[0-9]+') then quantity_raw::integer end as quantity
from tidy
