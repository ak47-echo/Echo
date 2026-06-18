import csv
import json
import re
from datetime import datetime
from pathlib import Path

from agents.research_agent import (
    classify_factor,
    classify_security,
    get_thesis,
    load_cached_market_data
)
from echo_investment_intent import classify_investment_intent
from market_coverage import build_market_coverage, read_market_coverage
from security_master_search import (
    load_current_holdings,
    load_security_master,
    load_watchlist,
    search_security_master
)


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_JSON_PATH = REPORTS_DIR / "security_intelligence.json"
DEFAULT_TEXT_PATH = REPORTS_DIR / "security_intelligence.txt"
NEWS_REPORT_PATH = REPORTS_DIR / "agents" / "news_full_report.txt"
ECHO_STATE_PATH = REPORTS_DIR / "echo_state.json"

QUALITY_ONLY_TERMS = {
    "low conviction",
    "reevaluate",
    "buy",
    "sell",
    "top priority",
    "recommendation",
    "consider reducing",
    "consider adding"
}

GENERIC_NEWS_NAME_TERMS = {
    "inc",
    "corp",
    "class",
    "common",
    "shares",
    "group",
    "holdings",
    "holding",
    "international",
    "energy",
    "growth",
    "value",
    "blend",
    "small",
    "large",
    "mid",
    "etf",
    "trust",
    "u.s",
    "us",
    "new"
}


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _norm(value):

    return _safe_text(value).casefold()


def _float(value):

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _float_or_none(value):

    text = _safe_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _unique(items):

    result = []
    for item in items or []:
        text = _safe_text(item)
        if text and text not in result:
            result.append(text)
    return result


def _read_text(path):

    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_json(path):

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _ticker_from_query(ticker_or_query):

    query = _safe_text(ticker_or_query).upper()
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", query):
        return query

    intent = classify_investment_intent(ticker_or_query or "")
    tickers = intent.get("tickers") or []
    if tickers:
        return _safe_text(tickers[0]).upper()

    search = search_security_master(ticker_or_query or "", max_results=1)
    matches = search.get("matches") or []
    if matches:
        return _safe_text(matches[0].get("ticker")).upper()

    return query.split()[0] if query else ""


def _holding_summary(ticker):

    ticker = _safe_text(ticker).upper()
    rows = [
        row for row in load_current_holdings()
        if _safe_text(row.get("ticker")).upper() == ticker
    ]
    total_value = sum(_float(row.get("market_value")) for row in rows)
    portfolio_total = sum(
        _float(row.get("market_value"))
        for row in load_current_holdings()
    )
    if not rows:
        return None
    return {
        "accounts": sorted({
            _safe_text(row.get("account"))
            for row in rows
            if _safe_text(row.get("account"))
        }),
        "quantity": sum(_float(row.get("quantity")) for row in rows),
        "market_value": round(total_value, 2),
        "portfolio_weight": (
            round(total_value / portfolio_total * 100, 4)
            if portfolio_total > 0
            else None
        ),
        "name": _safe_text(rows[0].get("name") or rows[0].get("security_name")),
        "category": _safe_text(rows[0].get("category"))
    }


def _watchlist_record(ticker):

    ticker = _safe_text(ticker).upper()
    for row in load_watchlist():
        if _safe_text(row.get("ticker")).upper() == ticker:
            return row
    return None


def _security_master_record(ticker):

    ticker = _safe_text(ticker).upper()
    for row in load_security_master():
        if _safe_text(row.get("ticker")).upper() == ticker:
            return row
    return None


def _coverage_item(ticker, query=None):

    ticker = _safe_text(ticker).upper()
    try:
        coverage = build_market_coverage(query or ticker)
    except Exception:
        coverage = read_market_coverage()

    for item in coverage.get("coverage_universe") or []:
        if _safe_text(item.get("ticker")).upper() == ticker:
            return item
    return {}


def _macro_state():

    state = _read_json(ECHO_STATE_PATH)
    current = (
        state.get("operating_context", {})
        .get("current_state", {})
        if isinstance(state.get("operating_context"), dict)
        else {}
    )
    return {
        "macro_regime": _safe_text(current.get("macro_regime")),
        "dominant_theme": _safe_text(current.get("dominant_theme")),
        "news_top_narrative": _safe_text(current.get("news_top_narrative"))
    }


