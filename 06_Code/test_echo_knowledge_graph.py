import json
import tempfile
import unittest
from pathlib import Path

from echo_knowledge_graph import (
    build_echo_knowledge_graph,
    write_knowledge_graph_json,
    write_knowledge_graph_text
)


def _state():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "top_priority": {
            "title": "Review Concentration Risk",
            "severity": "HIGH"
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
            },
            "concentration_flags": [
                {
                    "severity": "HIGH",
                    "ticker": "NVDA",
                    "description": "Large single-name exposure"
                }
            ],
            "weak_holdings": ["SMCI weak thesis"]
        },
        "research": {
            "top_convictions": [
                {
                    "ticker": "MSFT",
                    "basis": "Highest conviction holding"
                }
            ],
            "weak_coverage": [
                {
                    "area": "Uncovered Holdings",
                    "items": ["SMCI"]
                }
            ],
            "watchlist_priorities": ["Review AI infrastructure watchlist"]
        },
        "news": {
            "top_narrative": {
                "title": "AI capex concern"
            },
            "market_significant_items": [
                {
                    "title": "Rates pressure hits growth"
                }
            ],
            "portfolio_relevant_items": ["NVDA valuation pressure"]
        },
        "macro": {
            "regime": {
                "name": "Restrictive Rates"
            },
            "top_macro_risks": [
                {
                    "title": "Higher-for-longer rates",
                    "fields": {
                        "Priority Tier": "HIGH"
                    }
                }
            ]
        },
        "conflicts": [
            {
                "conflict_title": "Conviction versus concentration"
            }
        ],
        "action_queue": [
            "Review Concentration Risk"
        ],
        "risk_register": [
            {
                "source": "portfolio",
                "severity": "HIGH",
                "title": "Concentration Risk",
                "reason": "Large single-name exposure"
            },
            {
                "source": "duplicate",
                "severity": "HIGH",
                "title": "Concentration Risk",
                "reason": "Duplicate risk"
            }
        ]
    }


def _delta():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "summary": {
            "material_change_count": 1
        },
        "new_risks": [
            {
                "source": "portfolio",
                "severity": "HIGH",
                "title": "Concentration Risk"
            }
        ],
        "resolved_risks": []
    }


def _history():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "persistent_risks": [
            {
                "source": "portfolio",
                "severity": "HIGH",
                "title": "Concentration Risk",
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

    signal = {
        "type": "new_risk",
        "category": "risk",
        "name": "Concentration Risk",
        "description": "New high priority risk appeared.",
        "score": 40,
        "source": "delta",
        "is_material": True
    }

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "priority_signals": [],
        "risk_signals": [signal],
        "macro_signals": [],
        "portfolio_signals": [],
        "news_signals": [],
        "action_signals": [],
        "escalations": [signal],
        "deescalations": []
    }


class EchoKnowledgeGraphTests(unittest.TestCase):

    def test_empty_inputs_do_not_crash(self):

        graph = build_echo_knowledge_graph({}, {}, {}, {})

        self.assertEqual("1.0", graph["schema_version"])
        self.assertGreaterEqual(graph["summary"]["node_count"], 5)

    def test_required_top_level_keys_exist(self):

        graph = build_echo_knowledge_graph(
            _state(),
            _delta(),
            _history(),
            _change_detection()
        )

        for key in (
            "schema_version",
            "generated_at",
            "summary",
            "nodes",
            "edges",
            "clusters",
            "entity_index",
            "relationship_index"
        ):
            self.assertIn(key, graph)

    def test_duplicate_nodes_are_merged(self):

        graph = build_echo_knowledge_graph(
            _state(),
            _delta(),
            _history(),
            _change_detection()
        )
        concentration_nodes = [
            node for node in graph["nodes"]
            if (
                node["type"] == "risk"
                and node["label"] == "Concentration Risk"
            )
        ]

        self.assertEqual(1, len(concentration_nodes))
        self.assertGreater(concentration_nodes[0]["weight"], 10)

    def test_required_agent_nodes_exist(self):

        graph = build_echo_knowledge_graph({}, {}, {}, {})
        agent_labels = {
            node["label"]
            for node in graph["nodes"]
            if node["type"] == "agent"
        }

        self.assertTrue(
            {
                "Echo",
                "Portfolio Agent",
                "Research Agent",
                "News Agent",
                "Macro Agent"
            }.issubset(agent_labels)
        )

    def test_edges_are_created_between_echo_and_agents(self):

        graph = build_echo_knowledge_graph({}, {}, {}, {})
        edge_pairs = {
            (edge["source"], edge["target"], edge["relationship"])
            for edge in graph["edges"]
        }

        self.assertIn(
            ("agent:echo", "agent:portfolio_agent", "relates_to"),
            edge_pairs
        )
        self.assertIn(
            ("agent:portfolio_agent", "agent:echo", "belongs_to"),
            edge_pairs
        )

    def test_graph_json_is_serializable(self):

        graph = build_echo_knowledge_graph(
            _state(),
            _delta(),
            _history(),
            _change_detection()
        )

        json.dumps(graph)

    def test_output_files_are_written(self):

        graph = build_echo_knowledge_graph(
            _state(),
            _delta(),
            _history(),
            _change_detection()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_knowledge_graph.json"
            text_path = Path(temp_dir) / "echo_knowledge_graph.txt"

            json_result = write_knowledge_graph_json(graph, json_path)
            text_result = write_knowledge_graph_text(graph, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
