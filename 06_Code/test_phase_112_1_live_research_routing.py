import unittest
from datetime import datetime

import echo
import echo_api
from echo_agent_router import route_query_to_agents
from echo_context_budget import build_context_budget


def _cached_store():

    generated_at = datetime.now().isoformat(timespec="seconds")
    return {
        "generated_at": generated_at,
        "profiles": [
            {"ticker": "SMCI", "generated_at": generated_at},
            {"ticker": "NVDA", "generated_at": generated_at}
        ]
    }


class Phase1121LiveResearchRoutingTests(unittest.TestCase):

    def _selected_tools(self, query, research_evidence_store=None):

        budget = build_context_budget(
            query,
            {},
            research_evidence_store=research_evidence_store
        )
        routing = route_query_to_agents(query, budget)
        return echo._echo_orchestrator_select_tools(
            query,
            {},
            budget,
            routing
        )

    def test_research_smci_selects_live_research_tools(self):

        tools = self._selected_tools("research SMCI")

        self.assertIn("echo_get_live_research", tools)
        self.assertIn("echo_get_thesis_refresh", tools)
        self.assertIn("echo_get_security_intelligence", tools)
        self.assertIn("echo_resolve_security", tools)
        self.assertIn("echo_get_research_snapshot", tools)
        self.assertLess(
            tools.index("echo_resolve_security"),
            tools.index("echo_get_live_research")
        )
        self.assertLess(
            tools.index("echo_get_live_research"),
            tools.index("echo_get_research_snapshot")
        )

    def test_what_do_you_think_selects_security_intelligence_plus_live(self):

        tools = self._selected_tools("what do you think about SMCI")

        self.assertNotIn("echo_get_live_research", tools)
        self.assertNotIn("echo_get_thesis_refresh", tools)
        self.assertIn("echo_get_security_intelligence", tools)
        self.assertIn("echo_resolve_security", tools)

    def test_compare_selects_security_comparison(self):

        tools = self._selected_tools("compare SMCI vs NVDA")

        self.assertIn("echo_compare_securities", tools)
        self.assertIn("echo_get_live_research", tools)
        self.assertIn("echo_resolve_security", tools)

    def test_compare_with_fresh_cache_skips_live_research(self):

        tools = self._selected_tools(
            "compare SMCI vs NVDA",
            _cached_store()
        )

        self.assertIn("echo_compare_securities", tools)
        self.assertIn("echo_resolve_security", tools)
        self.assertNotIn("echo_get_live_research", tools)
        self.assertNotIn("echo_get_thesis_refresh", tools)

    def test_explicit_resolve_queries_select_security_resolver(self):

        for query in (
            "resolve SPCX",
            "resolve spcx",
            "identify SPCX",
            "what is SPCX"
        ):
            tools = self._selected_tools(query)

            self.assertIn("echo_resolve_security", tools)
            self.assertNotIn("echo_get_live_research", tools)
            self.assertNotIn("echo_get_thesis_refresh", tools)
            self.assertLess(
                tools.index("echo_resolve_security"),
                tools.index("echo_search_security_master")
            )
            self.assertNotIn("echo_get_top_priority", tools)
            self.assertNotIn("echo_get_themes", tools)

    def test_api_docs_include_live_research_endpoints(self):

        if echo_api.FastAPI is None:
            self.skipTest("FastAPI is not installed.")

        paths = echo_api.app.openapi()["paths"]

        self.assertIn("/research/live", paths)
        self.assertIn("/research/thesis-refresh", paths)
        self.assertIn("/security/resolve", paths)

    def test_claude_prompt_contains_resolver_gate_instruction(self):

        prompt = echo.build_echo_llm_system_prompt()

        self.assertIn("security_resolution.resolved is false", prompt)
        self.assertIn("Do not use the top candidate as truth", prompt)
        self.assertIn("explicit resolve", prompt)


if __name__ == "__main__":
    unittest.main()
