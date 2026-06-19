import json
import tempfile
import unittest
from pathlib import Path

from echo_context_assembler import (
    assemble_echo_context,
    write_context_assembly_json,
    write_context_assembly_text
)


def _memory():

    return {
        "summary": {
            "top_priority": "Review concentration",
            "dominant_theme": "Portfolio Concentration Risk"
        },
        "operating_context": {
            "current_state": {
                "top_priority": {"title": "Review concentration"}
            },
            "recommended_attention": [
                {"label": "Concentration Risk", "score": 40}
            ],
            "important_changes": [
                {"label": "Risk changed"}
            ],
            "persistent_patterns": [
                {"label": "Persistent risk"}
            ],
            "connected_entities": [
                {"label": "Portfolio Agent"}
            ],
            "top_signals": [
                {"label": "Top signal"}
            ]
        }
    }


def _budget(level="standard", query_class="agent_specific", max_items=20):

    return {
        "budget_level": level,
        "query_class": query_class,
        "max_context_items": max_items
    }


def _routing(agent="portfolio", include_full=True):

    return {
        "primary_agents": [agent],
        "secondary_agents": [],
        "excluded_agents": ["research", "news", "macro"],
        "routing_mode": "single_agent",
        "agent_context_plan": [
            {
                "agent": agent,
                "role": "primary",
                "context_sources": ["memory_context", f"{agent}_full_report"],
                "include_full_report": include_full,
                "reason": "Matched test agent."
            }
        ]
    }


def _reports():

    return {
        "portfolio": ["PORTFOLIO REPORT", "Concentration risk details."],
        "research": ["RESEARCH REPORT", "Research details."],
        "news": ["NEWS REPORT", "News details."],
        "macro": ["MACRO REPORT", "Macro details."],
        "executive": ["EXECUTIVE REPORT", "Executive details."]
    }


class EchoContextAssemblerTests(unittest.TestCase):

    def test_empty_inputs_do_not_crash(self):

        assembly = assemble_echo_context("", {}, {}, {}, {})

        self.assertEqual("1.0", assembly["schema_version"])
        self.assertTrue(assembly["context_blocks"])

    def test_minimal_budget_includes_no_full_reports(self):

        assembly = assemble_echo_context(
            "hello",
            _memory(),
            _budget("minimal", "simple", 5),
            _routing(),
            _reports()
        )

        self.assertEqual("minimal", assembly["assembly_mode"])
        self.assertFalse(
            assembly["context_summary"]["full_reports_included"]
        )

    def test_memory_meta_query_uses_memory_only_mode(self):

        assembly = assemble_echo_context(
            "what changed?",
            _memory(),
            _budget("standard", "memory"),
            {"routing_mode": "none", "excluded_agents": ["portfolio"]},
            _reports()
        )

        self.assertEqual("memory_only", assembly["assembly_mode"])

    def test_portfolio_agent_focused_query_includes_portfolio_when_allowed(self):

        assembly = assemble_echo_context(
            "portfolio risk",
            _memory(),
            _budget("expanded"),
            _routing("portfolio", True),
            _reports()
        )
        sources = {block["source"] for block in assembly["context_blocks"]}

        self.assertIn("portfolio_report", sources)

    def test_excluded_agent_report_is_not_included(self):

        assembly = assemble_echo_context(
            "portfolio risk",
            _memory(),
            _budget("expanded"),
            _routing("portfolio", True),
            _reports()
        )
        sources = {block["source"] for block in assembly["context_blocks"]}

        self.assertNotIn("research_report", sources)

    def test_max_context_items_caps_blocks(self):

        assembly = assemble_echo_context(
            "portfolio risk",
            _memory(),
            _budget("expanded", "agent_specific", 1),
            _routing("portfolio", True),
            _reports()
        )

        self.assertLessEqual(len(assembly["context_blocks"]), 1)

    def test_investment_query_prioritizes_live_research_over_legacy(self):

        reports = {
            "security_resolution": {"resolved": True, "selected_security": {"ticker": "SMCI"}},
            "live_research": {"profiles": [{"ticker": "SMCI"}]},
            "thesis_refresh": {"thesis_refreshes": [{"ticker": "SMCI"}]},
            "research_evidence_store": {"profiles": [{"ticker": "SMCI"}]},
            "security_intelligence": {"profiles": [{"ticker": "SMCI"}]},
            "research_snapshot": {"summary": "legacy low conviction"}
        }
        budget = _budget("standard", "ticker_question", 20)
        budget["preferred_context_sources"] = [
            "security_resolution",
            "live_research",
            "thesis_refresh",
            "research_evidence_store",
            "security_intelligence",
            "research_snapshot"
        ]
        assembly = assemble_echo_context(
            "research SMCI",
            _memory(),
            budget,
            {"routing_mode": "live_security_research", "excluded_agents": []},
            reports
        )
        priorities = {
            block["source"]: block["priority"]
            for block in assembly["context_blocks"]
        }

        self.assertEqual("investment_query", assembly["assembly_mode"])
        self.assertEqual("Security Resolution", assembly["context_blocks"][0]["title"])
        self.assertGreater(priorities["live_research"], priorities["research_snapshot"])
        self.assertGreater(priorities["security_resolution"], priorities["live_research"])

    def test_security_resolution_query_prioritizes_resolution_block(self):

        reports = {
            "security_resolution": {
                "resolved": True,
                "selected_security": {"ticker": "SPCX"}
            },
            "security_master_search": {"matches": [{"ticker": "SPCX"}]},
            "market_coverage": {"coverage_universe": [{"ticker": "SPCX"}]},
            "live_research": {"profiles": [{"ticker": "SPCX"}]},
            "research_evidence_store": {"profiles": [{"ticker": "SPCX"}]},
            "thesis_refresh": {"thesis_refreshes": [{"ticker": "SPCX"}]},
            "security_intelligence": {"profiles": [{"ticker": "SPCX"}]}
        }
        budget = _budget("standard", "security_resolution", 20)
        budget["preferred_context_sources"] = [
            "security_resolution",
            "security_master_search",
            "market_coverage",
            "live_research",
            "research_evidence_store",
            "thesis_refresh",
            "security_intelligence"
        ]

        assembly = assemble_echo_context(
            "resolve SPCX",
            _memory(),
            budget,
            {"routing_mode": "security_resolution", "excluded_agents": []},
            reports
        )

        self.assertEqual("investment_query", assembly["assembly_mode"])
        self.assertEqual("security_resolution", assembly["context_blocks"][0]["source"])
        self.assertEqual("Security Resolution", assembly["context_blocks"][0]["title"])

    def test_json_serializable(self):

        assembly = assemble_echo_context(
            "portfolio risk",
            _memory(),
            _budget("expanded"),
            _routing("portfolio", True),
            _reports()
        )

        json.dumps(assembly)

    def test_output_files_written(self):

        assembly = assemble_echo_context(
            "portfolio risk",
            _memory(),
            _budget("expanded"),
            _routing("portfolio", True),
            _reports()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_context_assembly.json"
            text_path = Path(temp_dir) / "echo_context_assembly.txt"

            json_result = write_context_assembly_json(assembly, json_path)
            text_result = write_context_assembly_text(assembly, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
