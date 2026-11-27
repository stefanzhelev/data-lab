# data/input/owid_energy.csv as Parquet. year is cast to a 32-bit integer: DuckDB's default
# 64-bit integers arrive in the browser as BigInt, which Observable Plot can't mix with numbers.
from _raw import csv, write_parquet

write_parquet(f"SELECT * REPLACE (year::INTEGER AS year) FROM {csv('owid_energy')}")