def _category_macro_exposures(category, name):

    text = f"{category} {name}".casefold()
    exposures = []
    if "growth" in text:
        exposures.append("Growth/rates exposure: sensitive to inflation, rates, and discount-rate changes.")
    if "energy" in text or "mlp" in text or "oil" in text:
        exposures.append("Energy exposure: sensitive to oil prices, supply shocks, and geopolitics.")
    if "bitcoin" in text or "crypto" in text:
        exposures.append("Crypto/liquidity exposure: sensitive to rates, liquidity, and risk appetite.")
    if "small" in text:
        exposures.append("Small-cap exposure: sensitive to credit conditions, rates, and growth expectations.")
    if "health" in text:
        exposures.append("Healthcare exposure: sensitive to regulation, reimbursement, and policy risk.")
    if "treasury" in text or "bond" in text:
        exposures.append("Rate/yield exposure: sensitive to Fed policy and Treasury yields.")
    return exposures


def _thesis_factors(thesis_text):

    text = _safe_text(thesis_text)
    if not text:
        return [], []

    lower = text.casefold()
    bull = []
    bear = []
    if "demand" in lower or "growth" in lower or "upside" in lower:
        bull.append(f"Thesis support: {text}")
    if "diversification" in lower or "complement" in lower:
        bull.append(f"Diversification thesis: {text}")
    if "risk" in lower or "competition" in lower or "regulatory" in lower:
        bear.append(f"Thesis risk: {text}")
    if not bull:
        bull.append(f"Thesis on file: {text}")
    return bull, bear


def _category_factors(ticker, category, name):

    classification = classify_security(ticker, category=category, name=name)
    factors = classify_factor(category=category, name=name)
    bull = []
    bear = []
    asset_class = classification.get("asset_class")
    security_type = classification.get("security_type")
    risk_bucket = classification.get("risk_bucket")
    if asset_class and asset_class != "unknown":
        bull.append(f"Classified as {asset_class} {security_type}; factors: {', '.join(factors)}.")
    if risk_bucket in {"high", "speculative"}:
        bear.append(f"Security classification risk bucket is {risk_bucket}.")
    return bull, bear, classification, factors


def _news_exposures(ticker, name, category):

    report = _read_text(NEWS_REPORT_PATH)
    if not report:
        return [], ["No local News Agent report was available."]

    name_parts = [
        part.strip(".,®")
        for part in re.split(r"\s+", name or "")
        if len(part.strip(".,®")) >= 5
        and part.strip(".,®").casefold() not in GENERIC_NEWS_NAME_TERMS
    ]
    terms = _unique([ticker, name, *name_parts])
    direct = [
        term for term in terms
        if term and re.search(
            r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])",
            report,
            flags=re.IGNORECASE
        )
    ]
    if direct:
        return [
            f"Direct local News Agent mention found for: {', '.join(direct[:5])}."
        ], []
    if category and category.casefold() in report.casefold():
        return [
            f"No direct company mention found; category/theme mention found for {category}."
        ], []
    return [], ["No direct local news was found for this ticker."]


def _historical_market_data(ticker):

    result = load_cached_market_data(ticker)
    if not result:
        return {}, ["Cached historical market data was not available."]
    rows = result.get("rows") or []
    if len(rows) < 2:
        return {
            "status": result.get("status"),
            "data_points": len(rows),
            "source": result.get("source")
        }, ["Historical market data cache has too few rows."]

    first = rows[0]
    latest = rows[-1]
    first_close = _float(first.get("close"))
    latest_close = _float(latest.get("close"))
    trailing_return = (
        round((latest_close / first_close - 1) * 100, 2)
        if first_close > 0
        else None
    )
    return {
        "status": result.get("status"),
        "source": result.get("source"),
        "data_points": len(rows),
        "start_date": first.get("date"),
        "end_date": latest.get("date"),
        "first_close": first_close,
        "latest_close": latest_close,
        "trailing_return_percent": trailing_return
    }, []


