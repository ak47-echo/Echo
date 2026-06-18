import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import market_coverage


class MarketCoverageTests(unittest.TestCase):

    def _holdings(self):

        return [
            {
                "ticker": "SMCI",
                "name": "Super Micro Computer Inc",
                "security_name": "Super Micro Computer Inc",
                "category": "US Large Growth",
                "market_value": 25000
            },
            {
                "ticker": "CASH0",
                "name": "Cash & Cash Investments",
                "security_name": "Cash & Cash Investments",
                "category": "",
                "market_value": 1000
            }
        ]

    def _watchlist(self):

        return [{
            "ticker": "AVUV",
            "name": "Avantis US Small Cap Value ETF",
            "category": "US Small Value",
            "expense_ratio": 0.0025
        }]

    def _security_master(self):

        return [
            {
                "ticker": "NVDA",
                "name": "Nvidia Corp",
                "category": "US Large Growth",
                "expense_ratio": 0.0
            },
            {
                "ticker": "OKLO",
                "name": "Oklo Inc",
                "category": "Nuclear Energy",
                "expense_ratio": None
            }
        ]

    def _build(self, query="what do you think about NVDA"):

        with patch.object(market_coverage, "load_current_holdings", self._holdings), \
                patch.object(market_coverage, "load_watchlist", self._watchlist), \
                patch.object(market_coverage, "load_security_master", self._security_master), \
                patch.object(market_coverage, "_load_research_theses", return_value=[]), \
                patch.object(market_coverage, "search_security_master") as search:
            search.return_value = {
                "matches": [self._security_master()[0]],
                "warnings": []
            }
            return market_coverage.build_market_coverage(query)

    def test_dynamic_holdings_terms_from_normalized_holdings(self):

        coverage = self._build()
        self.assertIn("SMCI", coverage["holdings_terms"])
        self.assertIn("Super Micro Computer Inc", coverage["holdings_terms"])

    def test_cash0_excluded_from_general_market_news_matching(self):

        coverage = self._build()
        all_terms = " ".join(
            coverage["holdings_terms"]
            + coverage["watchlist_terms"]
            + coverage["query_terms"]
        )
        self.assertNotIn("CASH0", all_terms)
        self.assertNotIn("Cash & Cash Investments", all_terms)

    def test_dynamic_watchlist_terms(self):

        coverage = self._build()
        self.assertIn("AVUV", coverage["watchlist_terms"])
        self.assertIn("US Small Value", coverage["watchlist_terms"])

    def test_security_master_ticker_lookup_for_non_holding(self):

        coverage = self._build("what do you think about NVDA")
        self.assertIn("NVDA", coverage["query_terms"])
        nvda = [
            item for item in coverage["coverage_universe"]
            if item["ticker"] == "NVDA"
        ][0]
        self.assertFalse(nvda["is_current_holding"])
        self.assertEqual("query", nvda["source"])

    def test_current_holding_resolves_as_holding(self):

        coverage = self._build()
        smci = [
            item for item in coverage["coverage_universe"]
            if item["ticker"] == "SMCI"
        ][0]
        self.assertTrue(smci["is_current_holding"])

    def test_category_lookup_terms(self):

        with patch.object(market_coverage, "load_current_holdings", self._holdings), \
                patch.object(market_coverage, "load_watchlist", self._watchlist), \
                patch.object(market_coverage, "load_security_master", self._security_master), \
                patch.object(market_coverage, "_load_research_theses", return_value=[]), \
                patch.object(market_coverage, "search_security_master") as search:
            search.return_value = {
                "matches": [self._security_master()[1]],
                "warnings": []
            }
            coverage = market_coverage.build_market_coverage(
                "find nuclear stocks worth researching"
            )
        self.assertIn("OKLO", coverage["query_terms"])
        self.assertTrue(
            any("Nuclear" in term for term in coverage["query_terms"])
        )

    def test_market_coverage_json_serializable(self):

        json.dumps(self._build())

    def test_output_files_written(self):

        coverage = self._build()
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "market_coverage.json"
            text_path = Path(temp_dir) / "market_coverage.txt"
            self.assertTrue(
                market_coverage.write_market_coverage_json(
                    coverage,
                    json_path
                )["success"]
            )
            self.assertTrue(
                market_coverage.write_market_coverage_text(
                    coverage,
                    text_path
                )["success"]
            )
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
