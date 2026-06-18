import os
import unittest
from contextlib import ExitStack
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


class IntentAwareProvider(FakeAnsweredProvider):

    def generate_response(self, messages, tools=None, context=None):

        tool_context = echo.format_tool_context_for_llm(tools)

        return {
            "status": "ANSWERED",
            "provider": self.provider_name,
            "model": self.model_name(),
            "answer": (
                "Reasoned LLM answer using "
                f"{tools['intent_reasoning']['reasoning_intent']}."
            ),
            "tool_context_used": True,
            "tool_context_char_count": len(tool_context),
            "live_call_attempted": True,
            "confidence": "HIGH",
            "notes": tool_context
        }


class ScenarioAwareProvider(FakeAnsweredProvider):

    def generate_response(self, messages, tools=None, context=None):

        intent = (tools or {}).get("intent_reasoning", {})
        reasoning_intent = intent.get("reasoning_intent")

        return {
            "status": "ANSWERED",
            "provider": self.provider_name,
            "model": self.model_name(),
            "answer": f"Scenario LLM answer using {reasoning_intent}.",
            "tool_context_used": True,
            "tool_context_char_count": len(
                echo.format_tool_context_for_llm(tools)
            ),
            "live_call_attempted": True,
            "confidence": "HIGH",
            "notes": "Scenario provider received reasoning payload."
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


class CapturingProvider(FakeAnsweredProvider):

    def __init__(self, answer="Captured LLM answer."):

        self.answer = answer
        self.messages = None
        self.tools = None
        self.context = None

    def generate_response(self, messages, tools=None, context=None):

        self.messages = messages
        self.tools = tools
        self.context = context
        return {
            "status": "ANSWERED",
            "provider": self.provider_name,
            "model": self.model_name(),
            "answer": self.answer,
            "tool_context_used": True,
            "tool_context_char_count": len(echo.format_tool_context_for_llm(tools)),
            "live_call_attempted": True,
            "confidence": "HIGH",
            "notes": "Captured provider response."
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
        "write_response_composer_text",
        "write_intent_reasoning_json",
        "write_intent_reasoning_text"
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

    def _api_post_with_provider(self, path, provider, message):

        from fastapi.testclient import TestClient

        with ExitStack() as stack:
            for item in _no_write_patches():
                stack.enter_context(item)

            stack.enter_context(
                patch.object(echo, "get_llm_provider", return_value=provider)
            )
            client = TestClient(echo_api.create_app())
            return client.post(path, json={"message": message})

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

    def test_default_provider_is_anthropic(self):

        with patch.dict(os.environ, {}, clear=True):
            provider = echo.get_llm_provider()

        self.assertIsInstance(provider, echo.AnthropicProvider)

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

        self.assertIn("Echo investment intent", prompt)
        self.assertIn("response_composer", prompt)
        self.assertIn("Review UNH risk.", prompt)
        self.assertIn("Do not introduce facts", prompt)
        self.assertIn("grounding draft", prompt)
        self.assertIn("if it is incomplete", prompt)
        self.assertIn("Do not claim live facts", prompt)

    def test_llm_context_includes_reasoning_intent(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=IntentAwareProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "Why is UNH my top priority?",
                _minimal_context()
            )

        self.assertEqual("llm", result["response_source"])
        self.assertTrue(result["llm_reviewed"])
        self.assertEqual("explanation", result["reasoning_intent"])
        self.assertIn('"reasoning_intent": "explanation"', result["notes"])
        self.assertIn("response_composer", result["notes"])

    def test_explanation_query_does_not_return_plain_template_on_llm_success(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=IntentAwareProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "Why is UNH my top priority?",
                _minimal_context()
            )

        self.assertEqual("ANSWERED", result["status"])
        self.assertEqual("explanation", result["reasoning_intent"])
        self.assertEqual("Reasoned LLM answer using explanation.", result["answer"])
        self.assertNotEqual(
            result["response_composer"]["answer"],
            result["answer"]
        )

    def test_scenario_query_does_not_return_plain_template_on_llm_success(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=IntentAwareProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "If UNH fell 40% tomorrow, how would that affect me?",
                _minimal_context()
            )

        self.assertEqual("ANSWERED", result["status"])
        self.assertEqual("scenario_analysis", result["reasoning_intent"])
        self.assertEqual(
            "Reasoned LLM answer using scenario_analysis.",
            result["answer"]
        )

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
        self.assertTrue(result["llm_reviewed"])
        self.assertEqual("ANSWERED", result["provider_status"])
        self.assertIsInstance(result["context_sources_used"], list)
        self.assertIsInstance(result["missing_data_notes"], list)
        self.assertEqual("conversational", result["query_class"])
        self.assertEqual("conversation", result["reasoning_intent"])

    def test_investment_query_uses_llm_when_provider_succeeds(self):

        provider = CapturingProvider("Claude investment answer.")
        with patch.object(echo, "get_llm_provider", return_value=provider):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "what do you think about NVDA",
                _minimal_context()
            )

        self.assertEqual("ANSWERED", result["status"])
        self.assertEqual("llm", result["response_source"])
        self.assertEqual("Claude investment answer.", result["answer"])
        self.assertFalse(result["fallback_used"])
        self.assertTrue(result["llm_reviewed"])
        self.assertEqual("ticker_question", result["query_class"])
        self.assertIn("investment_intent", provider.tools["context_budget"])
        self.assertIn("response_composer", provider.tools)
        self.assertIn("llm_policy", provider.tools)

    def test_portfolio_change_query_uses_llm_when_provider_succeeds(self):

        provider = CapturingProvider("Claude portfolio change answer.")
        with patch.object(echo, "get_llm_provider", return_value=provider):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "what changed in my portfolio",
                _minimal_context()
            )

        self.assertEqual("portfolio_change", result["query_class"])
        self.assertEqual("llm", result["response_source"])
        self.assertEqual("Claude portfolio change answer.", result["answer"])
        self.assertIn(
            "portfolio_change_detection",
            result["context_assembly"].get("included_sources", [])
        )

    def test_llm_policy_payload_marks_draft_as_reference_only(self):

        provider = CapturingProvider()
        with patch.object(echo, "get_llm_provider", return_value=provider):
            self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "why did my portfolio move",
                _minimal_context()
            )

        policy = provider.tools["llm_policy"]
        self.assertEqual(
            "llm_first_when_live_provider_succeeds",
            policy["final_answer_policy"]
        )
        self.assertIn(
            "not_final_answer",
            policy["deterministic_composer_role"]
        )
        self.assertIn(
            "correct it",
            policy["draft_review_instruction"]
        )

    def test_llm_prompt_includes_correction_instruction(self):

        prompt = echo._build_anthropic_prompt_message(
            [{"role": "user", "content": "what changed?"}],
            '{"response_composer":{"answer":"No material changes."}}'
        )

        self.assertIn("Review whether the deterministic draft", prompt)
        self.assertIn("correct it using available Echo context", prompt)
        self.assertIn("Do not claim live facts", prompt)

    def test_successful_provider_answer_not_replaced_by_validation_warning(self):

        provider = CapturingProvider("You should buy XYZ.")
        with patch.object(echo, "get_llm_provider", return_value=provider):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "what do you think about NVDA",
                _minimal_context()
            )

        self.assertEqual("ANSWERED", result["status"])
        self.assertEqual("llm", result["response_source"])
        self.assertEqual("You should buy XYZ.", result["answer"])
        self.assertFalse(result["fallback_used"])
        self.assertTrue(result["validation"]["fallback_required"])
        self.assertTrue(result["missing_data_notes"])

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
        self.assertFalse(result["llm_reviewed"])
        self.assertIn("I'm here.", result["answer"])
        self.assertNotIn("deterministic answer", result["answer"].casefold())
        self.assertNotIn("compact memory context", result["answer"].casefold())

    def test_reasoning_fallback_is_safe_for_scenario(self):

        with patch.object(
            echo,
            "get_llm_provider",
            return_value=FakeDisabledProvider()
        ):
            result = self._run_with_no_writes(
                echo.echo_generate_llm_answer,
                "If UNH fell 40% tomorrow, how would that affect me?",
                _minimal_context()
            )

        self.assertEqual("scenario_analysis", result["reasoning_intent"])
        self.assertEqual("deterministic", result["response_source"])
        self.assertIn("requires reasoning beyond deterministic fallback",
                      result["answer"])

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
        self.assertFalse(result["llm_reviewed"])
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
            "fallback_used": False,
            "reasoning_intent": "conversation",
            "reasoning_depth": "light",
            "answer_style": "conversational"
        }

        with patch.object(echo_api, "echo_generate_llm_answer", return_value=result):
            client = TestClient(echo_api.create_app())
            response = client.post("/chat", json={"message": "hi"})

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("LLM conversational answer.", payload["answer"])
        self.assertEqual("llm", payload["response_source"])
        self.assertEqual("conversation", payload.get("reasoning_intent"))

    def test_ask_uses_llm_answer_when_provider_succeeds(self):

        from fastapi.testclient import TestClient
        result = {
            "status": "ANSWERED",
            "answer": "LLM conversational answer.",
            "response_source": "llm",
            "llm_provider": "anthropic",
            "live_call_attempted": True,
            "fallback_used": False,
            "reasoning_intent": "conversation",
            "reasoning_depth": "light",
            "answer_style": "conversational"
        }

        with patch.object(echo_api, "echo_generate_llm_answer", return_value=result):
            client = TestClient(echo_api.create_app())
            response = client.post("/ask", json={"message": "hi"})

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("LLM conversational answer.", payload["answer"])
        self.assertEqual("llm", payload["response_source"])

    def test_chat_uses_provider_success_for_scenario_analysis(self):

        response = self._api_post_with_provider(
            "/chat",
            ScenarioAwareProvider(),
            "If UNH fell 40% tomorrow, how would that affect me?"
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("ANSWERED", payload["status"])
        self.assertEqual("llm", payload["response_source"])
        self.assertEqual("ANSWERED", payload["provider_status"])
        self.assertTrue(payload["live_call_attempted"])
        self.assertFalse(payload["fallback_used"])
        self.assertEqual("scenario_analysis", payload["reasoning_intent"])
        self.assertEqual(
            "Scenario LLM answer using scenario_analysis.",
            payload["answer"]
        )
        self.assertNotIn(
            "This requires reasoning beyond deterministic fallback",
            payload["answer"]
        )

    def test_ask_uses_provider_success_for_scenario_analysis(self):

        response = self._api_post_with_provider(
            "/ask",
            ScenarioAwareProvider(),
            "If UNH fell 40% tomorrow, how would that affect me?"
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("ANSWERED", payload["status"])
        self.assertEqual("llm", payload["response_source"])
        self.assertEqual("ANSWERED", payload["provider_status"])
        self.assertFalse(payload["fallback_used"])
        self.assertEqual("scenario_analysis", payload["reasoning_intent"])
        self.assertEqual(
            "Scenario LLM answer using scenario_analysis.",
            payload["answer"]
        )

    def test_chat_scenario_falls_back_when_provider_fails(self):

        response = self._api_post_with_provider(
            "/chat",
            FakeFailedProvider(),
            "If UNH fell 40% tomorrow, how would that affect me?"
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("DETERMINISTIC_FALLBACK", payload["status"])
        self.assertEqual("deterministic", payload["response_source"])
        self.assertEqual("ERROR", payload["provider_status"])
        self.assertTrue(payload["live_call_attempted"])
        self.assertTrue(payload["fallback_used"])
        self.assertEqual("scenario_analysis", payload["reasoning_intent"])
        self.assertIn(
            "requires reasoning beyond deterministic fallback",
            payload["answer"]
        )
        self.assertNotIn("TEST_SECRET_VALUE", str(payload))

    def test_chat_falls_back_to_composer_answer_when_provider_fails(self):

        from fastapi.testclient import TestClient
        result = {
            "status": "DETERMINISTIC_FALLBACK",
            "answer": "I'm here. Ask me what changed.",
            "response_source": "deterministic",
            "llm_provider": "anthropic",
            "live_call_attempted": True,
            "fallback_used": True,
            "reasoning_intent": "conversation",
            "reasoning_depth": "light",
            "answer_style": "conversational",
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

    def test_intent_reasoning_endpoint_returns_latest_artifact(self):

        from fastapi.testclient import TestClient

        artifact = {
            "reasoning_intent": "retrieval",
            "reasoning_depth": "light",
            "answer_style": "brief"
        }

        with patch.object(
            echo_api,
            "read_intent_reasoning",
            return_value=artifact
        ):
            client = TestClient(echo_api.create_app())
            response = client.get("/intent-reasoning")

        self.assertEqual(200, response.status_code)
        self.assertEqual("retrieval", response.json()["reasoning_intent"])


if __name__ == "__main__":
    unittest.main()
