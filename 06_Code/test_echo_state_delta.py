import json
import unittest

from echo_state_delta import build_echo_state_delta


def _state(priority="Risk A", risks=None):

    risk_register = [
        {
            "source": "top_priority",
            "severity": "HIGH",
            "title": priority,
            "reason": "Risk reason"
        }
    ] if risks is None else risks

    return {
        "schema_version": "1.0",
        "generated_at": "2026-01-01T00:00:00",
        "top_priority": {
            "title": priority,
            "severity": "HIGH",
            "source_agent": "Portfolio Manager"
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
            }
        },
        "research": {},
        "news": {
            "top_narrative": {
                "title": "Narrative A"
            }
        },
        "macro": {
            "regime": {
                "name": "Regime A"
            }
        },
        "conflicts": [],
        "action_queue": [
            "Review Risk A"
        ],
        "risk_register": risk_register
    }


class EchoStateDeltaTests(unittest.TestCase):

    def test_no_previous_state_does_not_crash(self):

        delta = build_echo_state_delta(None, _state())

        self.assertFalse(delta["has_previous_state"])
        self.assertEqual(0, delta["summary"]["material_change_count"])
        json.dumps(delta)

    def test_identical_states_have_zero_material_changes(self):

        state = _state()
        delta = build_echo_state_delta(state, state)

        self.assertTrue(delta["has_previous_state"])
        self.assertEqual(0, delta["summary"]["material_change_count"])
        self.assertEqual([], delta["changes"])

    def test_changed_top_priority_is_material(self):

        delta = build_echo_state_delta(_state("Risk A"), _state("Risk B"))

        self.assertIsNotNone(delta["priority_change"])
        self.assertGreaterEqual(delta["summary"]["material_change_count"], 1)
        self.assertIn(
            "top_priority",
            {change["field"] for change in delta["material_changes"]}
        )

    def test_new_risk_appears(self):

        previous = _state(risks=[])
        current = _state(risks=[
            {
                "source": "macro",
                "severity": "HIGH",
                "title": "New Macro Risk",
                "reason": "New risk"
            }
        ])
        delta = build_echo_state_delta(previous, current)

        self.assertEqual("New Macro Risk", delta["new_risks"][0]["title"])
        self.assertTrue(delta["material_changes"])

    def test_resolved_risk_appears(self):

        previous = _state(risks=[
            {
                "source": "macro",
                "severity": "HIGH",
                "title": "Old Macro Risk",
                "reason": "Old risk"
            }
        ])
        current = _state(risks=[])
        delta = build_echo_state_delta(previous, current)

        self.assertEqual("Old Macro Risk", delta["resolved_risks"][0]["title"])
        self.assertTrue(delta["material_changes"])

    def test_delta_is_json_serializable(self):

        json.dumps(build_echo_state_delta(_state(), _state("Risk B")))


if __name__ == "__main__":
    unittest.main()
