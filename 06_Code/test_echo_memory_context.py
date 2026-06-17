import json
import tempfile
import unittest
from pathlib import Path

from echo_memory_context import (
    build_echo_memory_context,
    write_memory_context_json,
    write_memory_context_text
)


def _state():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "top_priority": {
            "title": "Review Concentration Risk"
        },
        "dominant_theme": {
            "theme_title": "Portfolio Concentration Risk"
        },
        "portfolio": {
            "current_risk": {
                "title": "Concentration Risk"
            },
            "worst_stress_scenario": {
                "title": "Growth Shock"
            }
        },
        "macro": {
            "regime": {
                "name": "Restrictive Rates"
            }
        },
        "news": {
            "top_narrative": {
                "title": "Rates pressure narrative"
            }
        }
    }


def _delta():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "material_changes": [
            {
                "field": "top_priority",
                "previous": "Old Risk",
                "current": "Review Concentration Risk"
            }
        ],
        "new_risks": [
            {
                "title": "Concentration Risk",
                "severity": "HIGH"
            }
        ],
        "resolved_risks": [
            {
                "title": "Old Risk",
                "severity": "MEDIUM"
            }
        ]
    }


def _history():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "persistent_risks": [
            {
                "title": "Persistent Risk",
                "count": 3
            }
        ],
        "persistent_actions": [
            {
                "action": "Review Concentration Risk",
                "count": 2
            }
        ]
    }


def _change_detection():

    top_signal = {
        "type": "new_risk",
        "category": "risk",
        "name": "Concentration Risk",
        "score": 40,
        "description": "New risk appeared."
    }

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "summary": {
            "change_level": "high",
            "top_signal": top_signal,
            "material_change_count": 1,
            "persistent_issue_count": 1
        },
        "priority_signals": [],
        "risk_signals": [top_signal],
        "macro_signals": [],
        "portfolio_signals": [],
        "news_signals": [],
        "action_signals": [],
        "recommended_attention": [
            {
                "category": "risk",
                "name": "Concentration Risk",
                "score": 40,
                "description": "Review concentration."
            }
        ]
    }


def _knowledge_graph():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "summary": {
            "node_count": 3,
            "edge_count": 2,
            "dominant_cluster": "cluster:1",
            "top_connected_nodes": [
                {
                    "id": "risk:concentration_risk",
                    "label": "Concentration Risk",
                    "type": "risk",
                    "degree": 4,
                    "weight": 30
                }
            ]
        },
        "clusters": [
            {
                "id": "cluster:1",
                "label": "Concentration Risk",
                "node_ids": ["risk:concentration_risk"],
                "total_weight": 30,
                "primary_node": "risk:concentration_risk"
            }
        ]
    }


class EchoMemoryContextTests(unittest.TestCase):

    def test_empty_inputs_do_not_crash(self):

        memory = build_echo_memory_context({}, {}, {}, {}, {})

        self.assertEqual("1.0", memory["schema_version"])
        self.assertEqual("memory_first", memory["context_mode"])

    def test_required_top_level_keys_exist(self):

        memory = build_echo_memory_context(
            _state(),
            _delta(),
            _history(),
            _change_detection(),
            _knowledge_graph()
        )

        for key in (
            "schema_version",
            "generated_at",
            "context_mode",
            "summary",
            "operating_context",
            "context_budget",
            "source_artifacts"
        ):
            self.assertIn(key, memory)

    def test_max_items_caps_included_items(self):

        memory = build_echo_memory_context(
            _state(),
            _delta(),
            _history(),
            _change_detection(),
            _knowledge_graph(),
            max_items=3
        )

        self.assertLessEqual(
            memory["context_budget"]["included_items"],
            3
        )
        self.assertGreater(memory["context_budget"]["excluded_items"], 0)

    def test_source_artifacts_reflects_missing_and_present_artifacts(self):

        memory = build_echo_memory_context(
            _state(),
            {},
            _history(),
            {},
            _knowledge_graph()
        )

        self.assertTrue(memory["source_artifacts"]["state"])
        self.assertFalse(memory["source_artifacts"]["delta"])
        self.assertTrue(memory["source_artifacts"]["history"])
        self.assertFalse(memory["source_artifacts"]["change_detection"])
        self.assertTrue(memory["source_artifacts"]["knowledge_graph"])

    def test_json_output_serializable(self):

        memory = build_echo_memory_context(
            _state(),
            _delta(),
            _history(),
            _change_detection(),
            _knowledge_graph()
        )

        json.dumps(memory)

    def test_output_files_are_written(self):

        memory = build_echo_memory_context(
            _state(),
            _delta(),
            _history(),
            _change_detection(),
            _knowledge_graph()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_memory_context.json"
            text_path = Path(temp_dir) / "echo_memory_context.txt"

            json_result = write_memory_context_json(memory, json_path)
            text_result = write_memory_context_text(memory, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())

    def test_memory_context_includes_top_priority_when_present(self):

        memory = build_echo_memory_context(
            _state(),
            _delta(),
            _history(),
            _change_detection(),
            _knowledge_graph()
        )

        self.assertEqual(
            "Review Concentration Risk",
            memory["summary"]["top_priority"]
        )

    def test_memory_context_includes_recommended_attention_when_present(self):

        memory = build_echo_memory_context(
            _state(),
            _delta(),
            _history(),
            _change_detection(),
            _knowledge_graph(),
            max_items=20
        )

        attention = memory["operating_context"]["recommended_attention"]

        self.assertTrue(attention)
        self.assertEqual("Concentration Risk", attention[0]["label"])


if __name__ == "__main__":
    unittest.main()