def _quality_flags(thesis, profile):

    flags = []
    if not thesis:
        flags.append("Missing thesis: quality-control signal only, not investment evidence.")
    conviction = _safe_text(profile.get("conviction")).casefold()
    status = _safe_text(profile.get("thesis_status")).casefold()
    if conviction == "low":
        flags.append("Low conviction: quality-control signal only, not investment evidence.")
    if status in {"", "missing", "unknown"}:
        flags.append("Thesis status missing: quality-control signal only.")
    elif status == "inactive":
        flags.append("Inactive thesis: quality-control signal only.")
    return flags


def _confidence(known_data, missing_data):

    known_count = len(known_data)
    missing_count = len(missing_data)
    if known_count >= 6 and missing_count <= 1:
        return "HIGH"
    if known_count >= 3:
        return "MEDIUM"
    return "LOW"


def build_security_profile(ticker_or_query):

    ticker = _ticker_from_query(ticker_or_query)
    holding = _holding_summary(ticker)
    watchlist = _watchlist_record(ticker)
    master = _security_master_record(ticker)
    coverage = _coverage_item(ticker, ticker_or_query)
    thesis = get_thesis(ticker)

    name = (
        _safe_text((holding or {}).get("name"))
        or _safe_text((watchlist or {}).get("name"))
        or _safe_text((master or {}).get("name"))
        or _safe_text(coverage.get("name"))
    )
    category = (
        _safe_text((holding or {}).get("category"))
        or _safe_text((watchlist or {}).get("category"))
        or _safe_text((master or {}).get("category"))
        or _safe_text(coverage.get("category"))
    )
    expense_ratio = (
        (watchlist or {}).get("expense_ratio")
        if watchlist and (watchlist or {}).get("expense_ratio") is not None
        else (master or {}).get("expense_ratio")
    )
    thesis_summary = _safe_text((thesis or {}).get("thesis"))
    thesis_status = _safe_text((thesis or {}).get("thesis_status"))
    conviction = _safe_text((thesis or {}).get("conviction"))

    bull_factors, thesis_bears = _thesis_factors(thesis_summary)
    category_bulls, category_bears, classification, factors = _category_factors(
        ticker,
        category,
        name
    )
    macro_exposures = _category_macro_exposures(category, name)
    macro_state = _macro_state()
    if macro_state.get("macro_regime"):
        macro_exposures.append(f"Current local macro regime: {macro_state['macro_regime']}.")
    news_exposures, news_missing = _news_exposures(ticker, name, category)
    historical_data, historical_missing = _historical_market_data(ticker)

    known_data = []
    missing_data = []
    if master:
        known_data.append("security_master metadata")
    else:
        missing_data.append("security_master metadata")
    if holding:
        known_data.append("portfolio holding data")
    if watchlist:
        known_data.append("watchlist data")
    if thesis:
        known_data.append("thesis text")
    else:
        missing_data.append("thesis text")
    if news_exposures:
        known_data.append("local news exposure")
    missing_data.extend(news_missing)
    if macro_exposures:
        known_data.append("macro/category exposure")
    if historical_data:
        known_data.append("cached historical market data")
    missing_data.extend(historical_missing)
    if classification.get("asset_class") != "unknown":
        known_data.append("security classification")
    else:
        missing_data.append("category/factor classification")

    profile = {
        "ticker": ticker,
        "name": name,
        "category": category,
        "expense_ratio": _float_or_none(expense_ratio),
        "is_current_holding": bool(holding),
        "is_watchlist": bool(watchlist),
        "portfolio_weight": (holding or {}).get("portfolio_weight"),
        "thesis_summary": thesis_summary,
        "thesis_status": thesis_status,
        "conviction": conviction,
        "bull_factors": _unique(bull_factors + category_bulls),
        "bear_factors": _unique(thesis_bears + category_bears),
        "macro_exposures": _unique(macro_exposures),
        "news_exposures": _unique(news_exposures),
        "historical_market_data": historical_data,
        "research_quality_flags": [],
        "known_data": _unique(known_data),
        "missing_data": _unique(missing_data),
        "confidence": "LOW",
        "generated_at": _now()
    }
    profile["research_quality_flags"] = _quality_flags(thesis, profile)
    profile["confidence"] = _confidence(
        profile["known_data"],
        profile["missing_data"]
    )
    profile["classification"] = classification
    profile["factors"] = factors
    return profile


