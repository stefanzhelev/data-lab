"""Stage tests for pipeline.ipynb.

The notebook defines five functions and hands its namespace to ``run_tests``:

    read_raw(path) -> DataFrame
    clean_customers(raw) -> DataFrame
    clean_orders(raw, customers) -> (valid, quarantine, exact_duplicates_dropped)
    daily_revenue(valid) -> DataFrame
    run(raw_dir, out_dir) -> report dict

    test_pipeline.run_tests(globals(), "LoadTests")   # one stage
    test_pipeline.run_tests(globals())                 # everything

The tests check behaviour, not implementation: any helper functions and column
order are up to you. Expected values come from data/input/*.csv (the same
numbers practice_pandas.ipynb produces: 8 valid orders, 11 quarantined, 1 exact duplicate).
"""

from __future__ import annotations

import filecmp
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from pandas.api import types as ptypes

ROOT = next(p for p in [Path.cwd(), *Path(__file__).resolve().parents] if (p / "data" / "input").is_dir())
RAW = ROOT / "data" / "input"

VALID_STATUSES = {"shipped", "delivered", "refunded", "cancelled"}
ORDER_LINES = 20  # data rows in orders.csv
CUSTOMER_LINES = 8  # data rows in customers.csv

_ns: dict = {}


def _fn(name: str):
    if name not in _ns:
        raise AssertionError(f"define {name}() in the notebook first")
    return _ns[name]


def _customers() -> pd.DataFrame:
    return _fn("clean_customers")(_fn("read_raw")(RAW / "customers.csv"))


def _orders():
    return _fn("clean_orders")(_fn("read_raw")(RAW / "orders.csv"), _customers())


def _ids(df: pd.DataFrame) -> set[str]:
    return set(df["order_id"].astype(str))


class LoadTests(unittest.TestCase):
    """Stage 1: read_raw keeps every value exactly as it arrived."""

    @classmethod
    def setUpClass(cls):
        cls.customers = _fn("read_raw")(RAW / "customers.csv")
        cls.orders = _fn("read_raw")(RAW / "orders.csv")

    def test_every_row_loaded(self):
        self.assertEqual(len(self.customers), CUSTOMER_LINES)
        self.assertEqual(len(self.orders), ORDER_LINES)

    def test_source_columns_are_text(self):
        for df in (self.customers, self.orders):
            for col in df.columns.drop("source_row", errors="ignore"):
                self.assertTrue(ptypes.is_string_dtype(df[col]), f"{col} is {df[col].dtype}, expected text")

    def test_leading_zeros_kept(self):
        self.assertIn("00042", set(self.customers["customer_id"]))

    def test_literal_na_is_not_missing(self):
        self.assertIn("NA", set(self.customers["country"].str.strip()))

    def test_unconvertible_values_survive(self):
        self.assertIn("N/A", set(self.orders["amount"]))
        self.assertIn("two", set(self.orders["quantity"]))


class CustomerTests(unittest.TestCase):
    """Stage 2: clean_customers tidies text, parses dates, keeps the latest version."""

    @classmethod
    def setUpClass(cls):
        cls.df = _customers().set_index("customer_id", drop=False)

    def test_one_row_per_customer(self):
        self.assertTrue(self.df["customer_id"].is_unique)
        self.assertEqual(set(self.df["customer_id"]), {"00017", "00042", "00073", "00088", "00091", "00105"})

    def test_text_is_tidy(self):
        self.assertEqual(self.df.loc["00017", "name"], "Alice Smith")
        self.assertEqual(self.df.loc["00017", "email"], "alice@example.com")
        self.assertEqual(self.df.loc["00091", "country"], "CN")

    def test_namibia_survives(self):
        self.assertEqual(self.df.loc["00088", "country"], "NA")

    def test_latest_version_wins(self):
        self.assertEqual(self.df.loc["00042", "email"], "robert.jones@example.com")

    def test_dates_are_parsed(self):
        for col in ("signup_date", "updated_at"):
            self.assertTrue(ptypes.is_datetime64_any_dtype(self.df[col]), f"{col} is {self.df[col].dtype}")

    def test_blank_is_missing(self):
        self.assertTrue(pd.isna(self.df.loc["00105", "country"]), "a blank country should be missing, not ''")


