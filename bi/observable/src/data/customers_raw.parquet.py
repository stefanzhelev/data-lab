# Raw text in, nothing coerced; source_row is the CSV line number (header = line 1).
# Same as bi/evidence/sources/orders/customers_raw.sql.
from _raw import csv, write_parquet

write_parquet(f"SELECT (row_number() OVER () + 1)::INTEGER AS source_row, * FROM {csv('customers', all_varchar=True)}")
