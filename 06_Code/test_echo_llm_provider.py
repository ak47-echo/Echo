import os
import unittest
from unittest.mock import patch

import echo


class EchoLLMProviderTests(unittest.TestCase):

    def test_anthropic_missing_api_key_does_not_crash(self):

        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "anthropic",
                "LLM_LIVE_MODE": "true"
            },
            clear=True
        ):
            provider = echo.get_llm_provider()
            result = provider.generate_response(
                [{"role": "user", "content": "What matters today?"}],
                tools={
                    "response_composer": {
                        "answer": "Deterministic answer."
                    }
                }
            )

        self.assertEqual("anthropic", provider.provider_name)
        self.assertEqual("NOT_CONFIGURED", result["status"])
        self.assertFalse(result["live_call_attempted"])
        self.assertEqual("", result["answer"])
        self.assertNotIn("sk-", result["notes"])

    def test_llm_provider_env_name_selects_anthropic(self):

        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "anthropic"},
            clear=True
        ):
            provider = echo.get_llm_provider()
            status = echo.get_llm_provider_status()

        self.assertIsInstance(provider, echo.AnthropicProvider)
        self.assertEqual("anthropic", status["active_provider"])
        self.assertFalse(status["configured"])

    def test_anthropic_missing_key_falls_back_to_composer_answer(self):

        orchestrator_result = {
            "status": "ANSWERED",
            "message": "What matters today?",
            "selected_tools": [],
            "context_budget": {},
            "agent_routing": {},
            "context_assembly": {},
            "response_composer": {
                "answer": "Composer fallback answer."
            },
            "tool_results": {},
            "answer": "Composer fallback answer.",
            "confidence": "MEDIUM"
        }

        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "anthropic",
                "LLM_LIVE_MODE": "true"
            },
            clear=True
        ), patch.object(
            echo,
            "echo_orchestrate_user_message",
            return_value=orchestrator_result
        ):
            result = echo.echo_generate_llm_answer(
                "What matters today?",
                {"sections": {}}
            )

        self.assertEqual("DETERMINISTIC_FALLBACK", result["status"])
        self.assertEqual("anthropic", result["provider"])
        self.assertEqual("Composer fallback answer.", result["answer"])
        self.assertTrue(result["fallback_used"])
        self.assertFalse(result["live_call_attempted"])

    def test_anthropic_prompt_uses_echo_context_and_composer(self):

        prompt = echo._build_anthropic_prompt_message(
            [{"role": "user", "content": "Summarize risk."}],
            (
                '{"context_assembly":{"included_blocks":["portfolio"]},'
                '"response_composer":{"answer":"Review UNH risk."}}'
            )
        )

        self.assertIn("Echo assembled context", prompt)
        self.assertIn("response_composer", prompt)
        self.assertIn("Review UNH risk.", prompt)
        self.assertIn("Do not introduce facts", prompt)


if __name__ == "__main__":
    unittest.main()
