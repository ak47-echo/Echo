import json
import tempfile
import unittest
from pathlib import Path

from echo_agent_router import (
    route_query_to_agents,
    write_agent_routing_json,
    write_agent_routing_text
)


def _budget(level="standard", query_class="agent_specific"):

    return {
        "schema_version": "1.0",
        "query_class": query_class,
        "budget_level": level,
        "max_context_items": 20
    }


class EchoAgentRouterTests(unittest.TestCase):

    def test_portfolio_query_routes_to_portfolio(self):

        routing = route_query_to_agents(
            "review portfolio allocation risk",
            _budget("expanded")
        )

        self.assertIn("portfolio", routing["primary_agents"])

    def test_joke_about_portfolio_managers_does_not_route_to_portfolio(self):

        routing = route_query_to_agents(
            "Tell me a joke about portfolio managers.",
            _budget("minimal", "conversational")
        )

        self.assertEqual([], routing["primary_agents"])
        self.assertEqual("none", routing["routing_mode"])

    def test_macro_risk_query_routes_to_portfolio_and_macro(self):

        routing = route_query_to_agents(
            "How exposed am I to macro risk?",
            _budget("expanded", "multi_agent")
        )

        self.assertIn("portfolio", routing["primary_agents"])
        self.assertIn("macro", routing["primary_agents"])

    def test_macro_query_routes_to_macro(self):

        routing = route_query_to_agents(
            "what is the macro inflation regime?",
            _budget()
        )

        self.assertIn("macro", routing["primary_agents"])

    def test_news_query_routes_to_news(self):

        routing = route_query_to_agents(
            "what news headline matters?",
            _budget()
        )

        self.assertIn("news", routing["primary_agents"])

    def test_research_query_routes_to_research(self):

        routing = route_query_to_agents(
            "review thesis conviction and watchlist",
            _budget()
        )

        self.assertIn("research", routing["primary_agents"])

    def test_memory_meta_query_routes_to_no_primary_agent(self):

        routing = route_query_to_agents(
            "what changed and what is persistent?",
            _budget("standard", "memory")
        )

        self.assertEqual([], routing["primary_agents"])
        self.assertEqual("none", routing["routing_mode"])

    def test_portfolio_change_query_routes_to_portfolio_change_context(self):

        routing = route_query_to_agents(
            "what are my new positions from last report",
            _budget("standard", "portfolio_change")
        )

        self.assertEqual(["portfolio"], routing["primary_agents"])
        self.assertEqual("single_agent", routing["routing_mode"])
        self.assertIn(
            "portfolio_change_detection",
            routing["agent_context_plan"][0]["context_sources"]
        )

    def test_holding_news_routes_portfolio_news_macro(self):

        routing = route_query_to_agents(
            "what world events affect my current stocks",
            _budget("expanded", "holding_news")
        )

        self.assertEqual("investment_query", routing["routing_mode"])
        self.assertIn("portfolio", routing["primary_agents"])
        self.assertIn("news", routing["secondary_agents"])
        self.assertIn("macro", routing["secondary_agents"])
        sources = [
            source
            for item in routing["agent_context_plan"]
            for source in item["context_sources"]
        ]
        self.assertIn("market_coverage", sources)
        self.assertIn("dynamic_news_coverage", sources)

    def test_nonheld_ticker_does_not_require_portfolio_primary(self):

        routing = route_query_to_agents(
            "what do you think about NVDA",
            _budget("standard", "ticker_question")
        )

        self.assertEqual(["research"], routing["primary_agents"])
        self.assertNotIn("portfolio", routing["primary_agents"])

    def test_market_opportunity_scan_routes_news_macro_research(self):

        routing = route_query_to_agents(
            "what stocks could go up from this news",
            _budget("expanded", "market_opportunities")
        )

        sources = [
            source
            for item in routing["agent_context_plan"]
            for source in item["context_sources"]
        ]
        self.assertIn("market_opportunity_scan", sources)
        self.assertIn("market_coverage", sources)
        self.assertIn("dynamic_news_coverage", sources)
        self.assertIn("security_master_search", sources)
        self.assertIn("news", routing["secondary_agents"])
        self.assertIn("macro", routing["secondary_agents"])

    def test_security_master_search_routes_to_security_master(self):

        routing = route_query_to_agents(
            "small cap value ETFs",
            _budget("standard", "security_master_search")
        )

        self.assertIn(
            "security_master_search",
            routing["agent_context_plan"][0]["context_sources"]
        )
        self.assertIn(
            "market_coverage",
            routing["agent_context_plan"][0]["context_sources"]
        )

    def test_broad_synthesis_routes_to_all_active_agents(self):

        routing = route_query_to_agents(
            "give me a cross-agent executive summary",
            _budget("expanded", "multi_agent")
        )

        self.assertEqual("all_agents", routing["routing_mode"])
        self.assertEqual(
            {"portfolio", "research", "news", "macro"},
            set(routing["primary_agents"])
        )

    def test_minimal_budget_excludes_full_reports(self):

        routing = route_query_to_agents(
            "portfolio allocation",
            _budget("minimal")
        )

        self.assertFalse(
            routing["agent_context_plan"][0]["include_full_report"]
        )

    def test_full_budget_allows_relevant_full_reports(self):

        routing = route_query_to_agents(
            "portfolio allocation",
            _budget("full", "deep_dive")
        )

        self.assertTrue(
            routing["agent_context_plan"][0]["include_full_report"]
        )

    def test_json_serializable(self):

        routing = route_query_to_agents("macro rates", _budget())

        json.dumps(routing)

    def test_output_files_written(self):

        routing = route_query_to_agents("macro rates", _budget())

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "echo_agent_routing.json"
            text_path = Path(temp_dir) / "echo_agent_routing.txt"

            json_result = write_agent_routing_json(routing, json_path)
            text_result = write_agent_routing_text(routing, text_path)

            self.assertTrue(json_result["success"])
            self.assertTrue(text_result["success"])
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())


if __name__ == "__main__":
    unittest.main()
