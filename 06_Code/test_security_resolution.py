import csv
import json
import tempfile
import unittest
from pathlib import Path

from security_resolution import (
    build_security_resolution,
    extract_security_mentions
)


def _write_csv(path, fieldnames, rows):

    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class SecurityResolutionTests(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.master = self.root / "security_master.csv"
        self.holdings = self.root / "holdings_normalized.csv"
        self.watchlist = self.root / "watchlist.csv"
        self.aliases = self.root / "security_aliases.json"
        self.history = self.root / "security_ticker_history.json"
        _write_csv(
            self.master,
            ["ticker", "name", "category", "expense_ratio"],
            [
                {
                    "ticker": "SPCX",
                    "name": "Legacy SPAC ETF",
                    "category": "ETF",
                    "expense_ratio": "0.01"
                },
                {
                    "ticker": "NVDA",
                    "name": "Nvidia Corp",
                    "category": "US Large Growth",
                    "expense_ratio": "0"
                }
            ]
        )
        _write_csv(
            self.holdings,
            ["account", "ticker", "security_name", "category", "quantity", "market_value"],
            [{
                "account": "Brokerage",
                "ticker": "SMCI",
                "security_name": "Super Micro Computer Inc",
                "category": "US Small Growth",
                "quantity": "10",
                "market_value": "1000"
            }]
        )
        _write_csv(
            self.watchlist,
            ["ticker", "name", "category", "expense_ratio", "priority", "conviction", "notes"],
            [{
                "ticker": "AVUV",
                "name": "Avantis US Small Cap Value ETF",
                "category": "US Small Value",
                "expense_ratio": "0.0025",
                "priority": "high",
                "conviction": "high",
                "notes": "small-cap value candidate"
            }]
        )
        self.aliases.write_text(
            json.dumps({
                "facebook": [{
                    "ticker": "META",
                    "name": "Meta Platforms Inc",
                    "security_type": "stock"
                }]
            }),
            encoding="utf-8"
        )
        self.history.write_text(
            json.dumps({
                "OLD": {
                    "current_ticker": "NEW",
                    "current_name": "New Company Inc",
                    "security_type": "stock",
                    "status": "ticker changed",
                    "source_date": "2025-01-01"
                }
            }),
            encoding="utf-8"
        )

    def tearDown(self):

        self.temp_dir.cleanup()

    def _resolve(self, query, **kwargs):

        defaults = {
            "security_master_path": self.master,
            "holdings_path": self.holdings,
            "watchlist_path": self.watchlist,
            "alias_path": self.aliases,
            "history_path": self.history,
            "live_candidates": [],
            "news_candidates": []
        }
        defaults.update(kwargs)
        return build_security_resolution(query, **defaults)

    def test_spcx_ambiguity_between_local_old_candidate_and_fresh_live_candidate(self):

        resolution = self._resolve(
            "SPCX",
            live_candidates=[{
                "ticker": "SPCX",
                "name": "Example Newly Listed Operating Company",
                "security_type": "stock",
                "status": "IPO newly listed current exchange listing",
                "source_date": "2026-06-01",
                "match_reason": "newly listed ticker debut"
            }]
        )

        self.assertTrue(resolution["ambiguity_detected"])
        self.assertFalse(resolution["resolved"])
        self.assertGreaterEqual(len(resolution["candidates"]), 2)
        self.assertTrue(any(item["source"] == "security_master" for item in resolution["candidates"]))
        self.assertTrue(any(item["source"] == "live_research_candidate" for item in resolution["candidates"]))

    def test_ticker_alias_resolution(self):

        resolution = self._resolve("Facebook")

        self.assertTrue(resolution["resolved"])
        self.assertEqual("META", resolution["selected_security"]["ticker"])
        self.assertEqual("HIGH", resolution["confidence"])

    def test_ticker_rename_resolution(self):

        resolution = self._resolve("OLD")

        self.assertTrue(resolution["resolved"])
        self.assertEqual("NEW", resolution["selected_security"]["ticker"])
        self.assertIn("historical", resolution["selected_security"]["source"])

    def test_company_name_resolution(self):

        resolution = self._resolve("Nvidia")

        self.assertTrue(resolution["resolved"])
        self.assertEqual("NVDA", resolution["selected_security"]["ticker"])

    def test_compare_query_extracts_each_side(self):

        self.assertEqual(["USO", "SPCX"], extract_security_mentions("compare USO vs SPCX"))

    def test_current_holding_resolution(self):

        resolution = self._resolve("SMCI")

        self.assertTrue(resolution["resolved"])
        self.assertEqual("SMCI", resolution["selected_security"]["ticker"])
        self.assertEqual("current_holding", resolution["selected_security"]["source"])

    def test_watchlist_resolution(self):

        resolution = self._resolve("AVUV")

        self.assertTrue(resolution["resolved"])
        self.assertEqual("AVUV", resolution["selected_security"]["ticker"])
        self.assertEqual("watchlist", resolution["selected_security"]["source"])

    def test_low_confidence_ambiguity_for_unknown(self):

        resolution = self._resolve("Unknown Future Asset")

        self.assertFalse(resolution["resolved"])
        self.assertTrue(resolution["ambiguity_detected"])
        self.assertEqual(0, len(resolution["candidates"]))


if __name__ == "__main__":
    unittest.main()
