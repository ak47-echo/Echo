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

    def _write_rows(self, path, rows):

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(rows)

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

    def test_schwab_sectioned_all_accounts_export_normalizes(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            import_dir, output_path, archive_dir = self._paths(temp_dir)
            header = [
                "Symbol",
                "Description",
                "Qty (Quantity)",
                "Price",
                "Price Chng %",
                "Mkt Val (Market Value)",
                "Day Chng $",
                "Cost Basis",
                "Gain $",
                "% of Acct"
            ]
            self._write_rows(
                import_dir / "schwab_positions.csv",
                [
                    ["All-Accounts Positions for June 18, 2026"],
                    [],
                    ["Roth_Contributory_IRA ...399"],
                    header,
                    [
                        "UNH",
                        "UNITEDHEALTH GROUP INC",
                        "16",
                        "$403.86",
                        "-0.02%",
                        "$6,461.73",
                        "-$18.58",
                        "$4,573.17",
                        "$1,888.56",
                        "97.2%"
                    ],
                    [
                        "Cash & Cash Investments",
                        "",
                        "--",
                        "",
                        "",
                        "$183.76",
                        "",
                        "--",
                        "",
                        "2.8%"
                    ],
                    [
                        "Positions Total",
                        "",
                        "",
                        "",
                        "",
                        "$6,645.49",
                        "",
                        "$4,573.17",
                        "",
                        "100%"
                    ],
                    [],
                    ["Individual_Brokerage ...123"],
                    header,
                    [
                        "SMCI",
                        "SUPER MICRO COMPUTER INC",
                        "91",
                        "$30.34",
                        "1.20%",
                        "$2,760.50",
                        "$10.00",
                        "$3,555.26",
                        "-$794.76",
                        "74.8%"
                    ],
                    [
                        "IBIT",
                        "ISHARES BITCOIN TRUST ETF",
                        "25",
                        "$35.77",
                        "0.5%",
                        "$894.25",
                        "$5.00",
                        "$1,100.50",
                        "-$206.25",
                        "24.2%"
                    ],
                    [
                        "Cash & Cash Investments",
                        "",
                        "--",
                        "",
                        "",
                        "$35.06",
                        "",
                        "--",
                        "",
                        "1.0%"
                    ],
                    [
                        "Positions Total",
                        "",
                        "",
                        "",
                        "",
                        "$3,689.81",
                        "",
                        "$4,655.76",
                        "",
                        "100%"
                    ]
                ]
            )

            result = ingest_latest_portfolio_import(
                import_dir,
                output_path,
                archive_dir
            )
            rows = self._read_output(output_path)
            positions = {
                (row["account"], row["ticker"]): row
                for row in rows
            }

            self.assertEqual("success", result["status"])
            self.assertEqual(5, result["position_count"])
            self.assertEqual(5, result["rows_read"])
            self.assertEqual(0, result["rows_skipped"])
            self.assertAlmostEqual(10335.30, result["total_market_value"])
            self.assertIn(("Roth_Contributory_IRA ...399", "UNH"), positions)
            self.assertIn(("Individual_Brokerage ...123", "SMCI"), positions)
            self.assertIn(("Individual_Brokerage ...123", "IBIT"), positions)
            self.assertIn(("Roth_Contributory_IRA ...399", "CASH0"), positions)
            self.assertIn(("Individual_Brokerage ...123", "CASH0"), positions)
            self.assertEqual(
                "6461.73",
                positions[("Roth_Contributory_IRA ...399", "UNH")][
                    "market_value"
                ]
            )
            self.assertEqual(
                "3555.26",
                positions[("Individual_Brokerage ...123", "SMCI")][
                    "cost_basis"
                ]
            )
            self.assertEqual(
                "25",
                positions[("Individual_Brokerage ...123", "IBIT")][
                    "quantity"
                ]
            )
            self.assertEqual(
                "Cash & Cash Investments",
                positions[("Roth_Contributory_IRA ...399", "CASH0")][
                    "security_name"
                ]
            )


if __name__ == "__main__":
    unittest.main()
