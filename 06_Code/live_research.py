import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from echo_investment_intent import classify_investment_intent
from security_master_search import load_current_holdings, load_watchlist, search_security_master


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "04_Reports"
EVIDENCE_JSON_PATH = REPORTS_DIR / "research_evidence_store.json"
EVIDENCE_TEXT_PATH = REPORTS_DIR / "research_evidence_store.txt"
THESIS_REFRESH_JSON_PATH = REPORTS_DIR / "thesis_refresh.json"
THESIS_REFRESH_TEXT_PATH = REPORTS_DIR / "thesis_refresh.txt"


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _unique(items):

    result = []
    for item in items or []:
        text = _safe_text(item)
        if text and text not in result:
            result.append(text)
    return result


def _env_flag(name, default=False):

    value = os.getenv(name)
    if value is None:
        return bool(default)
    return str(value).strip().casefold() in {"1", "true", "yes", "on"}


def live_research_enabled():

    return _env_flag("LIVE_RESEARCH_ENABLED", False)


def anthropic_web_search_enabled():

    return _env_flag("ANTHROPIC_WEB_SEARCH_ENABLED", False)


def live_research_source_mode():

    if live_research_enabled() and anthropic_web_search_enabled():
        return "hybrid"
    return "local_only"


def get_anthropic_web_search_tools():

    if not anthropic_web_search_enabled():
        return []
    return [{"type": "web_search_20250305", "name": "web_search"}]


def live_research_provider_policy():

    return {
        "live_research_enabled": live_research_enabled(),
        "anthropic_web_search_enabled": anthropic_web_search_enabled(),
        "source_mode": live_research_source_mode(),
        "anthropic_tools": get_anthropic_web_search_tools(),
        "live_web_discipline": (
            "Do not claim live web evidence unless the Anthropic web search "
            "tool returned it in provider context. Local-only research must "
            "state missing live web evidence."
        )
    }


def _max_tickers_per_run():

    try:
        return max(1, int(os.getenv("LIVE_RESEARCH_MAX_TICKERS_PER_RUN", "5")))
    except ValueError:
        return 5


def _read_json(path):

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(data, path):

    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def _write_text(text, path):

    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text), encoding="utf-8")
    except OSError as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def _ticker_candidates(tickers=None, query=None):

    explicit = [
        _safe_text(ticker).upper()
        for ticker in (tickers or [])
        if _safe_text(ticker)
    ]
    if explicit:
        return _unique(ticker for ticker in explicit if ticker != "CASH0")

    query_text = _safe_text(query)
    if query_text:
        intent = classify_investment_intent(query_text)
        if intent.get("tickers"):
            return _unique(
                _safe_text(ticker).upper()
                for ticker in intent.get("tickers") or []
                if _safe_text(ticker).upper() != "CASH0"
            )
        search = search_security_master(query_text, max_results=3)
        matches = [
            _safe_text(match.get("ticker")).upper()
            for match in search.get("matches") or []
            if _safe_text(match.get("ticker")).upper() != "CASH0"
        ]
        if matches:
            return _unique(matches)

    holdings = [
        _safe_text(row.get("ticker")).upper()
        for row in load_current_holdings()
        if _safe_text(row.get("ticker")).upper() != "CASH0"
    ]
    watchlist = [
        _safe_text(row.get("ticker")).upper()
        for row in load_watchlist()
        if _safe_text(row.get("ticker")).upper() != "CASH0"
    ]
    return _unique(holdings + watchlist)[:_max_tickers_per_run()]


def _evidence(claim, source, source_type, confidence="MEDIUM"):

    return {
        "claim": _safe_text(claim),
        "source": _safe_text(source),
        "source_type": _safe_text(source_type),
        "as_of": _now(),
        "confidence": _safe_text(confidence).upper() or "MEDIUM"
    }


def _profile_from_security_intelligence(ticker_or_query):

    from security_intelligence import build_security_profile

    return build_security_profile(ticker_or_query)


def _research_status(source_mode, missing_data):

    missing_text = " ".join(missing_data or []).casefold()
    if source_mode == "local_only":
        return "insufficient"
    if "live web evidence" in missing_text:
        return "insufficient"
    return "fresh"


