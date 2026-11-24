-- Tidy and type the customer master. Nothing is dropped here: every raw row keeps
-- its source_row (CSV line number) so quarantine output can point back to it.
with raw as (
    select row_number() over () + 1 as source_row, *
    from {{ source('raw', 'customers') }}
),

tidy as (
    select
        source_row,
        nullif(trim(customer_id), '')        as customer_id,
        nullif(trim(name), '')               as name,
        nullif(lower(trim(email)), '')       as email,
        nullif(upper(trim(country)), '')     as country,
        nullif(trim(signup_date), '')        as signup_date_raw,
        nullif(trim(updated_at), '')         as updated_at_raw
    from raw
)

select
    *,
    try_strptime(signup_date_raw, '%Y-%m-%d')::date     as signup_date,
    try_strptime(updated_at_raw, '%Y-%m-%dT%H:%M:%S')   as updated_at
from tidy
