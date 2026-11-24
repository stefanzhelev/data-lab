select customer_id, name, email, country, signup_date, updated_at
from {{ ref('int_customers_checked') }}
where reject_reason = ''
order by customer_id
