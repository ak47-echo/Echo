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
