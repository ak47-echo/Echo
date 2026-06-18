import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import echo
import live_research
import security_intelligence
from agents.portfolio_manager import get_thesis_refresh_implications


class LiveResearchTests(unittest.TestCase):

    def _isolate_security_intelligence_reports(self, temp_dir):

        old_refresh = security_intelligence.THESIS_REFRESH_PATH
        old_evidence = security_intelligence.RESEARCH_EVIDENCE_STORE_PATH
        security_intelligence.THESIS_REFRESH_PATH = Path(temp_dir) / "missing_refresh.json"
        security_intelligence.RESEARCH_EVIDENCE_STORE_PATH = Path(temp_dir) / "missing_evidence.json"
        return old_refresh, old_evidence

    def _restore_security_intelligence_reports(self, old_paths):

        security_intelligence.THESIS_REFRESH_PATH = old_paths[0]
        security_intelligence.RESEARCH_EVIDENCE_STORE_PATH = old_paths[1]

    def test_stale_theses_csv_is_manual_legacy_not_current_truth(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            old_paths = self._isolate_security_intelligence_reports(temp_dir)
            try:
                profile = security_intelligence.build_security_profile("SMCI")
            finally:
                self._restore_security_intelligence_reports(old_paths)

        self.assertEqual("manual_legacy_thesis", profile["thesis_source"])
        self.assertIn("manual_legacy_thesis", profile["known_data"])
        self.assertTrue(
            any("not current truth" in item for item in profile["missing_data"])
        )

    def test_thesis_refresh_overrides_manual_thesis(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            refresh_path = Path(temp_dir) / "thesis_refresh.json"
            refresh_path.write_text(json.dumps({
                "thesis_refreshes": [{
                    "ticker": "SMCI",
                    "current_thesis": "Fresh generated SMCI thesis.",
                    "bull_case_summary": "Fresh bull case.",
                    "bear_case_summary": "Fresh bear case.",
                    "conviction_direction": "improving",
                    "research_status": "fresh",
                    "recommended_next_review": "2026-07-18",
                    "portfolio_action_implication": "monitor",
                    "requires_user_approval": True
                }]
            }), encoding="utf-8")
            old_refresh = security_intelligence.THESIS_REFRESH_PATH
            old_evidence = security_intelligence.RESEARCH_EVIDENCE_STORE_PATH
            security_intelligence.THESIS_REFRESH_PATH = refresh_path
            security_intelligence.RESEARCH_EVIDENCE_STORE_PATH = Path(temp_dir) / "missing_evidence.json"
            try:
                profile = security_intelligence.build_security_profile("SMCI")
            finally:
                security_intelligence.THESIS_REFRESH_PATH = old_refresh
                security_intelligence.RESEARCH_EVIDENCE_STORE_PATH = old_evidence

        self.assertEqual("thesis_refresh", profile["thesis_source"])
        self.assertEqual("Fresh generated SMCI thesis.", profile["thesis_summary"])
        self.assertTrue(profile["manual_legacy_thesis"])

    def test_live_research_disabled_gives_local_only_mode(self):

        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            "os.environ",
            {
                "LIVE_RESEARCH_ENABLED": "false",
                "ANTHROPIC_WEB_SEARCH_ENABLED": "false"
            },
            clear=False
        ):
            old_paths = self._isolate_security_intelligence_reports(temp_dir)
            try:
                profile = live_research.build_research_profile("SMCI")
            finally:
                self._restore_security_intelligence_reports(old_paths)

        self.assertEqual("local_only", profile["source_mode"])
        self.assertTrue(
            any("Missing live web evidence" in item for item in profile["missing_data"])
        )

    def test_web_search_enabled_flag_is_passed_to_anthropic_provider(self):

        with patch.dict("os.environ", {"ANTHROPIC_WEB_SEARCH_ENABLED": "true"}, clear=False):
            provider = echo.AnthropicProvider()
            self.assertTrue(provider.web_search_tools())
            status = echo.get_llm_provider_status("anthropic")

        self.assertTrue(
            status["live_research_policy"]["anthropic_web_search_enabled"]
        )

    def test_security_intelligence_prioritizes_fresh_generated_research(self):

        self.test_thesis_refresh_overrides_manual_thesis()

    def test_portfolio_manager_receives_implications_but_does_not_trade(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "thesis_refresh.json"
            path.write_text(json.dumps({
                "thesis_refreshes": [{
                    "ticker": "UNH",
                    "research_status": "fresh",
                    "conviction_direction": "deteriorating",
                    "portfolio_action_implication": "research_more"
                }]
            }), encoding="utf-8")
            lines = get_thesis_refresh_implications(path)

        text = " ".join(lines).casefold()
        self.assertIn("research review needed", text)
        self.assertIn("informational only", text)
        self.assertIn("no trades", text)

    def test_no_overwrite_of_theses_csv(self):

        path = Path(__file__).resolve().parent.parent / "02_Data" / "theses.csv"
        before = path.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "research_evidence_store.json"
            thesis_path = Path(temp_dir) / "thesis_refresh.json"
            store = live_research.build_research_evidence_store(["SMCI"])
            refresh = live_research.build_thesis_refresh(["SMCI"], evidence_store=store)
            live_research.write_research_evidence_store_json(store, evidence_path)
            live_research.write_thesis_refresh_json(refresh, thesis_path)
        after = path.read_text(encoding="utf-8")

        self.assertEqual(before, after)

    def test_json_serializable_and_no_secrets_exposed(self):

        with patch.dict(
            "os.environ",
            {"ANTHROPIC_API_KEY": "TEST_SECRET_VALUE"},
            clear=False
        ):
            store = live_research.build_research_evidence_store(["SMCI"])
            refresh = live_research.build_thesis_refresh(["SMCI"], evidence_store=store)
            text = json.dumps({"store": store, "refresh": refresh})

        self.assertNotIn("TEST_SECRET_VALUE", text)
        self.assertIn("research_evidence_store", json.dumps({"research_evidence_store": store}))


if __name__ == "__main__":
    unittest.main()
