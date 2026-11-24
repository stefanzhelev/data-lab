-- Every raw order line must be accounted for: valid + quarantined + exact duplicates.
-- Returns a row (= failure) if anything went missing.
with counts as (
    select
        (select count(*) from {{ ref('stg_orders') }})                                           as rows_in,
        (select count(*) from {{ ref('orders_enriched') }})                                      as valid,
        (select count(*) from {{ ref('orders_quarantine') }})                                    as quarantined,
        (select count(*) from {{ ref('stg_orders') }}) - (select count(*) from {{ ref('int_orders_deduped') }}) as exact_duplicates
)
select * from counts
where rows_in <> valid + quarantined + exact_duplicates
