import json
import tempfile
import unittest
from pathlib import Path

from echo_response_composer import (
    RAW_TOOL_NAMES,
    compose_echo_response,
    write_response_composer_json,
    write_response_composer_text
)


def _memory(material_changes=None):

    return {
        "summary": {
            "top_priority": "UNH position concentration 45.1%",
            "change_level": "moderate",
            "top_signal": "Energy: RISING",
            "dominant_theme": "Inflation/Energy Risk",
            "material_change_count": len(material_changes or []),
            "persistent_issue_count": 3
        },
        "operating_context": {
            "current_state": {
                "top_priority": {
                    "title": "UNH position concentration 45.1%",
                    "reason": "HIGH | UNH | Position concentration 45.1%"
                },
                "portfolio_current_risk": {
                    "title": "UNH position concentration 45.1%"
                },
                "portfolio_worst_stress_scenario": {
                    "title": "2008_STYLE_CRISIS | Impact -50.12%"
                },
                "macro_regime": {
                    "name": "Inflation Stress",
                    "reason": "Inflation can reprice Fed expectations."
                },
                "news_top_narrative": {
                    "title": "Middle East Energy Risk",
                    "reason": "Energy-linked geopolitical narrative."
                }
            },
            "important_changes": material_changes or [],
            "persistent_patterns": [
                {
                    "label": "Energy: RISING",
                    "metadata": {"reason": "Risk appears in history."}
                },
                {
                    "label": "Growth exposure conflicts with inflation/rates theme"
                }
            ],
            "recommended_attention": [
                {"label": "Energy: RISING"},
                {"label": "Inflation Trend: RISING"}
            ],
            "top_signals": [
                {"label": "Energy: RISING"}
            ]
        }
    }


def _budget(query_class="memory", level="standard"):

    return {
        "query_class": query_class,
        "budget_level": level,
        "max_context_items": 20
    }


def _routing(primary=None, mode="none"):

    primary = primary or []

    return {
        "primary_agents": primary,
        "secondary_agents": [],
        "excluded_agents": [
            agent
            for agent in ("portfolio", "research", "news", "macro")
            if agent not in primary
        ],
        "routing_mode": mode,
        "agent_context_plan": []
    }


def _assembly(source="memory_context"):

    return {
        "assembly_mode": "memory_only",
        "context_blocks": [
            {
                "source": source,
                "role": "primary",
                "title": "Memory Summary",
                "content": "Clean compact context",
                "priority": 100
            }
        ],
        "context_summary": {
            "full_reports_included": False,
            "block_count": 1
        }
    }


def _portfolio_change_assembly():

    report = {
        "summary": {
            "change_count": 1,
            "material_change_count": 1,
            "total_market_value_change": 250.0,
            "top_change": {
                "account": "Brokerage",
                "ticker": "AVUV",
                "delta_market_value": 250.0
            }
        },
        "new_positions": [
            {
                "account": "Brokerage",
                "ticker": "AVUV",
                "current_market_value": 250.0,
                "material": True
            }
        ],
        "removed_positions": [],
        "quantity_changes": [],
        "market_value_changes": [],
        "concentration_changes": [],
        "cash_changes": []
    }

    return {
        "assembly_mode": "portfolio_change",
        "context_blocks": [
            {
                "source": "portfolio_change_detection",
                "role": "primary",
                "title": "Portfolio Change Detection",
                "content": json.dumps(report),
                "priority": 120
            }
        ],
        "context_summary": {
            "full_reports_included": False,
            "block_count": 1
        }
    }


def _custom_block_assembly(source, payload, mode="investment_query"):

    return {
        "assembly_mode": mode,
        "context_blocks": [
            {
                "source": source,
                "role": "primary",
                "title": source,
                "content": json.dumps(payload),
                "priority": 120
            }
        ],
        "context_summary": {
            "full_reports_included": False,
            "block_count": 1
        }
    }


def _portfolio_change_report(**updates):

    report = {
        "summary": {
            "change_count": 0,
            "material_change_count": 0,
            "total_market_value_change": 0,
            "top_change": None
        },
        "new_positions": [],
        "removed_positions": [],
        "quantity_changes": [],
        "market_value_changes": [],
        "concentration_changes": [],
        "cash_changes": []
    }
    report.update(updates)
    return _custom_block_assembly(
        "portfolio_change_detection",
        report,
        "portfolio_change"
    )