def build_research_profile(ticker_or_query):

    security_profile = _profile_from_security_intelligence(ticker_or_query)
    ticker = _safe_text(security_profile.get("ticker")).upper()
    name = _safe_text(security_profile.get("name"))
    category = _safe_text(security_profile.get("category"))
    source_mode = live_research_source_mode()
    missing_data = list(security_profile.get("missing_data") or [])
    evidence = []

    if source_mode == "local_only":
        if not live_research_enabled():
            missing_data.append("Live research is disabled by LIVE_RESEARCH_ENABLED.")
        if not anthropic_web_search_enabled():
            missing_data.append("Missing live web evidence: ANTHROPIC_WEB_SEARCH_ENABLED is false.")
    else:
        missing_data.append(
            "Live web search is enabled, but generated claims must still be "
            "limited to evidence returned through the provider path."
        )

    if name or category:
        evidence.append(_evidence(
            f"{ticker} identity resolved as {name or 'Unknown'} in {category or 'uncategorized'}.",
            "security_master.csv / market coverage",
            "security_master",
            "HIGH"
        ))
    if security_profile.get("is_current_holding"):
        evidence.append(_evidence(
            f"{ticker} is a current holding with portfolio weight {security_profile.get('portfolio_weight')}.",
            "holdings_normalized.csv",
            "portfolio",
            "HIGH"
        ))
    for item in security_profile.get("macro_exposures") or []:
        evidence.append(_evidence(item, "Macro Agent / category mapping", "macro_agent"))
    for item in security_profile.get("news_exposures") or []:
        evidence.append(_evidence(item, "News Agent local report", "news_agent"))
    historical = security_profile.get("historical_market_data") or {}
    if historical:
        evidence.append(_evidence(
            f"Cached market data available through {historical.get('end_date') or 'unknown date'}.",
            "Research Agent cached market data",
            "historical_market_data"
        ))

    bull_case = _unique(security_profile.get("bull_factors") or [])
    bear_case = _unique(security_profile.get("bear_factors") or [])
    macro = _unique(security_profile.get("macro_exposures") or [])
    news = _unique(security_profile.get("news_exposures") or [])
    quality_flags = _unique(security_profile.get("research_quality_flags") or [])

    if quality_flags:
        missing_data.append(
            "Research quality flags are present and must not be used as investment evidence."
        )

    company_summary = (
        f"{ticker} is {name or 'an unresolved security'}"
        f"{' in ' + category if category else ''}."
    )
    business_model = (
        f"Local data identifies the security category as {category}."
        if category
        else "Local data does not include enough business model detail."
    )
    if security_profile.get("thesis_source") == "manual_legacy_thesis":
        missing_data.append(
            "Only a manual legacy thesis was found; it is not treated as current truth."
        )

    confidence = "LOW"
    if len(evidence) >= 4 and source_mode != "local_only":
        confidence = "HIGH"
    elif len(evidence) >= 2:
        confidence = "MEDIUM"

    return {
        "ticker": ticker,
        "name": name,
        "generated_at": _now(),
        "source_mode": source_mode,
        "company_summary": company_summary,
        "business_model": business_model,
        "bull_case": bull_case,
        "bear_case": bear_case,
        "key_drivers": _unique(bull_case[:3] + macro[:3]),
        "key_risks": _unique(bear_case[:4]),
        "recent_developments": news or ["No direct local news was found for this ticker."],
        "valuation_notes": (
            [f"Cached trailing return: {historical.get('trailing_return_percent')}%."]
            if historical.get("trailing_return_percent") is not None
            else ["No valuation model or current valuation data was supplied."]
        ),
        "competitive_position": [
            "No local competitive-position evidence was supplied."
        ],
        "macro_sensitivity": macro,
        "portfolio_implications": _portfolio_implications(security_profile),
        "thesis_invalidation_signals": _unique(bear_case[:3] + [
            "Refresh the thesis if direct news, fundamentals, valuation, or portfolio fit contradicts the current evidence."
        ]),
        "evidence": evidence,
        "missing_data": _unique(missing_data),
        "confidence": confidence
    }


def _portfolio_implications(security_profile):

    ticker = _safe_text(security_profile.get("ticker")).upper()
    implications = []
    if security_profile.get("is_current_holding"):
        implications.append(
            f"{ticker} is currently held; thesis implications are informational and require user approval before any action."
        )
        if security_profile.get("portfolio_weight") is not None:
            implications.append(
                f"Current portfolio weight is {security_profile.get('portfolio_weight')}%."
            )
    else:
        implications.append(
            f"{ticker} is not currently held based on latest local portfolio data."
        )
    return implications


def build_research_evidence_store(tickers=None, query=None):

    selected_tickers = _ticker_candidates(tickers, query)
    profiles = [
        build_research_profile(ticker)
        for ticker in selected_tickers[:_max_tickers_per_run()]
    ]
    warnings = []
    if live_research_source_mode() == "local_only":
        warnings.append(
            "Live web research evidence is unavailable; research is local-only."
        )
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "source_mode": live_research_source_mode(),
        "profile_count": len(profiles),
        "tickers": [profile.get("ticker") for profile in profiles],
        "profiles": profiles,
        "evidence_policy": (
            "Generated evidence may use local news, macro, portfolio, security "
            "master, and historical market data. Previous recommendations are "
            "not evidence."
        ),
        "warnings": warnings
    }


def _summarize(items, fallback):

    selected = _unique(items)[:3]
    if not selected:
        return fallback
    return " ".join(selected)


def _next_review():

    return (datetime.now() + timedelta(days=30)).date().isoformat()


