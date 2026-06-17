import json
import unittest

from echo_change_detection import build_echo_change_detection


def _state(priority="Risk A"):

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "top_priority": {
            "title": priority
        },
        "dominant_theme": {
            "theme_title": "Theme A"
        },
        "portfolio": {
            "current_risk": {
                "title": "Portfolio Risk A"
            },
            "worst_stress_scenario": {
                "title": "Stress A"
            },
            "concentration_flags": []
        },
        "news": {
            "top_narrative": {
                "title": "Narrative A"
            },
            "market_significant_items": [],
            "portfolio_relevant_items": []
        },
        "macro": {
            "regime": {
                "name": "Regime A"
            }
        },
        "risk_register": [],
        "action_queue": []
    }


def _delta():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "has_previous_state": True,
        "summary": {
            "change_count": 0,
            "material_change_count": 0,
            "top_change": None
        },
        "changes": [],
        "material_changes": [],
        "new_risks": [],
        "resolved_risks": [],
        "priority_change": None,
        "theme_change": None,
        "macro_regime_change": None,
        "portfolio_risk_change": None,
        "stress_scenario_change": None,
        "news_narrative_change": None
    }


def _history():

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-02T00:00:00",
        "sample_count": 1,
        "risk_frequency": [],
        "action_frequency": [],
        "persistent_risks": [],
        "persistent_actions": [],
        "state_stability": {
            "priority_changed_count": 0,
            "theme_changed_count": 0,
            "macro_regime_changed_count": 0,
            "portfolio_risk_changed_count": 0
        },
        "summary": {
            "dominant_persistent_risk": None,
            "dominant_persistent_action": None,
            "most_common_priority": None,
            "most_common_theme": None,
            "most_common_macro_regime": None,
            "most_common_portfolio_risk": None
        }
    }


class EchoChangeDetectionTests(unittest.TestCase):

    def test_no_changes_produces_none_or_low_level(self):

        detection = build_echo_change_detection(_state(), _delta(), _history())

        self.assertIn(
            detection["summary"]["change_level"],
            {"none", "low"}
        )

    def test_priority_change_creates_high_scoring_priority_signal(self):

        delta = _delta()
        delta["summary"]["material_change_count"] = 1
        delta["priority_change"] = {
            "change_type": "changed",
            "field": "top_priority",
            "previous": "Risk A",
            "current": "Risk B",
            "material": True,
            "reason": "Top priority changed."
        }

        detection = build_echo_change_detection(
            _state(priority="Risk B"),
            delta,
            _history()
        )

        self.assertGreaterEqual(
            detection["priority_signals"][0]["score"],
            50
        )
        self.assertEqual("high", detection["summary"]["change_level"])

    def test_new_risk_creates_risk_signal(self):

        delta = _delta()
        delta["new_risks"] = [
            {
                "source": "test",
                "severity": "MEDIUM",
                "title": "New Risk",
                "reason": "Risk reason"
            }
        ]

        detection = build_echo_change_detection(_state(), delta, _history())

        self.assertEqual("new_risk", detection["risk_signals"][0]["type"])
        self.assertEqual("New Risk", detection["risk_signals"][0]["name"])

    def test_persistent_risk_creates_persistent_signal(self):

        history = _history()
        history["sample_count"] = 3
        history["persistent_risks"] = [
            {
                "source": "test",
                "severity": "HIGH",
                "title": "Persistent Risk",
                "reason": "Risk reason",
                "count": 3
            }
        ]

        detection = build_echo_change_detection(_state(), _delta(), history)

        self.assertTrue(detection["persistent_signals"])
        self.assertEqual(
            "Persistent Risk",
            detection["persistent_signals"][0]["name"]
        )

    def test_resolved_risk_creates_deescalation(self):

        delta = _delta()
        delta["resolved_risks"] = [
            {
                "source": "test",
                "severity": "HIGH",
                "title": "Resolved Risk",
                "reason": "Risk reason"
            }
        ]

        detection = build_echo_change_detection(_state(), delta, _history())

        self.assertTrue(detection["deescalations"])
        self.assertEqual(
            "Resolved Risk",
            detection["deescalations"][0]["name"]
        )

    def test_recommended_attention_is_capped_at_five(self):

        delta = _delta()
        delta["new_risks"] = [
            {
                "source": "test",
                "severity": "MEDIUM",
                "title": f"New Risk {index}",
                "reason": "Risk reason"
            }
            for index in range(10)
        ]

        detection = build_echo_change_detection(_state(), delta, _history())

        self.assertEqual(5, len(detection["recommended_attention"]))

    def test_change_detection_is_json_serializable(self):

        detection = build_echo_change_detection(_state(), _delta(), _history())

        json.dumps(detection)


if __name__ == "__main__":
    unittest.main()
