import json
import tempfile
import unittest
from pathlib import Path

from echo_state_history import (
    build_echo_state_history,
    write_state_history_json,
    write_state_history_text
)


def _state(generated_at, priority="Risk A", risk_title="Risk A"):

    return {
        "schema_version": "1.0",
        "generated_at": generated_at,
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
            }
        },
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
        "risk_register": [
            {
                "source": "test",
                "severity": "HIGH",
                "title": risk_title,
                "reason": "Risk reason"
            }
        ],
        "action_queue": [
            "Review Risk A"
        ]
    }


class EchoStateHistoryTests(unittest.TestCase):

    def test_no_archive_directory_does_not_crash(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            missing_dir = Path(temp_dir) / "missing"
            history = build_echo_state_history(
                _state("2026-01-02T00:00:00"),
                missing_dir
            )

            self.assertEqual(1, history["sample_count"])
            self.assertEqual(0, history["lookback"]["available_snapshots"])

    def test_malformed_json_is_skipped(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir)
            (archive / "bad.json").write_text("{bad", encoding="utf-8")
            (archive / "good.json").write_text(
                json.dumps(_state("2026-01-01T00:00:00")),
                encoding="utf-8"
            )
            history = build_echo_state_history(
                _state("2026-01-02T00:00:00"),
                archive
            )

            self.assertEqual(2, history["sample_count"])
            self.assertEqual(1, history["lookback"]["available_snapshots"])

    def test_repeated_risk_is_persistent(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir)
            (archive / "one.json").write_text(
                json.dumps(_state("2026-01-01T00:00:00")),
                encoding="utf-8"
            )
            history = build_echo_state_history(
                _state("2026-01-02T00:00:00"),
                archive
            )

            self.assertEqual("Risk A", history["persistent_risks"][0]["title"])
            self.assertEqual(2, history["persistent_risks"][0]["count"])

    def test_changed_priority_increments_stability_count(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir)
            (archive / "one.json").write_text(
                json.dumps(_state("2026-01-01T00:00:00", priority="Risk A")),
                encoding="utf-8"
            )
            history = build_echo_state_history(
                _state("2026-01-02T00:00:00", priority="Risk B"),
                archive
            )

            self.assertEqual(
                1,
                history["state_stability"]["priority_changed_count"]
            )

    def test_history_is_json_serializable(self):

        history = build_echo_state_history(
            _state("2026-01-02T00:00:00"),
            Path("missing-history-dir")
        )

        json.dumps(history)

    def test_output_files_are_written(self):

        history = build_echo_state_history(
            _state("2026-01-02T00:00:00"),
            Path("missing-history-dir")
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_state_history.json"
            text_path = Path(temp_dir) / "echo_state_history.txt"

            json_result = write_state_history_json(history, json_path)
            text_result = write_state_history_text(history, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
