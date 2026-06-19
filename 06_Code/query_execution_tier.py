from datetime import datetime, timedelta
import os
import re

from echo_investment_intent import (
    classify_investment_intent,
    is_explicit_security_resolution_query
)


EXECUTION_TIERS = {"FAST_LOCAL", "STANDARD_CONTEXT", "DEEP_RESEARCH"}
DEFAULT_TTL_HOURS = 24


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _tokens(text):

    return set(re.findall(r"[a-z0-9]+", _safe_text(text).casefold()))


def _has_any(text, terms):

    lowered = _safe_text(text).casefold()
    return any(term in lowered for term in terms)


def _ttl_hours(value=None):

    raw = value if value is not None else os.getenv(
        "LIVE_RESEARCH_CACHE_TTL_HOURS",
        str(DEFAULT_TTL_HOURS)
    )
    try:
        return max(float(raw), 0.0)
    except (TypeError, ValueError):
        return DEFAULT_TTL_HOURS


def _parse_datetime(value):

    text = _safe_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def explicit_live_research_requested(query):

    return _has_any(query, (
        "current research",
        "latest research",
        "live research",
        "fresh research",
        "deep research",
        "deep dive",
        "latest",
        "current",
        "live",
        "up to date",
        "web search",
        "search the web"
    ))


def _deep_research_requested(query):

    lowered = _safe_text(query).casefold()
    return (
        explicit_live_research_requested(query)
        or lowered.startswith("research ")
        or _has_any(query, (
            "update thesis",
            "deep dive",
            "full breakdown",
            "comprehensive",
            "bull case",
            "bear case"
        ))
    )


def _profile_generated_at(profile, store):

    return (
        _parse_datetime(profile.get("generated_at"))
        or _parse_datetime(profile.get("as_of"))
        or _parse_datetime(store.get("generated_at"))
    )


def fresh_cached_research(tickers, research_evidence_store=None,
                          ttl_hours=None, now=None):

    tickers = [
        str(ticker or "").strip().upper()
        for ticker in tickers or []
        if str(ticker or "").strip()
    ]
    if not tickers or not isinstance(research_evidence_store, dict):
        return False

    current = now or datetime.now()
    max_age = timedelta(hours=_ttl_hours(ttl_hours))
    profiles = research_evidence_store.get("profiles") or []
    by_ticker = {
        str(profile.get("ticker") or "").strip().upper(): profile
        for profile in profiles
        if isinstance(profile, dict)
    }

    for ticker in tickers:
        profile = by_ticker.get(ticker)
        if not profile:
            return False
        generated_at = _profile_generated_at(profile, research_evidence_store)
        if not generated_at or current - generated_at > max_age:
            return False

    return True


def classify_execution_tier(user_query, investment_intent=None,
                            research_evidence_store=None, ttl_hours=None):

    query = _safe_text(user_query)
    normalized = query.casefold().strip(" ?!.")
    tokens = _tokens(query)
    intent = (
        investment_intent
        if isinstance(investment_intent, dict)
        else classify_investment_intent(query)
    )
    intent_name = intent.get("investment_intent") or "unknown"
    tickers = intent.get("tickers") or []
    has_fresh_cache = fresh_cached_research(
        tickers,
        research_evidence_store,
        ttl_hours
    )
    reason = "Default standard context path."
    tier = "STANDARD_CONTEXT"

    if (
        normalized in {"hi", "hello", "hey", "thanks", "thank you", "status", "system status"}
        or "joke" in tokens
        or intent_name in {"security_resolution", "portfolio_change"}
        or is_explicit_security_resolution_query(query)
        or _has_any(query, (
            "top priority",
            "current priority",
            "debug",
            "system status",
            "are you working",
            "portfolio concentration",
            "concentration question"
        ))
    ):
        tier = "FAST_LOCAL"
        reason = "Query can be answered from resolver, memory, or current local artifacts."
    elif _deep_research_requested(query):
        if _has_any(query, ("compare", " vs ", " versus ")) and has_fresh_cache:
            tier = "STANDARD_CONTEXT"
            reason = "Comparison has fresh cached research for requested tickers."
        elif _has_any(query, ("bull case", "bear case")) and has_fresh_cache:
            tier = "STANDARD_CONTEXT"
            reason = "Bull/bear query has fresh cached research for requested tickers."
        else:
            tier = "DEEP_RESEARCH"
            reason = "Query explicitly asks for deep, current, live, or thesis-level research."
    elif _has_any(query, ("compare", " vs ", " versus ")):
        if has_fresh_cache:
            tier = "STANDARD_CONTEXT"
            reason = "Comparison can use fresh cached research."
        else:
            tier = "DEEP_RESEARCH"
            reason = "Comparison is missing fresh cached research."
    elif intent_name in {"ticker_question", "ticker_news"}:
        tier = "STANDARD_CONTEXT"
        reason = (
            "Ticker query can use existing local artifacts and cached research."
            if has_fresh_cache
            else "Regular ticker query should start with local context before live research."
        )
    elif intent_name in {"holding_news", "market_opportunities", "market_risks"}:
        tier = "STANDARD_CONTEXT"
        reason = "Portfolio/news/market context can use existing artifacts."

    if tier == "FAST_LOCAL":
        max_seconds = 3
    elif tier == "STANDARD_CONTEXT":
        max_seconds = 10
    else:
        max_seconds = 60

    live_allowed = tier == "DEEP_RESEARCH" or explicit_live_research_requested(query)
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "execution_tier": tier,
        "reason": reason,
        "live_research_allowed": bool(live_allowed),
        "web_search_allowed": bool(live_allowed and tier == "DEEP_RESEARCH"),
        "artifact_write_allowed": True,
        "max_expected_seconds": max_seconds,
        "cache_ttl_hours": _ttl_hours(ttl_hours),
        "cached_research_available": bool(has_fresh_cache),
        "slow_path_reasons": [] if tier != "DEEP_RESEARCH" else [reason]
    }
