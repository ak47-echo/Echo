import json
import tempfile
import unittest
from pathlib import Path

from echo_intent_reasoning import (
    classify_reasoning_intent,
    write_intent_reasoning_json,
    write_intent_reasoning_text
)


class EchoIntentReasoningTests(unittest.TestCase):

    def test_top_priority_is_retrieval(self):

        result = classify_reasoning_intent("What is my current top priority?")

        self.assertEqual("retrieval", result["reasoning_intent"])

    def test_why_unh_is_explanation(self):

        result = classify_reasoning_intent("Why is UNH my top priority?")

        self.assertEqual("explanation", result["reasoning_intent"])
        self.assertIn("UNH", result["detected_entities"])

    def test_unh_drop_is_scenario_analysis(self):

        result = classify_reasoning_intent(
            "If UNH fell 40% tomorrow, how would that affect me?"
        )

        self.assertEqual("scenario_analysis", result["reasoning_intent"])
        self.assertEqual("tomorrow", result["detected_horizon"])

    def test_challenge_portfolio_is_critique(self):

        result = classify_reasoning_intent("Challenge my current portfolio.")

        self.assertEqual("critique", result["reasoning_intent"])

    def test_focus_this_week_is_prioritization(self):

        result = classify_reasoning_intent(
            "What should I focus on this week?"
        )

        self.assertEqual("prioritization", result["reasoning_intent"])
        self.assertEqual("this week", result["detected_horizon"])

    def test_next_step_is_recommendation(self):

        result = classify_reasoning_intent("What should I do next?")

        self.assertEqual("recommendation", result["reasoning_intent"])

    def test_joke_is_conversation(self):

        result = classify_reasoning_intent(
            "Tell me a joke about portfolio managers."
        )

        self.assertEqual("conversation", result["reasoning_intent"])

    def test_next_12_months_horizon_detected(self):

        result = classify_reasoning_intent(
            "What are the consequences over the next 12 months?"
        )

        self.assertEqual("next 12 months", result["detected_horizon"])

    def test_json_serializable(self):

        result = classify_reasoning_intent("Why is UNH important?")

        json.dumps(result)

    def test_output_files_written(self):

        result = classify_reasoning_intent("Why is UNH important?")

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "intent.json"
            text_path = Path(temp_dir) / "intent.txt"

            json_result = write_intent_reasoning_json(result, json_path)
            text_result = write_intent_reasoning_text(result, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
