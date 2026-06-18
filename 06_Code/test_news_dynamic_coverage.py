import unittest

from agents import news_agent


class NewsDynamicCoverageTests(unittest.TestCase):

    def _article(self, title, summary=""):

        return {
            "source": "Test",
            "title": title,
            "summary": summary,
            "link": "",
            "published": None,
            "official_source": False
        }

    def _coverage(self):

        return {
            "schema_version": "1.0",
            "holdings_terms": ["ACME"],
            "watchlist_terms": ["NUKE"],
            "query_terms": ["NVDA", "Nvidia Corp"],
            "security_master_terms": ["Semiconductor", "Nvidia Corp"],
            "sector_category_terms": ["Semiconductor"],
            "coverage_universe": [
                {
                    "ticker": "ACME",
                    "name": "Acme Test Holdings",
                    "category": "US Large Growth",
                    "expense_ratio": None,
                    "source": "holding",
                    "aliases": ["ACME"],
                    "is_current_holding": True,
                    "is_watchlist": False,
                    "portfolio_weight": 10.0
                }
            ],
            "warnings": []
        }

    def test_news_agent_uses_dynamic_holding_terms(self):

        scored = news_agent._score_article(
            self._article("ACME earnings guidance beats estimates"),
            market_coverage=self._coverage()
        )
        self.assertIn("ACME", scored["portfolio_matches"])
        self.assertGreater(scored["portfolio_score"], 0)
        self.assertIn("PORTFOLIO", scored["category_tags"])

    def test_news_agent_no_longer_requires_static_portfolio_terms(self):

        self.assertNotIn("ACME", news_agent.PORTFOLIO_TERMS)
        scored = news_agent._score_article(
            self._article("ACME announces major acquisition"),
            market_coverage=self._coverage()
        )
        self.assertIn("ACME", scored["portfolio_matches"])

    def test_security_master_query_terms_match_non_held_ticker_news(self):

        scored = news_agent._score_article(
            self._article("Nvidia Corp expands semiconductor capacity"),
            market_coverage=self._coverage()
        )
        self.assertIn("Nvidia Corp", scored["security_master_matches"])
        self.assertIn("SECURITY_MASTER", scored["category_tags"])

    def test_category_theme_news_response_works(self):

        scored = news_agent._score_article(
            self._article(
                "Semiconductor stocks rally after AI chip demand update"
            ),
            market_coverage=self._coverage()
        )
        self.assertIn("Semiconductor", scored["security_master_matches"])
        self.assertIn("AI_SEMICONDUCTOR", scored["category_tags"])

    def test_collect_news_includes_dynamic_coverage_summary(self):

        source = {"name": "Unit", "url": "unused", "official": False}

        def fetcher(_source):
            return {
                "source": "Unit",
                "status": "OK",
                "articles": [
                    self._article("ACME earnings guidance beats estimates")
                ],
                "error": ""
            }

        result = news_agent.collect_news(
            sources=[source],
            fetcher=fetcher,
            market_coverage=self._coverage()
        )
        self.assertEqual(1, result["dynamic_coverage"]["coverage_universe_count"])
        self.assertIn("ACME", result["articles"][0]["portfolio_matches"])


if __name__ == "__main__":
    unittest.main()