def thesis_refresh_from_profile(profile):

    ticker = _safe_text(profile.get("ticker")).upper()
    source_mode = _safe_text(profile.get("source_mode"))
    missing = profile.get("missing_data") or []
    status = _research_status(source_mode, missing)
    bull_summary = _summarize(
        profile.get("bull_case") or [],
        "No durable bull case was established from local evidence."
    )
    bear_summary = _summarize(
        profile.get("bear_case") or profile.get("key_risks") or [],
        "No durable bear case was established from local evidence."
    )
    current_thesis = (
        f"Current generated research view for {ticker}: {bull_summary} "
        f"Primary risks: {bear_summary}"
    )
    action = "monitor"
    conviction_direction = "stable"
    if status == "insufficient":
        action = "research_more"
        conviction_direction = "unknown"
    if any("deteriorat" in _safe_text(item).casefold() for item in profile.get("key_risks") or []):
        action = "research_more"
        conviction_direction = "deteriorating"

    return {
        "ticker": ticker,
        "current_thesis": current_thesis,
        "bull_case_summary": bull_summary,
        "bear_case_summary": bear_summary,
        "conviction_direction": conviction_direction,
        "research_status": status,
        "recommended_next_review": _next_review(),
        "portfolio_action_implication": action,
        "requires_user_approval": True
    }


def build_thesis_refresh(tickers=None, query=None, evidence_store=None):

    store = evidence_store or build_research_evidence_store(tickers, query)
    refreshes = [
        thesis_refresh_from_profile(profile)
        for profile in store.get("profiles") or []
    ]
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "source_mode": store.get("source_mode") or live_research_source_mode(),
        "refresh_count": len(refreshes),
        "tickers": [item.get("ticker") for item in refreshes],
        "thesis_refreshes": refreshes,
        "policy": (
            "Generated thesis refreshes are informational. They do not place "
            "trades, alter holdings, or overwrite theses.csv."
        ),
        "warnings": store.get("warnings") or []
    }


def render_research_evidence_store_text(store):

    lines = [
        "RESEARCH EVIDENCE STORE",
        "",
        f"Generated At: {store.get('generated_at')}",
        f"Source Mode: {store.get('source_mode')}",
        f"Profile Count: {store.get('profile_count') or 0}",
        f"Evidence Policy: {store.get('evidence_policy')}",
        ""
    ]
    for profile in store.get("profiles") or []:
        lines.extend([
            f"- {profile.get('ticker')} | {profile.get('name') or 'Unknown'} | confidence {profile.get('confidence')}",
            f"  Company: {profile.get('company_summary')}",
            f"  Bull: {'; '.join(profile.get('bull_case') or ['None'])}",
            f"  Bear: {'; '.join(profile.get('bear_case') or ['None'])}",
            f"  Recent: {'; '.join(profile.get('recent_developments') or ['None'])}",
            f"  Missing: {'; '.join(profile.get('missing_data') or ['None'])}"
        ])
    if not store.get("profiles"):
        lines.append("No profiles generated.")
    return "\n".join(lines) + "\n"


def render_thesis_refresh_text(report):

    lines = [
        "THESIS REFRESH",
        "",
        f"Generated At: {report.get('generated_at')}",
        f"Source Mode: {report.get('source_mode')}",
        f"Refresh Count: {report.get('refresh_count') or 0}",
        f"Policy: {report.get('policy')}",
        ""
    ]
    for item in report.get("thesis_refreshes") or []:
        lines.extend([
            f"- {item.get('ticker')} | status {item.get('research_status')} | direction {item.get('conviction_direction')}",
            f"  Thesis: {item.get('current_thesis')}",
            f"  Bull: {item.get('bull_case_summary')}",
            f"  Bear: {item.get('bear_case_summary')}",
            f"  Implication: {item.get('portfolio_action_implication')} | user approval {item.get('requires_user_approval')}"
        ])
    if not report.get("thesis_refreshes"):
        lines.append("No thesis refreshes generated.")
    return "\n".join(lines) + "\n"


def write_research_evidence_store_json(store, path=None):

    return _write_json(store, path or EVIDENCE_JSON_PATH)


def write_research_evidence_store_text(store, path=None):

    return _write_text(render_research_evidence_store_text(store), path or EVIDENCE_TEXT_PATH)


def write_thesis_refresh_json(report, path=None):

    return _write_json(report, path or THESIS_REFRESH_JSON_PATH)


def write_thesis_refresh_text(report, path=None):

    return _write_text(render_thesis_refresh_text(report), path or THESIS_REFRESH_TEXT_PATH)


def read_research_evidence_store(path=None):

    value = _read_json(path or EVIDENCE_JSON_PATH)
    return value if value else build_research_evidence_store([])


def read_thesis_refresh(path=None):

    value = _read_json(path or THESIS_REFRESH_JSON_PATH)
    return value if value else build_thesis_refresh([], evidence_store=build_research_evidence_store([]))


def build_and_write_live_research(tickers=None, query=None):

    store = build_research_evidence_store(tickers, query)
    refresh = build_thesis_refresh(tickers, query, store)
    return {
        "research_evidence_store": store,
        "thesis_refresh": refresh,
        "evidence_json_result": write_research_evidence_store_json(store),
        "evidence_text_result": write_research_evidence_store_text(store),
        "thesis_json_result": write_thesis_refresh_json(refresh),
        "thesis_text_result": write_thesis_refresh_text(refresh)
    }
