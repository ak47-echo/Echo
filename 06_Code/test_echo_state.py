import json
import tempfile
import unittest
from pathlib import Path

from echo_state import (
    REQUIRED_TOP_LEVEL_KEYS,
    build_echo_state,
    validate_echo_state,
    write_echo_state
)


class EchoStateTests(unittest.TestCase):

    def test_state_has_required_keys_and_is_json_serializable(self):

        state = build_echo_state({
            "sections": {
                "executive_summary": [
                    "Top Priority: Concentration risk",
                    "Dominant Cross-Agent Theme: Portfolio Concentration Risk",
                    "Priority Action Queue:",
                    "1. Review concentration risk"
                ],
                "priority_summary": [
                    "Top Priority: Concentration risk",
                    "Priority Source: Portfolio Manager"
                ]
            }
        })

        self.assertTrue(validate_echo_state(state))
        self.assertEqual(set(REQUIRED_TOP_LEVEL_KEYS), set(state.keys()))
        json.dumps(state)

    def test_missing_agent_sections_do_not_crash(self):

        state = build_echo_state({})

        self.assertTrue(validate_echo_state(state))
        self.assertIsNone(state["top_priority"])
        self.assertEqual([], state["conflicts"])
        self.assertEqual([], state["action_queue"])

    def test_state_files_are_written(self):

        state = build_echo_state({})

        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_echo_state(state, reports_dir=temp_dir)

            self.assertTrue(result["success"])
            self.assertTrue((Path(temp_dir) / "echo_state.json").exists())
            self.assertTrue((Path(temp_dir) / "echo_state.txt").exists())


if __name__ == "__main__":
    unittest.main()
