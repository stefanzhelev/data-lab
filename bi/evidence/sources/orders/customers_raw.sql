-- Raw text in, nothing coerced; source_row is the CSV line number (header = line 1).
SELECT row_number() OVER () + 1 AS source_row, *
FROM read_csv('../../data/input/customers.csv', header = true, all_varchar = true)
