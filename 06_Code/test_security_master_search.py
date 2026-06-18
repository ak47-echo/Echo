import csv
import json
import tempfile
import unittest
from pathlib import Path

from security_master_search import load_security_master, search_security_master


class SecurityMasterSearchTests(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "security_master.csv"
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["ticker", "name", "category", "expense_ratio"]
            )
            writer.writeheader()
            writer.writerow({
                "ticker": "NVDA",
                "name": "Nvidia Corp",
                "category": "US Large Growth",
                "expense_ratio": "0.0"
            })
            writer.writerow({
                "ticker": "AVUV",
                "name": "Avantis US Small Cap Value ETF",
                "category": "US Small Value",
                "expense_ratio": "0.0025"
            })
            writer.writerow({
                "ticker": "NUKE",
                "name": "Nuclear Energy Test Fund",
                "category": "Energy ETF",
                "expense_ratio": ""
            })

    def tearDown(self):

        self.temp_dir.cleanup()

    def test_ticker_match(self):

        result = search_security_master("NVDA", path=self.path)
        self.assertEqual("NVDA", result["matches"][0]["ticker"])

    def test_name_match(self):

        result = search_security_master("Nvidia", path=self.path)
        self.assertEqual("NVDA", result["matches"][0]["ticker"])

    def test_category_match(self):

        result = search_security_master(
            "small cap value",
            categories=["small value"],
            path=self.path
        )
        self.assertTrue(any(item["ticker"] == "AVUV" for item in result["matches"]))

    def test_etf_fund_category_match(self):

        result = search_security_master("energy ETF", path=self.path)
        self.assertTrue(any(item["ticker"] == "NUKE" for item in result["matches"]))

    def test_expense_ratio_parsing(self):

        rows = load_security_master(self.path)
        avuv = [row for row in rows if row["ticker"] == "AVUV"][0]
        self.assertEqual(0.0025, avuv["expense_ratio"])

    def test_no_match_safe_response(self):

        result = search_security_master("zzzz unmatched security", path=self.path)
        self.assertEqual(0, result["match_count"])
        self.assertTrue(result["warnings"])

    def test_json_serializable(self):

        json.dumps(search_security_master("NVDA", path=self.path))


if __name__ == "__main__":
    unittest.main()
