from datetime import datetime, timedelta
import unittest

from query_execution_tier import (
    classify_execution_tier,
    fresh_cached_research
)


def _store(tickers, generated_at=None):

    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    return {
        "generated_at": generated_at,
        "profiles": [
            {"ticker": ticker, "generated_at": generated_at}
            for ticker in tickers
        ]
    }


class QueryExecutionTierTests(unittest.TestCase):

    def test_hi_is_fast_local(self):

        tier = classify_execution_tier("hi")

        self.assertEqual("FAST_LOCAL", tier["execution_tier"])
        self.assertFalse(tier["live_research_allowed"])
        self.assertFalse(tier["web_search_allowed"])
        self.assertEqual(3, tier["max_expected_seconds"])

    def test_top_priority_is_fast_local(self):

        tier = classify_execution_tier("what is my top priority")

        self.assertEqual("FAST_LOCAL", tier["execution_tier"])

    def test_resolve_spcx_is_fast_local(self):

        tier = classify_execution_tier("resolve SPCX")

        self.assertEqual("FAST_LOCAL", tier["execution_tier"])
        self.assertFalse(tier["live_research_allowed"])

    def test_research_nvda_is_deep_research(self):

        tier = classify_execution_tier("research NVDA")

        self.assertEqual("DEEP_RESEARCH", tier["execution_tier"])
        self.assertTrue(tier["live_research_allowed"])
        self.assertTrue(tier["web_search_allowed"])

    def test_compare_uses_standard_when_cache_is_fresh(self):

        tier = classify_execution_tier(
            "compare SMCI vs NVDA",
            research_evidence_store=_store(["SMCI", "NVDA"])
        )

        self.assertEqual("STANDARD_CONTEXT", tier["execution_tier"])
        self.assertFalse(tier["live_research_allowed"])
        self.assertTrue(tier["cached_research_available"])

    def test_compare_uses_deep_when_cache_is_stale(self):

        stale = (datetime.now() - timedelta(hours=48)).isoformat(timespec="seconds")
        tier = classify_execution_tier(
            "compare SMCI vs NVDA",
            research_evidence_store=_store(["SMCI", "NVDA"], stale)
        )

        self.assertEqual("DEEP_RESEARCH", tier["execution_tier"])
        self.assertTrue(tier["live_research_allowed"])

    def test_fresh_cached_research_honors_ttl(self):

        self.assertTrue(fresh_cached_research(["SMCI"], _store(["SMCI"]), 24))
        stale = (datetime.now() - timedelta(hours=25)).isoformat(timespec="seconds")
        self.assertFalse(
            fresh_cached_research(["SMCI"], _store(["SMCI"], stale), 24)
        )


if __name__ == "__main__":
    unittest.main()
