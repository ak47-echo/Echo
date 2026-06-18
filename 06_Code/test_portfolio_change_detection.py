import csv
import json
import tempfile
import unittest
from pathlib import Path

from portfolio_change_detection import (
    build_portfolio_change_report,
    write_portfolio_change_report_text
)


class PortfolioChangeDetectionTests(unittest.TestCase):

    def _write_holdings(self, path, rows):

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "account",
                    "ticker",
                    "quantity",
                    "cost_basis",
                    "market_value",
                    "security_name",
                    "source_file",
                    "imported_at"
                ]
            )
            writer.writeheader()
            writer.writerows(rows)

    def test_no_previous_snapshot_does_not_crash(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            current = Path(temp_dir) / "current.csv"
            self._write_holdings(current, [
                {
                    "account": "Brokerage",
                    "ticker": "UNH",
                    "quantity": "1",
                    "cost_basis": "100",
                    "market_value": "120",
                    "security_name": "UnitedHealth",
                    "source_file": "current.csv",
                    "imported_at": "now"
                }
            ])

            report = build_portfolio_change_report(None, current)

            self.assertFalse(report["has_previous_snapshot"])
            self.assertEqual(1, report["summary"]["material_change_count"])
            self.assertEqual("UNH", report["new_positions"][0]["ticker"])

    def test_new_position_detected(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            previous = Path(temp_dir) / "previous.csv"
            current = Path(temp_dir) / "current.csv"
            self._write_holdings(previous, [])
            self._write_holdings(current, [
                {
                    "account": "Brokerage",
                    "ticker": "SMCI",
                    "quantity": "2",
                    "cost_basis": "50",
                    "market_value": "250",
                    "security_name": "SMCI",
                    "source_file": "current.csv",
                    "imported_at": "now"
                }
            ])

            report = build_portfolio_change_report(previous, current)

            self.assertEqual(1, len(report["new_positions"]))
            self.assertTrue(report["new_positions"][0]["material"])

    def test_removed_position_detected(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            previous = Path(temp_dir) / "previous.csv"
            current = Path(temp_dir) / "current.csv"
            row = {
                "account": "Brokerage",
                "ticker": "IBIT",
                "quantity": "5",
                "cost_basis": "100",
                "market_value": "200",
                "security_name": "IBIT",
                "source_file": "previous.csv",
                "imported_at": "old"
            }
            self._write_holdings(previous, [row])
            self._write_holdings(current, [])

            report = build_portfolio_change_report(previous, current)

            self.assertEqual(1, len(report["removed_positions"]))
            self.assertEqual("IBIT", report["removed_positions"][0]["ticker"])

    def test_quantity_change_detected(self):

        report = self._single_position_report("10", "12", "1000", "1000")

        self.assertEqual(1, len(report["quantity_changes"]))
        self.assertEqual(2, report["quantity_changes"][0]["delta_quantity"])

    def test_market_value_change_detected(self):

        report = self._single_position_report("10", "10", "1000", "1200")

        self.assertEqual(1, len(report["market_value_changes"]))
        self.assertEqual(
            200,
            report["market_value_changes"][0]["delta_market_value"]
        )

    def test_concentration_change_detected(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            previous = Path(temp_dir) / "previous.csv"
            current = Path(temp_dir) / "current.csv"
            self._write_holdings(previous, [
                self._row("A", "UNH", "10", "1000"),
                self._row("A", "SMCI", "10", "1000")
            ])
            self._write_holdings(current, [
                self._row("A", "UNH", "10", "1500"),
                self._row("A", "SMCI", "10", "500")
            ])

            report = build_portfolio_change_report(previous, current)
            material = [
                item for item in report["concentration_changes"]
                if item["ticker"] == "UNH"
            ][0]

            self.assertGreaterEqual(abs(material["delta_weight"]), 1)
            self.assertTrue(material["material"])

    def test_cash0_cash_change_detected(self):

        report = self._single_position_report(
            "100",
            "250",
            "100",
            "250",
            ticker="CASH0"
        )

        self.assertTrue(report["cash_changes"])
        self.assertEqual("TOTAL", report["cash_changes"][-1]["account"])

    def test_material_count_works(self):

        report = self._single_position_report("10", "11", "1000", "1125")

        self.assertGreaterEqual(report["summary"]["material_change_count"], 1)

    def test_json_serializable(self):

        report = self._single_position_report("10", "10", "1000", "1200")

        json.dumps(report, sort_keys=True)

    def test_text_output_written(self):

        report = self._single_position_report("10", "10", "1000", "1200")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "portfolio_change_detection.txt"
            result = write_portfolio_change_report_text(report, path)

            self.assertTrue(result["success"])
            self.assertTrue(path.exists())

    def _row(self, account, ticker, quantity, market_value):

        return {
            "account": account,
            "ticker": ticker,
            "quantity": quantity,
            "cost_basis": "0",
            "market_value": market_value,
            "security_name": ticker,
            "source_file": "test.csv",
            "imported_at": "now"
        }

    def _single_position_report(
        self,
        previous_quantity,
        current_quantity,
        previous_value,
        current_value,
        ticker="UNH"
    ):

        with tempfile.TemporaryDirectory() as temp_dir:
            previous = Path(temp_dir) / "previous.csv"
            current = Path(temp_dir) / "current.csv"
            self._write_holdings(previous, [
                self._row("Brokerage", ticker, previous_quantity, previous_value)
            ])
            self._write_holdings(current, [
                self._row("Brokerage", ticker, current_quantity, current_value)
            ])

            return build_portfolio_change_report(previous, current)


if __name__ == "__main__":
    unittest.main()
