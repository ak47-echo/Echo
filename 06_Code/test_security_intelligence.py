import json
import tempfile
import unittest
from pathlib import Path

from security_intelligence import (
    build_security_intelligence_report,
    build_security_profile,
    compare_security_profiles,
    write_security_intelligence_json,
    write_security_intelligence_text
)


class SecurityIntelligenceTests(unittest.TestCase):

    def test_smci_profile_generated(self):

        profile = build_security_profile("SMCI")

        self.assertEqual("SMCI", profile["ticker"])
        self.assertTrue(profile["name"])
        self.assertTrue(profile["known_data"])

    def test_nvda_profile_generated(self):

        profile = build_security_profile("NVDA")

        self.assertEqual("NVDA", profile["ticker"])
        self.assertIn("NVIDIA", profile["name"].upper())

    def test_held_status_detected(self):

        profile = build_security_profile("SMCI")

        self.assertTrue(profile["is_current_holding"])
        self.assertIsNotNone(profile["portfolio_weight"])

    def test_watchlist_status_detected(self):

        profile = build_security_profile("AVUV")

        self.assertTrue(profile["is_watchlist"])

    def test_thesis_integration_works(self):

        profile = build_security_profile("SMCI")

        self.assertIn("AI infrastructure", profile["thesis_summary"])
        self.assertEqual("active", profile["thesis_status"])

    def test_missing_thesis_handled(self):

        profile = build_security_profile("NVDA")

        self.assertIn("thesis text", profile["missing_data"])
        self.assertTrue(
            any("Missing thesis" in flag for flag in profile["research_quality_flags"])
        )

    def test_low_conviction_quality_flag_only(self):

        profile = build_security_profile("SMCI")

        self.assertTrue(
            any("Low conviction" in flag for flag in profile["research_quality_flags"])
        )
        evidence_text = " ".join(
            profile["bull_factors"]
            + profile["bear_factors"]
            + profile["macro_exposures"]
            + profile["news_exposures"]
        ).casefold()
        self.assertNotIn("low conviction", evidence_text)
        self.assertNotIn("reevaluate", evidence_text)
        self.assertNotIn("buy", evidence_text)
        self.assertNotIn("sell", evidence_text)

    def test_bull_and_bear_factors_generated(self):

        profile = build_security_profile("SMCI")

        self.assertTrue(profile["bull_factors"])
        self.assertTrue(profile["bear_factors"])

    def test_macro_exposures_generated(self):

        profile = build_security_profile("UNH")

        self.assertTrue(profile["macro_exposures"])

    def test_no_direct_news_handled_honestly(self):

        profile = build_security_profile("NVDA")

        self.assertTrue(
            profile["news_exposures"]
            or any("No direct local news" in item for item in profile["missing_data"])
        )

    def test_comparison_works(self):

        comparison = compare_security_profiles(["SMCI", "NVDA"])

        self.assertEqual(["SMCI", "NVDA"], comparison["tickers"])
        self.assertEqual(2, len(comparison["comparison"]))
        self.assertIn("evidence_policy", comparison)

    def test_json_serializable(self):

        json.dumps(build_security_intelligence_report(["SMCI", "NVDA"]))

    def test_output_files_written(self):

        report = build_security_intelligence_report(["SMCI", "NVDA"])
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "security_intelligence.json"
            text_path = Path(temp_dir) / "security_intelligence.txt"
            self.assertTrue(
                write_security_intelligence_json(report, json_path)["success"]
            )
            self.assertTrue(
                write_security_intelligence_text(report, text_path)["success"]
            )
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
