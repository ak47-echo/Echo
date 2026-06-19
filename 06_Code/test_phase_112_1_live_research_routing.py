import unittest

import echo
import echo_api
from echo_agent_router import route_query_to_agents
from echo_context_budget import build_context_budget


class Phase1121LiveResearchRoutingTests(unittest.TestCase):

    def _selected_tools(self, query):

        budget = build_context_budget(query, {})
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
        self.assertIn("echo_get_research_snapshot", tools)
        self.assertLess(
            tools.index("echo_get_live_research"),
            tools.index("echo_get_research_snapshot")
        )

    def test_what_do_you_think_selects_security_intelligence_plus_live(self):

        tools = self._selected_tools("what do you think about SMCI")

        self.assertIn("echo_get_live_research", tools)
        self.assertIn("echo_get_thesis_refresh", tools)
        self.assertIn("echo_get_security_intelligence", tools)

    def test_compare_selects_security_comparison(self):

        tools = self._selected_tools("compare SMCI vs NVDA")

        self.assertIn("echo_compare_securities", tools)
        self.assertIn("echo_get_live_research", tools)

    def test_api_docs_include_live_research_endpoints(self):

        if echo_api.FastAPI is None:
            self.skipTest("FastAPI is not installed.")

        paths = echo_api.app.openapi()["paths"]

        self.assertIn("/research/live", paths)
        self.assertIn("/research/thesis-refresh", paths)


if __name__ == "__main__":
    unittest.main()
