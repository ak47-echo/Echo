import os
import unittest
from unittest.mock import patch

import echo
import echo_api


class FakeAnsweredProvider:

    provider_name = "anthropic"

    def model_name(self):

        return "claude-test"

    def live_calls_enabled(self):

        return True

    def is_configured(self):

        return True

    def generate_response(self, messages, tools=None, context=None):

        return {
            "status": "ANSWERED",
            "provider": self.provider_name,
            "model": self.model_name(),
            "answer": "LLM conversational answer.",
            "tool_context_used": True,
            "tool_context_char_count": 120,
            "live_call_attempted": True,
            "confidence": "HIGH",
            "notes": "Fake provider response."
        }


class FakeFailedProvider(FakeAnsweredProvider):

    def generate_response(self, messages, tools=None, context=None):

        return {
            "status": "ERROR",
            "provider": self.provider_name,
            "model": self.model_name(),
            "answer": "",
            "tool_context_used": True,
            "tool_context_char_count": 120,
            "live_call_attempted": True,
            "confidence": "LOW",
            "notes": "Provider failed with ANTHROPIC_API_KEY=TEST_SECRET_VALUE."
        }


class FakeDisabledProvider(FakeAnsweredProvider):

    def live_calls_enabled(self):

        return False

    def generate_response(self, messages, tools=None, context=None):

        return {
            "status": "STUB",
            "provider": self.provider_name,
            "model": self.model_name(),
            "answer": "",
            "tool_context_used": True,
            "tool_context_char_count": 120,
            "live_call_attempted": False,
            "confidence": "LOW",
            "notes": "Live mode disabled."
        }


def _minimal_context():

    return {"sections": {}}


def _no_write_patches():

    names = (
        "write_context_budget_json",
        "write_context_budget_text",
        "write_agent_routing_json",
        "write_agent_routing_text",
        "write_context_assembly_json",
        "write_context_assembly_text",
        "write_response_composer_json",
        "write_response_composer_text"
    )

    return [
        patch.object(echo, name, return_value={"success": True})
        for name in names
    ]


class EchoLLMProviderTests(unittest.TestCase):

    def _run_with_no_writes(self, function, *args, **kwargs):

        patches = _no_write_patches()

        for item in patches:
            item.start()

        try:
            return function(*args, **kwargs)
        finally:
            for item in reversed(patches):
                item.stop()

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

    def test_hi_returns_llm_answer_when_provider_succeeds(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeAnsweredProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "hi",
                _minimal_context()
            )

        self.assertEqual("ANSWERED", result["status"])
        self.assertEqual("LLM conversational answer.", result["answer"])
        self.assertEqual("llm", result["response_source"])
        self.assertEqual("anthropic", result["llm_provider"])
        self.assertTrue(result["live_call_attempted"])
        self.assertFalse(result["fallback_used"])
        self.assertEqual("conversational", result["query_class"])

    def test_hi_returns_clean_fallback_when_live_mode_disabled(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeDisabledProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "hi",
                _minimal_context()
            )

        self.assertEqual("DETERMINISTIC_FALLBACK", result["status"])
        self.assertEqual("deterministic", result["response_source"])
        self.assertIn("I'm here.", result["answer"])
        self.assertNotIn("deterministic answer", result["answer"].casefold())
        self.assertNotIn("compact memory context", result["answer"].casefold())

    def test_joke_does_not_return_portfolio_risk_summary(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeDisabledProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "Tell me a joke about portfolio managers.",
                _minimal_context()
            )

        self.assertEqual("deterministic", result["response_source"])
        self.assertEqual("conversational", result["query_class"])
        self.assertEqual("none", result["routing_mode"])
        self.assertNotIn("Portfolio read:", result["answer"])
        self.assertNotIn("UNH position concentration", result["answer"])

    def test_provider_failure_falls_back_and_redacts_secret_notes(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeFailedProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "hi",
                _minimal_context()
            )

        serialized = str(result)
        self.assertEqual("deterministic", result["response_source"])
        self.assertTrue(result["fallback_used"])
        self.assertNotIn("TEST_SECRET_VALUE", serialized)
        self.assertIn("[REDACTED]", result["notes"])

    def test_portfolio_only_summary_still_routes_to_portfolio(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeDisabledProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "Give me a portfolio-only summary.",
                _minimal_context()
            )

        self.assertEqual("agent_specific", result["query_class"])
        self.assertEqual("single_agent", result["routing_mode"])
        self.assertEqual(["portfolio"], result["agent_routing"]["primary_agents"])

    def test_macro_risk_question_routes_to_portfolio_and_macro(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeDisabledProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "How exposed am I to macro risk?",
                _minimal_context()
        )

        self.assertEqual("multi_agent", result["query_class"])
        self.assertEqual("multi_agent", result["routing_mode"])
        self.assertIn("portfolio", result["agent_routing"]["primary_agents"])
        self.assertIn("macro", result["agent_routing"]["primary_agents"])

    def test_chat_uses_llm_answer_when_provider_succeeds(self):

        from fastapi.testclient import TestClient
        result = {
            "status": "ANSWERED",
            "answer": "LLM conversational answer.",
            "response_source": "llm",
            "llm_provider": "anthropic",
            "live_call_attempted": True,
            "fallback_used": False
        }

        with patch.object(echo_api, "echo_generate_llm_answer", return_value=result):
            client = TestClient(echo_api.create_app())
            response = client.post("/chat", json={"message": "hi"})

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("LLM conversational answer.", payload["answer"])
        self.assertEqual("llm", payload["response_source"])

    def test_ask_uses_llm_answer_when_provider_succeeds(self):

        from fastapi.testclient import TestClient
        result = {
            "status": "ANSWERED",
            "answer": "LLM conversational answer.",
            "response_source": "llm",
            "llm_provider": "anthropic",
            "live_call_attempted": True,
            "fallback_used": False
        }

        with patch.object(echo_api, "echo_generate_llm_answer", return_value=result):
            client = TestClient(echo_api.create_app())
            response = client.post("/ask", json={"message": "hi"})

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("LLM conversational answer.", payload["answer"])
        self.assertEqual("llm", payload["response_source"])

    def test_chat_falls_back_to_composer_answer_when_provider_fails(self):

        from fastapi.testclient import TestClient
        result = {
            "status": "DETERMINISTIC_FALLBACK",
            "answer": "I'm here. Ask me what changed.",
            "response_source": "deterministic",
            "llm_provider": "anthropic",
            "live_call_attempted": True,
            "fallback_used": True,
            "notes": "Provider failed without exposing secrets."
        }

        with patch.object(echo_api, "echo_generate_llm_answer", return_value=result):
            client = TestClient(echo_api.create_app())
            response = client.post("/chat", json={"message": "hi"})

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("deterministic", payload["response_source"])
        self.assertTrue(payload["fallback_used"])
        self.assertIn("I'm here.", payload["answer"])
        self.assertNotIn("TEST_SECRET_VALUE", str(payload))


if __name__ == "__main__":
    unittest.main()