class OrderTests(unittest.TestCase):
    """Stage 3: clean_orders types valid rows and quarantines the rest, with a reason."""

    @classmethod
    def setUpClass(cls):
        result = _orders()
        assert isinstance(result, tuple) and len(result) == 3, "return (valid, quarantine, exact_duplicates_dropped)"
        cls.valid, cls.quarantine, cls.n_exact = result

    def test_every_row_accounted_for(self):
        self.assertEqual(len(self.valid) + len(self.quarantine) + self.n_exact, ORDER_LINES)

    def test_counts(self):
        self.assertEqual((len(self.valid), len(self.quarantine), self.n_exact), (8, 11, 1))

    def test_no_order_in_both_outputs(self):
        self.assertFalse(_ids(self.valid) & _ids(self.quarantine))

    def test_valid_is_typed(self):
        self.assertTrue(ptypes.is_numeric_dtype(self.valid["amount"]))
        self.assertTrue(ptypes.is_integer_dtype(self.valid["quantity"]))
        self.assertTrue(ptypes.is_datetime64_any_dtype(self.valid["order_date"]))
        self.assertLessEqual(set(self.valid["status"]), VALID_STATUSES)

    def test_currency_amount_parsed(self):
        amount = self.valid.set_index(self.valid["order_id"].astype(str)).loc["1002", "amount"]
        self.assertAlmostEqual(float(amount), 1200.00)

    def test_valid_has_country(self):
        self.assertIn("country", self.valid.columns)
        self.assertEqual(len(self.valid), self.valid["order_id"].nunique(), "the join must not duplicate orders")

    def test_bad_rows_quarantined(self):
        # impossible date, N/A amount, unknown customer, conflicting duplicate, invalid status
        self.assertLessEqual({"1005", "1006", "1007", "1013", "1015"}, _ids(self.quarantine))

    def test_quarantine_has_reasons(self):
        self.assertIn("reject_reason", self.quarantine.columns)
        self.assertFalse(
            self.quarantine["reject_reason"].isna().any() or (self.quarantine["reject_reason"] == "").any()
        )

    def test_quarantine_keeps_raw_text(self):
        amounts = set(self.quarantine["amount"].astype(str))
        self.assertIn("N/A", amounts, "keep the value that arrived, so the rejection can be checked")


class RevenueTests(unittest.TestCase):
    """Stage 4: daily_revenue per order_date and country, cancelled excluded."""

    @classmethod
    def setUpClass(cls):
        cls.valid = _orders()[0]
        cls.df = _fn("daily_revenue")(cls.valid)

    def test_columns(self):
        self.assertLessEqual({"order_date", "country", "revenue", "orders"}, set(self.df.columns))

    def test_one_row_per_day_and_country(self):
        self.assertFalse(self.df.duplicated(["order_date", "country"]).any())

    def test_total_excludes_cancelled_and_keeps_every_country(self):
        billable = self.valid[self.valid["status"] != "cancelled"]
        self.assertAlmostEqual(float(self.df["revenue"].sum()), float(billable["amount"].sum()), places=2)
        self.assertAlmostEqual(float(self.df["revenue"].sum()), 1293.75, places=2)

    def test_order_count(self):
        billable = self.valid[self.valid["status"] != "cancelled"]
        self.assertEqual(int(self.df["orders"].sum()), billable["order_id"].nunique())


class RunTests(unittest.TestCase):
    """Stage 5: run writes the outputs and a report, and is idempotent."""

    def test_returns_report(self):
        with tempfile.TemporaryDirectory() as d:
            report = _fn("run")(RAW, Path(d))
            self.assertIsInstance(report, dict)
            self.assertTrue(any(Path(d).glob("*.json")), "write the report as JSON")
            self.assertTrue(any(Path(d).glob("*.csv")), "write the output tables")

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            _fn("run")(RAW, Path(a))
            _fn("run")(RAW, Path(a))  # second run over the same directory
            _fn("run")(RAW, Path(b))
            files = sorted(p.name for p in Path(a).iterdir())
            self.assertEqual(sorted(p.name for p in Path(b).iterdir()), files, "no stray files")
            _, mismatch, errors = filecmp.cmpfiles(a, b, files, shallow=False)
            self.assertEqual(mismatch + errors, [], "two runs must write identical files")


STAGES = [LoadTests, CustomerTests, OrderTests, RevenueTests, RunTests]


def run_tests(ns: dict, *names: str) -> unittest.TestResult:
    """Run the named test classes (default: all) against the functions in ``ns``.

    Prints the results and returns them; never raises, so the notebook keeps running.
    """
    _ns.clear()
    _ns.update(ns)
    by_name = {c.__name__: c for c in STAGES}
    unknown = [n for n in names if n not in by_name]
    if unknown:
        raise ValueError(f"unknown test class {unknown}; choose from {list(by_name)}")
    cases = [by_name[n] for n in names] or STAGES
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in cases)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
