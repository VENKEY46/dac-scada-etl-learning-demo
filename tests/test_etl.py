import unittest

import pandas as pd

from run_etl import validate_and_transform
from test_validation import valid_reading


class EtlTests(unittest.TestCase):
    def test_duplicate_is_logged_and_latest_row_is_kept(self):
        first = valid_reading()
        second = valid_reading()
        first["temperature_c"] = 24.0
        clean, rejected, stats = validate_and_transform(pd.DataFrame([first, second]))
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean.iloc[0]["temperature_c"], 25.0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(stats["duplicates_removed"], 1)

    def test_invalid_numeric_text_is_rejected(self):
        row = valid_reading()
        row["pressure_kpa"] = "not-a-number"
        clean, rejected, _ = validate_and_transform(pd.DataFrame([row]))
        self.assertTrue(clean.empty)
        self.assertEqual(len(rejected), 1)
        self.assertIn("pressure_kpa", rejected.iloc[0]["rejection_reason"])


if __name__ == "__main__":
    unittest.main()