class EchoResponseComposerTests(unittest.TestCase):

    def _assert_no_tool_names(self, answer):

        for tool_name in RAW_TOOL_NAMES:
            self.assertNotIn(tool_name, answer)

    def test_top_priority_query_returns_clean_answer_without_tool_names(self):

        response = compose_echo_response(
            "what's the biggest issue?",
            _budget(),
            _routing(),
            _assembly(),
            _memory()
        )

        self.assertEqual("memory", response["response_mode"])
        self.assertIn("UNH position concentration", response["answer"])
        self._assert_no_tool_names(response["answer"])

    def test_what_changed_query_with_no_material_changes_says_none(self):

        response = compose_echo_response(
            "anything new?",
            _budget(),
            _routing(),
            _assembly(),
            _memory([])
        )

        self.assertIn("No material changes", response["answer"])

    def test_persistent_query_mentions_persistent_risks(self):

        response = compose_echo_response(
            "what keeps showing up?",
            _budget(),
            _routing(),
            _assembly(),
            _memory()
        )

        self.assertIn("Energy: RISING", response["answer"])

    def test_portfolio_query_returns_agent_summary_mode(self):

        response = compose_echo_response(
            "give me a portfolio-only summary",
            _budget("agent_specific", "expanded"),
            _routing(["portfolio"], "single_agent"),
            _assembly("portfolio_report"),
            _memory()
        )

        self.assertEqual("agent_summary", response["response_mode"])
        self.assertIn("Portfolio read", response["answer"])

    def test_portfolio_change_query_uses_change_detection_context(self):

        response = compose_echo_response(
            "what are my new positions from last report",
            _budget("portfolio_change", "standard"),
            _routing(["portfolio"], "single_agent"),
            _portfolio_change_assembly(),
            _memory([])
        )

        self.assertEqual("memory", response["response_mode"])
        self.assertIn("AVUV", response["answer"])
        self.assertTrue(
            any("Brokerage AVUV" in point for point in response["supporting_points"])
        )

    def test_price_only_movement_does_not_become_generic_risk(self):

        response = compose_echo_response(
            "what changed in my portfolio now",
            _budget("portfolio_change", "standard"),
            _routing(["portfolio"], "single_agent"),
            _portfolio_change_report(
                summary={"change_count": 1, "material_change_count": 1},
                market_value_changes=[{
                    "account": "Brokerage",
                    "ticker": "SMCI",
                    "delta_market_value": 120.0
                }]
            ),
            _memory([])
        )

        self.assertIn("No new positions", response["answer"])
        self.assertNotIn("Portfolio read", response["answer"])

    def test_removed_position_question_lists_removed_positions(self):

        response = compose_echo_response(
            "what did I sell",
            _budget("portfolio_change", "standard"),
            _routing(["portfolio"], "single_agent"),
            _portfolio_change_report(
                removed_positions=[{
                    "account": "Brokerage",
                    "ticker": "MSTR",
                    "previous_quantity": 1,
                    "previous_market_value": 100
                }]
            ),
            _memory([])
        )

        self.assertIn("MSTR", response["answer"])
        self.assertIn("qty 1", response["answer"])

    def test_cash_change_question_uses_cash_changes(self):

        response = compose_echo_response(
            "did my cash change",
            _budget("portfolio_change", "standard"),
            _routing(["portfolio"], "single_agent"),
            _portfolio_change_report(
                cash_changes=[{
                    "account": "Brokerage",
                    "ticker": "CASH0",
                    "delta_cash": 150
                }]
            ),
            _memory([])
        )

        self.assertIn("Cash changes", response["answer"])
        self.assertIn("CASH0", response["answer"])

    def test_concentration_question_uses_concentration_changes(self):

        response = compose_echo_response(
            "did my UNH concentration change",
            _budget("portfolio_change", "standard"),
            _routing(["portfolio"], "single_agent"),
            _portfolio_change_report(
                concentration_changes=[{
                    "account": "Brokerage",
                    "ticker": "UNH",
                    "previous_weight": 40,
                    "current_weight": 41.5,
                    "delta_weight": 1.5
                }]
            ),
            _memory([])
        )

        self.assertIn("40.00%", response["answer"])
        self.assertIn("41.50%", response["answer"])

    def test_security_master_response(self):

        response = compose_echo_response(
            "small cap value ETFs",
            _budget("security_master_search", "standard"),
            _routing(["research"], "investment_query"),
            _custom_block_assembly(
                "security_master_search",
                {
                    "matches": [{
                        "ticker": "AVUV",
                        "name": "Avantis US Small Cap Value ETF",
                        "category": "US Small Value",
                        "expense_ratio": 0.0025
                    }],
                    "match_count": 1,
                    "warnings": []
                }
            ),
            _memory([])
        )

        self.assertIn("AVUV", response["answer"])
        self.assertIn("expense ratio", response["answer"])

    def test_ticker_response_handles_nonheld_security(self):

        response = compose_echo_response(
            "what do you think about NVDA",
            _budget("ticker_question", "standard"),
            _routing(["research"], "investment_query"),
            _custom_block_assembly(
                "security_master_search",
                {
                    "matches": [{
                        "ticker": "NVDA",
                        "name": "Nvidia Corp",
                        "category": "US Large Growth",
                        "expense_ratio": 0.0,
                        "match_reason": "security_master:ticker"
                    }],
                    "match_count": 1,
                    "warnings": []
                }
            ),
            _memory([])
        )

        self.assertIn("not currently held", response["answer"])
        self.assertIn("NVDA", response["answer"])

    def test_market_scan_response_is_research_only(self):

        response = compose_echo_response(
            "what stocks could go up from this news",
            _budget("market_opportunities", "expanded"),
            _routing(["research"], "investment_query"),
            _custom_block_assembly(
                "market_opportunity_scan",
                {
                    "opportunity_candidates": [{
                        "ticker": "AVUV",
                        "direction": "watch",
                        "reason": "Watchlist candidate."
                    }],
                    "risk_candidates": [],
                    "warnings": []
                }
            ),
            _memory([])
        )

        self.assertIn("AVUV", response["answer"])
        self.assertIn("no trades", response["answer"])

    def test_paper_allocation_future_placeholder(self):

        response = compose_echo_response(
            "if I gave Echo $1000 to allocate on paper, what would it do?",
            _budget("paper_allocation_future", "minimal"),
            _routing(["research"], "investment_query"),
            _assembly(),
            _memory([])
        )

        self.assertIn("future Echo mode", response["answer"])
        self.assertIn("No real trades", response["answer"])

    def test_macro_risk_query_returns_summary_mode(self):

        response = compose_echo_response(
            "how exposed am I to macro risk?",
            _budget("agent_specific", "expanded"),
            _routing(["macro"], "single_agent"),
            _assembly("macro_report"),
            _memory()
        )

        self.assertIn(
            response["response_mode"],
            {"agent_summary", "multi_agent_summary"}
        )
        self.assertIn("Inflation Stress", response["answer"])

    def test_missing_context_returns_fallback_without_crash(self):

        response = compose_echo_response(
            "something unrelated",
            None,
            None,
            None,
            None
        )

        self.assertEqual("fallback", response["response_mode"])
        self.assertTrue(response["answer"])

    def test_debug_summary_contains_routing_budget_info(self):

        response = compose_echo_response(
            "what changed?",
            _budget("memory", "standard"),
            _routing(),
            _assembly(),
            _memory()
        )
        debug = response["debug_summary"]

        self.assertEqual("memory", debug["query_class"])
        self.assertEqual("standard", debug["budget_level"])
        self.assertEqual("none", debug["routing_mode"])

    def test_answer_never_includes_raw_tool_names(self):

        response = compose_echo_response(
            "what should I care about right now?",
            _budget(),
            _routing(),
            _assembly(),
            _memory()
        )

        self._assert_no_tool_names(response["answer"])

    def test_json_serializable(self):

        response = compose_echo_response(
            "overall picture",
            _budget("multi_agent", "expanded"),
            _routing(["portfolio", "macro", "news", "research"], "all_agents"),
            _assembly(),
            _memory()
        )

        json.dumps(response)

    def test_output_files_written(self):

        response = compose_echo_response(
            "top priority",
            _budget(),
            _routing(),
            _assembly(),
            _memory()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_response_composer.json"
            text_path = Path(temp_dir) / "echo_response_composer.txt"

            json_result = write_response_composer_json(response, json_path)
            text_result = write_response_composer_text(response, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
