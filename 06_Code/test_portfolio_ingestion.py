import csv
import json
import tempfile
import unittest
from pathlib import Path

from portfolio_ingestion import ingest_latest_portfolio_import


class PortfolioIngestionTests(unittest.TestCase):

    def _paths(self, root):

        root = Path(root)
        return (
            root / "imports",
            root / "current" / "holdings_normalized.csv",
            root / "archive"
        )

    def _write_csv(self, path, fieldnames, rows):

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _read_output(self, output_path):

        with Path(output_path).open("r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    def test_no_import_directory_does_not_crash(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )

            self.assertEqual("no_imports", result["status"])
            self.assertTrue(import_dir.exists())
            self.assertTrue(archive_dir.exists())
            self.assertTrue(output_path.parent.exists())

    def test_no_csvs_returns_no_imports(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            import_dir.mkdir(parents=True)

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )

            self.assertEqual("no_imports", result["status"])
            self.assertEqual(0, result["rows_read"])

    def test_alias_columns_normalize_correctly(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                [
                    "Account Name",
                    "Symbol",
                    "Shares",
                    "Total Cost",
                    "Current Value",
                    "Description"
                ],
                [
                    {
                        "Account Name": "Brokerage",
                        "Symbol": "abc",
                        "Shares": "2",
                        "Total Cost": "10.25",
                        "Current Value": "12.50",
                        "Description": "ABC Co"
                    }
                ]
            )

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )
            rows = self._read_output(output_path)

            self.assertEqual("success", result["status"])
            self.assertEqual("ABC", rows[0]["ticker"])
            self.assertEqual("2", rows[0]["quantity"])
            self.assertEqual("10.25", rows[0]["cost_basis"])
            self.assertEqual("12.50", rows[0]["market_value"])
            self.assertEqual("ABC Co", rows[0]["security_name"])

    def test_duplicate_ticker_account_rows_aggregate(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                ["account", "ticker", "quantity", "cost_basis", "market_value"],
                [
                    {
                        "account": "Roth",
                        "ticker": "XYZ",
                        "quantity": "1",
                        "cost_basis": "10",
                        "market_value": "11"
                    },
                    {
                        "account": "Roth",
                        "ticker": "XYZ",
                        "quantity": "2",
                        "cost_basis": "20",
                        "market_value": "22"
                    }
                ]
            )

            ingest_latest_portfolio_import(import_dir, output_path, archive_dir)
            rows = self._read_output(output_path)

            self.assertEqual(1, len(rows))
            self.assertEqual("3", rows[0]["quantity"])
            self.assertEqual("30.00", rows[0]["cost_basis"])
            self.assertEqual("33.00", rows[0]["market_value"])

    def test_invalid_numeric_row_skipped(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                ["account", "ticker", "quantity", "cost_basis", "market_value"],
                [
                    {
                        "account": "Roth",
                        "ticker": "BAD",
                        "quantity": "not-number",
                        "cost_basis": "10",
                        "market_value": "11"
                    },
                    {
                        "account": "Roth",
                        "ticker": "GOOD",
                        "quantity": "1",
                        "cost_basis": "10",
                        "market_value": "11"
                    }
                ]
            )

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )
            rows = self._read_output(output_path)

            self.assertEqual("partial", result["status"])
            self.assertEqual(1, result["rows_skipped"])
            self.assertEqual(["GOOD"], [row["ticker"] for row in rows])

    def test_missing_ticker_skipped(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                ["account", "ticker", "quantity", "cost_basis", "market_value"],
                [
                    {
                        "account": "Roth",
                        "ticker": "",
                        "quantity": "1",
                        "cost_basis": "10",
                        "market_value": "11"
                    },
                    {
                        "account": "Roth",
                        "ticker": "GOOD",
                        "quantity": "1",
                        "cost_basis": "10",
                        "market_value": "11"
                    }
                ]
            )

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )

            self.assertEqual(1, result["rows_skipped"])
            self.assertIn("missing ticker", result["warnings"][0])

    def test_cash_rows_preserve_cash0_convention(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                ["account", "ticker", "quantity", "cost_basis", "market_value"],
                [
                    {
                        "account": "Brokerage",
                        "ticker": "cash",
                        "quantity": "5",
                        "cost_basis": "5",
                        "market_value": "5"
                    }
                ]
            )

            ingest_latest_portfolio_import(import_dir, output_path, archive_dir)
            rows = self._read_output(output_path)

            self.assertEqual("CASH0", rows[0]["ticker"])

    def test_normalized_output_written_and_archive_created(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                ["account", "ticker", "quantity", "cost_basis", "market_value"],
                [
                    {
                        "account": "Brokerage",
                        "ticker": "ABC",
                        "quantity": "1",
                        "cost_basis": "10",
                        "market_value": "11"
                    }
                ]
            )

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )

            self.assertTrue(output_path.exists())
            self.assertTrue(Path(result["archive_path"]).exists())
            self.assertEqual(1, len(list(archive_dir.glob("*.csv"))))

    def test_json_output_serializable(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            self._write_csv(
                import_dir / "positions.csv",
                ["account", "ticker", "quantity", "cost_basis", "market_value"],
                [
                    {
                        "account": "Brokerage",
                        "ticker": "ABC",
                        "quantity": "1",
                        "cost_basis": "10",
                        "market_value": "11"
                    }
                ]
            )

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )

            json.dumps(result, sort_keys=True)


if __name__ == "__main__":
    unittest.main()
