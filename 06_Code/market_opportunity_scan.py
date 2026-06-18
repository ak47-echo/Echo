import json
from datetime import datetime
from pathlib import Path

from security_master_search import (
    load_current_holdings,
    load_watchlist,
    search_security_master
)


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_JSON_PATH = REPORTS_DIR / "market_opportunity_scan.json"
DEFAULT_TEXT_PATH = REPORTS_DIR / "market_opportunity_scan.txt"


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _load_json(path):

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _current_state():

    return _load_json(REPORTS_DIR / "echo_state.json")


def _candidate(ticker, name, category, direction, reason, source_agents,
               is_current_holding=False, is_watchlist=False,
               security_master_match=None, evidence=None,
               confidence="medium"):

    return {
        "ticker": ticker,
        "name": name,
        "category": category,
        "direction": direction,
        "reason": reason,
        "source_agents": source_agents,
        "confidence": confidence,
        "is_current_holding": bool(is_current_holding),
        "is_watchlist": bool(is_watchlist),
        "security_master_match": security_master_match,
        "evidence": evidence or []
    }


def build_market_opportunity_scan():

    state = _current_state()
    holdings = load_current_holdings()
    watchlist = load_watchlist()
    held = {row.get("ticker"): row for row in holdings}
    watched = {row.get("ticker"): row for row in watchlist}
    source_signals = []
    opportunities = []
    risks = []
    warnings = []

    news = state.get("news_top_narrative") or {}
    macro = state.get("macro_regime") or {}
    portfolio_risk = state.get("portfolio_current_risk") or {}
    theme = state.get("dominant_theme") or {}
    news_title = _safe_text(news.get("title") or news.get("name"))
    macro_name = _safe_text(macro.get("name") or macro.get("title"))
    theme_title = _safe_text(theme.get("theme_title") or theme.get("title"))

    for label, value in (
        ("news", news_title),
        ("macro", macro_name),
        ("theme", theme_title),
        ("portfolio", _safe_text(portfolio_risk.get("title")))
    ):
        if value:
            source_signals.append({"source": label, "signal": value})

    lowered_blob = " ".join(
        [news_title, macro_name, theme_title, json.dumps(state, default=str)]
    ).casefold()

    if any(term in lowered_blob for term in ("energy", "oil", "inflation")):
        search = search_security_master("energy ETF oil", categories=["energy"], max_results=3)
        for match in search.get("matches") or []:
            ticker = match.get("ticker")
            opportunities.append(_candidate(
                ticker,
                match.get("name"),
                match.get("category"),
                "watch",
                "Energy/inflation themes are active; treat as a research candidate only.",
                ["news", "macro"],
                ticker in held,
                ticker in watched,
                match,
                [news_title, macro_name],
                "low"
            ))

    if any(term in lowered_blob for term in ("rates", "fed", "inflation")):
        risk_seen = set()
        for row in holdings:
            category = _safe_text(row.get("category") or row.get("name")).casefold()
            ticker = row.get("ticker")
            if ticker == "CASH0" or ticker in risk_seen:
                continue
            if any(term in category for term in ("growth", "bitcoin", "semiconductor")):
                risk_seen.add(ticker)
                risks.append(_candidate(
                    ticker,
                    row.get("name"),
                    row.get("category"),
                    "downside",
                    "Rates/inflation pressure can pressure long-duration or speculative exposure.",
                    ["portfolio", "macro"],
                    True,
                    ticker in watched,
                    None,
                    [macro_name, theme_title],
                    "medium"
                ))

    for row in watchlist:
        ticker = row.get("ticker")
        opportunities.append(_candidate(
            ticker,
            row.get("name"),
            row.get("category"),
            "watch",
            "Existing watchlist candidate available for research review.",
            ["research"],
            ticker in held,
            True,
            None,
            [_safe_text(row.get("notes"))],
            "medium" if row.get("priority") == "high" else "low"
        ))

    if not opportunities and not risks:
        warnings.append("No conservative opportunity or risk candidates were produced from local signals.")

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "opportunity_candidates": opportunities[:20],
        "risk_candidates": risks[:20],
        "source_signals": source_signals,
        "warnings": warnings
    }


def render_market_opportunity_scan_text(scan):

    lines = [
        "MARKET OPPORTUNITY AND RISK SCAN",
        "",
        f"Generated At: {scan.get('generated_at')}",
        "",
        "Opportunity Candidates"
    ]
    for item in scan.get("opportunity_candidates") or []:
        lines.append(
            f"- {item.get('ticker') or 'UNKNOWN'} | {item.get('direction')} | "
            f"{item.get('reason')}"
        )
    if not scan.get("opportunity_candidates"):
        lines.append("None")
    lines.extend(["", "Risk Candidates"])
    for item in scan.get("risk_candidates") or []:
        lines.append(
            f"- {item.get('ticker') or 'UNKNOWN'} | {item.get('direction')} | "
            f"{item.get('reason')}"
        )
    if not scan.get("risk_candidates"):
        lines.append("None")
    lines.extend(["", "Warnings"])
    lines.extend(scan.get("warnings") or ["None"])
    return "\n".join(lines) + "\n"


def write_market_opportunity_scan_json(scan, path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scan, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def write_market_opportunity_scan_text(scan, path=None):

    path = Path(path or DEFAULT_TEXT_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_market_opportunity_scan_text(scan), encoding="utf-8")
    except OSError as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def read_market_opportunity_scan(path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    scan = _load_json(path)
    return scan if scan else build_market_opportunity_scan()


def build_and_write_market_opportunity_scan():

    scan = build_market_opportunity_scan()
    return {
        "scan": scan,
        "json_result": write_market_opportunity_scan_json(scan),
        "text_result": write_market_opportunity_scan_text(scan)
    }