def compare_security_profiles(tickers):

    profiles = [
        build_security_profile(ticker)
        for ticker in (tickers or [])
        if _safe_text(ticker)
    ]
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "tickers": [profile["ticker"] for profile in profiles],
        "profiles": profiles,
        "comparison": [
            {
                "ticker": profile["ticker"],
                "held_status": (
                    "current_holding"
                    if profile.get("is_current_holding")
                    else "not_held"
                ),
                "is_watchlist": profile.get("is_watchlist"),
                "category": profile.get("category"),
                "thesis_available": bool(profile.get("thesis_summary")),
                "bull_factors": profile.get("bull_factors") or [],
                "bear_factors": profile.get("bear_factors") or [],
                "macro_exposures": profile.get("macro_exposures") or [],
                "direct_news": profile.get("news_exposures") or [],
                "missing_data": profile.get("missing_data") or [],
                "confidence": profile.get("confidence")
            }
            for profile in profiles
        ],
        "evidence_policy": (
            "Previous recommendations, low conviction labels, buy/sell text, "
            "top-priority text, and reevaluate text are not evidence. "
            "Research quality flags are quality-control signals only."
        )
    }


def _default_report_tickers(tickers=None):

    if tickers:
        return _unique(_safe_text(ticker).upper() for ticker in tickers)
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
    return _unique(holdings + watchlist)


def build_security_intelligence_report(tickers=None):

    report_tickers = _default_report_tickers(tickers)
    profiles = [build_security_profile(ticker) for ticker in report_tickers]
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "profile_count": len(profiles),
        "tickers": report_tickers,
        "profiles": profiles,
        "evidence_policy": (
            "Previous recommendations are not evidence. Low conviction, "
            "reevaluate, buy, sell, and top-priority text may appear only as "
            "research quality-control signals."
        ),
        "warnings": []
    }


def render_security_intelligence_text(report):

    lines = [
        "SECURITY INTELLIGENCE",
        "",
        f"Generated At: {report.get('generated_at')}",
        f"Profile Count: {report.get('profile_count') or 0}",
        f"Evidence Policy: {report.get('evidence_policy')}",
        "",
        "Profiles"
    ]
    for profile in report.get("profiles") or []:
        lines.extend([
            (
                f"- {profile.get('ticker')} | {profile.get('name') or 'Unknown'} | "
                f"{profile.get('category') or 'uncategorized'} | "
                f"held {profile.get('is_current_holding')} | "
                f"watchlist {profile.get('is_watchlist')} | "
                f"confidence {profile.get('confidence')}"
            ),
            f"  Bull: {'; '.join(profile.get('bull_factors') or ['None'])}",
            f"  Bear: {'; '.join(profile.get('bear_factors') or ['None'])}",
            f"  Macro: {'; '.join(profile.get('macro_exposures') or ['None'])}",
            f"  News: {'; '.join(profile.get('news_exposures') or ['No direct local news found'])}",
            f"  Quality Flags: {'; '.join(profile.get('research_quality_flags') or ['None'])}",
            f"  Missing Data: {'; '.join(profile.get('missing_data') or ['None'])}"
        ])
    if not report.get("profiles"):
        lines.append("None")
    return "\n".join(lines) + "\n"


def write_security_intelligence_json(report, path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def write_security_intelligence_text(report, path=None):

    path = Path(path or DEFAULT_TEXT_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_security_intelligence_text(report), encoding="utf-8")
    except OSError as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def read_security_intelligence(path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    value = _read_json(path)
    return value if value else build_security_intelligence_report()


def build_and_write_security_intelligence_report(tickers=None):

    report = build_security_intelligence_report(tickers)
    return {
        "report": report,
        "json_result": write_security_intelligence_json(report),
        "text_result": write_security_intelligence_text(report)
    }
