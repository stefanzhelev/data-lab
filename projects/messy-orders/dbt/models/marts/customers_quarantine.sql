select source_row, customer_id, name, email, country, signup_date_raw, updated_at_raw, reject_reason
from {{ ref('int_customers_checked') }}
where reject_reason <> ''
order by source_row
