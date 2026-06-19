import re
from datetime import datetime

from security_master_search import (
    load_current_holdings,
    load_watchlist,
    search_security_master
)


INTENTS = {
    "portfolio_snapshot",
    "portfolio_change",
    "portfolio_movement",
    "holding_news",
    "security_resolution",
    "ticker_question",
    "ticker_news",
    "market_opportunities",
    "market_risks",
    "watchlist_management",
    "security_master_search",
    "paper_allocation_future",
    "general_market_question",
    "unknown"
}


_RESOLUTION_TICKER_PATTERN = r"[A-Za-z][A-Za-z0-9.]{0,5}"
_RESOLUTION_NON_TICKERS = {
    "a",
    "an",
    "for",
    "is",
    "symbol",
    "security",
    "the",
    "this",
    "ticker",
    "who",
    "what"
}


def _looks_like_resolution_symbol(value):

    token = _safe_text(value).strip(" ?!.:,;").casefold()
    return (
        bool(token)
        and token not in _RESOLUTION_NON_TICKERS
        and bool(re.fullmatch(_RESOLUTION_TICKER_PATTERN, token, re.IGNORECASE))
    )


def is_explicit_security_resolution_query(user_query):

    query = _safe_text(user_query)
    lowered = query.casefold()
    patterns = (
        rf"\b(?:resolve|identify)\s+(?:ticker|symbol|security)?\s*({_RESOLUTION_TICKER_PATTERN})\b",
        rf"\bwhat\s+is\s+({_RESOLUTION_TICKER_PATTERN})\b",
        rf"\bwho\s+is\s+({_RESOLUTION_TICKER_PATTERN})\b",
        rf"\bsecurity\s+resolution\s+for\s+({_RESOLUTION_TICKER_PATTERN})\b"
    )

    for pattern in patterns:
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if match and _looks_like_resolution_symbol(match.group(1)):
            return True

    return "what is this ticker" in lowered


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _tokens(text):

    return set(re.findall(r"[a-z0-9]+", _safe_text(text).casefold()))


def _has(text, phrases):

    lowered = _safe_text(text).casefold()
    return any(phrase in lowered for phrase in phrases)


def _extract_tickers(query):

    tickers = []
    pattern = (
        r"\b[A-Za-z][A-Za-z0-9.]{0,5}\b"
        if is_explicit_security_resolution_query(query)
        else r"\b[A-Z][A-Z0-9.]{0,5}\b"
    )
    for token in re.findall(pattern, str(query or "")):
        token = token.upper()
        if token not in {
            "I",
            "A",
            "ETF",
            "ETFS",
            "IRA",
            "USD",
            "CASH",
            "RESOLVE",
            "IDENTIFY",
            "TICKER",
            "SYMBOL",
            "SECURITY",
            "RESOLUTION",
            "FOR",
            "WHAT",
            "WHO",
            "IS",
            "THIS"
        }:
            tickers.append(token)
    return list(dict.fromkeys(tickers))


def _extract_categories(query):

    lowered = _safe_text(query).casefold()
    categories = []
    known = (
        "small cap value",
        "small value",
        "large growth",
        "semiconductor",
        "nuclear",
        "energy",
        "bitcoin",
        "cash",
        "bond",
        "treasury",
        "healthcare",
        "international",
        "intl"
    )
    for category in known:
        if category in lowered:
            categories.append(category)
    if "etf" in lowered or "fund" in lowered:
        categories.append("etf")
    return categories


def _security_names(query, tickers, categories):

    search = search_security_master(
        query,
        tickers=tickers,
        categories=categories,
        max_results=5
    )
    return [
        item.get("name")
        for item in search.get("matches") or []
        if item.get("name")
    ]


def _portfolio_relevance(tickers):

    if not tickers:
        return "unknown"

    held = {row.get("ticker") for row in load_current_holdings()}
    watch = {row.get("ticker") for row in load_watchlist()}
    holding_count = len([ticker for ticker in tickers if ticker in held])
    known_count = len([ticker for ticker in tickers if ticker in held or ticker in watch])

    if holding_count == len(tickers):
        return "holding"
    if holding_count > 0:
        return "mixed"
    if known_count or tickers:
        return "non_holding"
    return "unknown"


