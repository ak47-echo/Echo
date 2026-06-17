import json
import tempfile
import unittest
from pathlib import Path

from echo_context_budget import (
    build_context_budget,
    write_context_budget_json,
    write_context_budget_text
)


def _memory_context():

    return {
        "schema_version": "1.0",
        "context_mode": "memory_first",
        "context_budget": {
            "max_items": 20,
            "included_items": 12,
            "excluded_items": 0
        },
        "summary": {
            "top_priority": "Review concentration risk"
        }
    }


class EchoContextBudgetTests(unittest.TestCase):

    def test_greeting_becomes_simple_minimal(self):

        budget = build_context_budget("hello", _memory_context())

        self.assertEqual("simple", budget["query_class"])
        self.assertEqual("minimal", budget["budget_level"])

    def test_what_changed_becomes_memory_standard(self):

        budget = build_context_budget("what changed today?", _memory_context())

        self.assertEqual("memory", budget["query_class"])
        self.assertEqual("standard", budget["budget_level"])
        self.assertIn("change_detection", budget["preferred_context_sources"])

    def test_portfolio_query_becomes_agent_specific(self):

        budget = build_context_budget(
            "what is the portfolio risk?",
            _memory_context()
        )

        self.assertEqual("agent_specific", budget["query_class"])
        self.assertIn("portfolio_snapshot", budget["preferred_context_sources"])

    def test_broad_synthesis_query_becomes_multi_agent(self):

        budget = build_context_budget(
            "synthesize portfolio macro and news risk",
            _memory_context()
        )

        self.assertEqual("multi_agent", budget["query_class"])
        self.assertEqual("expanded", budget["budget_level"])

    def test_deep_dive_query_becomes_deep_dive_full(self):

        budget = build_context_budget(
            "give me a detailed full breakdown of the portfolio risk",
            _memory_context()
        )

        self.assertEqual("deep_dive", budget["query_class"])
        self.assertEqual("full", budget["budget_level"])

    def test_json_serializable(self):

        budget = build_context_budget("what matters?", _memory_context())

        json.dumps(budget)

    def test_output_files_written(self):

        budget = build_context_budget("what matters?", _memory_context())

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_context_budget.json"
            text_path = Path(temp_dir) / "echo_context_budget.txt"

            json_result = write_context_budget_json(budget, json_path)
            text_result = write_context_budget_text(budget, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
