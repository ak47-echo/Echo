import unittest

from echo_investment_intent import classify_investment_intent


class EchoInvestmentIntentTests(unittest.TestCase):

    def _intent(self, query):

        return classify_investment_intent(query)["investment_intent"]

    def test_portfolio_change_queries(self):

        self.assertEqual(
            "portfolio_change",
            self._intent("what changed in my portfolio")
        )
        self.assertEqual(
            "portfolio_change",
            self._intent("what are my new positions from last report")
        )

    def test_portfolio_movement_query(self):

        self.assertEqual(
            "portfolio_movement",
            self._intent("why did my portfolio move")
        )

    def test_holding_news_query(self):

        self.assertEqual(
            "holding_news",
            self._intent("what world events affect my stocks")
        )

    def test_market_opportunity_and_risk_queries(self):

        self.assertEqual(
            "market_opportunities",
            self._intent("what stocks could go up from this news")
        )
        self.assertEqual(
            "market_risks",
            self._intent("what stocks could go down")
        )
        self.assertEqual(
            "market_risks",
            self._intent("what am I missing about my current holdings")
        )

    def test_ticker_queries(self):

        self.assertEqual(
            "ticker_question",
            self._intent("what do you think about NVDA")
        )
        self.assertEqual(
            "ticker_news",
            self._intent("why is UNH down")
        )
        for query in (
            "research SMCI",
            "research NVDA",
            "update thesis on UNH",
            "bull case for SMCI",
            "bear case for SMCI",
            "compare SMCI vs NVDA",
            "what am I missing about UNH"
        ):
            self.assertEqual("ticker_question", self._intent(query))

    def test_explicit_security_resolution_queries(self):

        for query in (
            "resolve SPCX",
            "resolve spcx",
            "identify SPCX",
            "what is SPCX",
            "who is SPCX",
            "security resolution for SPCX",
            "what is this ticker"
        ):
            self.assertEqual("security_resolution", self._intent(query))

    def test_security_search_queries(self):

        self.assertEqual(
            "security_master_search",
            self._intent("find nuclear stocks worth researching")
        )
        self.assertEqual(
            "security_master_search",
            self._intent("small cap value ETFs")
        )

    def test_paper_allocation_future(self):

        self.assertEqual(
            "paper_allocation_future",
            self._intent("if I gave Echo $1000 allocation on paper")
        )


if __name__ == "__main__":
    unittest.main()