def _base_result(query):

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": _safe_text(query),
        "investment_intent": "unknown",
        "entities": [],
        "tickers": [],
        "security_names": [],
        "categories": [],
        "portfolio_relevance": "unknown",
        "requires_portfolio_context": False,
        "requires_portfolio_change_context": False,
        "requires_news_context": False,
        "requires_macro_context": False,
        "requires_research_context": False,
        "requires_watchlist_context": False,
        "requires_security_master_context": False,
        "requires_external_ticker_context": False,
        "answer_mode": "general",
        "confidence": "low",
        "reason": "No investment-specific pattern matched."
    }


def classify_investment_intent(user_query, portfolio_state=None,
                               memory_context=None):

    query = _safe_text(user_query)
    lowered = query.casefold()
    tokens = _tokens(query)
    tickers = _extract_tickers(query)
    categories = _extract_categories(query)
    result = _base_result(query)
    result["tickers"] = tickers
    result["categories"] = categories
    result["portfolio_relevance"] = _portfolio_relevance(tickers)

    def set_intent(intent, answer_mode, confidence, reason, **flags):
        result["investment_intent"] = intent
        result["answer_mode"] = answer_mode
        result["confidence"] = confidence
        result["reason"] = reason
        for key, value in flags.items():
            result[key] = bool(value)

    if is_explicit_security_resolution_query(query):
        set_intent(
            "security_resolution",
            "security_resolution",
            "high",
            "User explicitly asked Echo to resolve or identify a security.",
            requires_security_master_context=True,
            requires_research_context=True
        )
    elif _has(lowered, (
        "allocate on paper",
        "paper allocation",
        "autonomous allocation",
        "simulate allocating",
        "gave echo",
        "give echo",
        "$1000 allocation",
        "$1,000 allocation",
        "invest $1000",
        "invest 1000"
    )):
        set_intent(
            "paper_allocation_future",
            "future_allocation_placeholder",
            "high",
            "User asked about future paper/autonomous allocation mode.",
            requires_research_context=True,
            requires_watchlist_context=True
        )
    elif _has(lowered, (
        "what changed in my portfolio",
        "new positions",
        "removed positions",
        "what did i buy",
        "what did i sell",
        "last report",
        "last import",
        "cash changed",
        "cash change",
        "concentration change",
        "concentration changed"
    )):
        set_intent(
            "portfolio_change",
            "change_analysis",
            "high",
            "User asked about holdings-level portfolio changes.",
            requires_portfolio_context=True,
            requires_portfolio_change_context=True
        )
    elif _has(lowered, (
        "why did my portfolio move",
        "what drove",
        "gains",
        "losses",
        "contributed most",
        "price movement",
        "portfolio move",
        "portfolio moved"
    )):
        set_intent(
            "portfolio_movement",
            "movement_attribution",
            "high",
            "User asked for portfolio movement attribution.",
            requires_portfolio_context=True,
            requires_portfolio_change_context=True
        )
    elif _has(lowered, (
        "world events affect my stocks",
        "news affect my stocks",
        "affect my current stocks",
        "affect my holdings",
        "affect my portfolio",
        "news affecting my"
    )):
        set_intent(
            "holding_news",
            "ticker_analysis",
            "high",
            "User asked for news or macro impact on current holdings.",
            requires_portfolio_context=True,
            requires_news_context=True,
            requires_macro_context=True
        )
    elif tickers and _has(lowered, (
        "worth researching",
        "what do you think",
        "compare",
        "research",
        "update thesis",
        "thesis on",
        "bull case",
        "bear case",
        "what am i missing",
        "what am i missing about"
    )):
        set_intent(
            "ticker_question",
            "ticker_analysis",
            "high",
            "User asked about a specific ticker or security.",
            requires_research_context=True,
            requires_security_master_context=True,
            requires_portfolio_context=result["portfolio_relevance"] in {"holding", "mixed"}
        )
    elif _has(lowered, (
        "could go up",
        "worth researching",
        "research candidates",
        "opportunity",
        "opportunities",
        "showing up in news",
        "strengthening"
    )):
        intent = (
            "security_master_search"
            if categories and not _has(lowered, (
                "news",
                "macro",
                "go up",
                "research candidates"
            ))
            else "market_opportunities"
        )
        set_intent(
            intent,
            "opportunity_scan" if intent == "market_opportunities" else "security_search",
            "high",
            "User asked for research candidates or upside ideas.",
            requires_news_context=True,
            requires_macro_context=True,
            requires_research_context=True,
            requires_watchlist_context=True,
            requires_security_master_context=True
        )
    elif tickers and _has(lowered, (
        "could go down",
        "downside",
        "negative news",
        "weakening",
        "risks",
        "risk candidates",
        "what am i missing",
        "what am i missing about"
    )):
        set_intent(
            "ticker_question",
            "ticker_analysis",
            "high",
            "User asked for ticker-specific risks or missing evidence.",
            requires_research_context=True,
            requires_news_context=True,
            requires_macro_context=True,
            requires_security_master_context=True,
            requires_portfolio_context=result["portfolio_relevance"] in {"holding", "mixed"}
        )
    elif _has(lowered, (
        "could go down",
        "downside",
        "negative news",
        "weakening",
        "risks",
        "risk candidates",
        "what am i missing",
        "what am i missing about"
    )):
        set_intent(
            "market_risks",
            "risk_scan",
            "high",
            "User asked for downside or risk candidates.",
            requires_portfolio_context=True,
            requires_news_context=True,
            requires_macro_context=True,
            requires_research_context=True,
            requires_security_master_context=True
        )
    elif _has(lowered, (
        "watchlist",
        "promote",
        "demote",
        "add to watch",
        "remove from watch"
    )):
        set_intent(
            "watchlist_management",
            "watchlist_review",
            "high",
            "User asked about watchlist management.",
            requires_research_context=True,
            requires_watchlist_context=True,
            requires_news_context=True,
            requires_macro_context=True
        )
    elif _has(lowered, (
        "security master",
        "search for",
        "find",
        "what etfs",
        "what funds",
        "low expense",
        "expense ratios"
    )) or ("etfs" in tokens and categories):
        set_intent(
            "security_master_search",
            "security_search",
            "high",
            "User asked to search the local security master.",
            requires_security_master_context=True
        )
    elif tickers and _has(lowered, ("news", "down", "up", "why is", "current news")):
        set_intent(
            "ticker_news",
            "ticker_analysis",
            "medium",
            "User asked about ticker-specific news or movement.",
            requires_news_context=True,
            requires_research_context=True,
            requires_security_master_context=True,
            requires_portfolio_context=result["portfolio_relevance"] in {"holding", "mixed"}
        )
    elif tickers:
        set_intent(
            "ticker_question",
            "ticker_analysis",
            "high",
            "User asked about a specific ticker or security.",
            requires_research_context=True,
            requires_security_master_context=True,
            requires_portfolio_context=result["portfolio_relevance"] in {"holding", "mixed"}
        )
    elif _has(lowered, (
        "what do i own",
        "current holdings",
        "allocation",
        "concentration",
        "exposure",
        "portfolio risk",
        "holdings"
    )):
        set_intent(
            "portfolio_snapshot",
            "snapshot",
            "high",
            "User asked about current holdings, allocation, or risk.",
            requires_portfolio_context=True
        )
    elif tokens & {"market", "macro", "fed", "inflation", "rates", "economy", "sector"}:
        set_intent(
            "general_market_question",
            "general",
            "medium",
            "User asked a broad market or macro question.",
            requires_news_context=True,
            requires_macro_context=True
        )

    if result["requires_security_master_context"] or tickers or categories:
        result["security_names"] = _security_names(query, tickers, categories)
        result["entities"] = list(dict.fromkeys(tickers + categories + result["security_names"]))

    if result["investment_intent"] not in INTENTS:
        result["investment_intent"] = "unknown"

    return result
