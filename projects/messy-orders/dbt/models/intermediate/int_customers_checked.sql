-- Latest version per customer_id wins (SCD1), then rule checks.
with deduped as (
    select *
    from {{ ref('stg_customers') }}
    qualify row_number() over (
        partition by customer_id
        order by updated_at desc nulls last, source_row desc
    ) = 1
)

select
    *,
    concat_ws(';',
        case when customer_id is null then 'missing_customer_id' end
    ) as reject_reason
from deduped
