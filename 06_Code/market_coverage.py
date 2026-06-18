import csv
import json
import re
from datetime import datetime
from pathlib import Path

from echo_investment_intent import classify_investment_intent
from security_master_search import (
    load_current_holdings,
    load_security_master,
    load_watchlist,
    search_security_master
)


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_JSON_PATH = REPORTS_DIR / "market_coverage.json"
DEFAULT_TEXT_PATH = REPORTS_DIR / "market_coverage.txt"
DEFAULT_THESES_PATH = BASE_DIR / "02_Data" / "theses.csv"

TERM_STOPWORDS = {
    "inc",
    "corp",
    "corporation",
    "class",
    "shares",
    "common",
    "ordinary",
    "new",
    "the",
    "and",
    "company",
    "fund",
    "etf",
    "trust",
    "holdings",
    "holding",
    "can",
    "from",
    "within",
    "but",
    "and",
    "or",
    "provides",
    "provide",
    "offers",
    "offer",
    "exposure",
    "return",
    "returns",
    "potential",
    "benefit",
    "demand",
    "risk",
    "risks"
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


def _term_tokens(value):

    return [
        token for token in re.findall(r"[A-Za-z][A-Za-z0-9&.-]{1,}", str(value or ""))
        if token.casefold() not in TERM_STOPWORDS
        and not token.isdigit()
    ]


def _add_term(terms, value):

    text = _safe_text(value)
    if not text or text.upper() == "CASH0":
        return
    if text.casefold() in {"cash", "cash investments", "cash & cash investments"}:
        return
    if text not in terms:
        terms.append(text)


def _aliases(ticker, name, category=None):

    aliases = []
    _add_term(aliases, ticker)
    _add_term(aliases, name)
    _add_term(aliases, category)

    tokens = _term_tokens(name)
    for size in (3, 2, 1):
        for index in range(0, max(len(tokens) - size + 1, 0)):
            fragment = " ".join(tokens[index:index + size])
            if len(fragment) >= 3:
                _add_term(aliases, fragment)

    return aliases[:12]


def _portfolio_weights(holdings):

    total = sum(_float(row.get("market_value")) for row in holdings)
    weights = {}
    if total <= 0:
        return weights
    for row in holdings:
        ticker = _safe_text(row.get("ticker")).upper()
        if not ticker:
            continue
        weights[ticker] = weights.get(ticker, 0.0) + (
            _float(row.get("market_value")) / total * 100
        )
    return weights


def _item(record, source, is_holding=False, is_watchlist=False,
          portfolio_weight=None):

    ticker = _safe_text(record.get("ticker")).upper()
    name = _safe_text(record.get("name") or record.get("security_name"))
    category = _safe_text(record.get("category"))
    return {
        "ticker": ticker,
        "name": name,
        "category": category,
        "expense_ratio": record.get("expense_ratio"),
        "source": source,
        "aliases": _aliases(ticker, name, category),
        "is_current_holding": bool(is_holding),
        "is_watchlist": bool(is_watchlist),
        "portfolio_weight": portfolio_weight
    }


def _merge_universe(items):

    merged = {}
    order = []
    for item in items:
        ticker = _safe_text(item.get("ticker")).upper()
        key = ticker or _norm(item.get("name"))
        if not key:
            continue
        if key not in merged:
            merged[key] = dict(item)
            order.append(key)
            continue

        existing = merged[key]
        existing["is_current_holding"] = (
            existing.get("is_current_holding") or item.get("is_current_holding")
        )
        existing["is_watchlist"] = (
            existing.get("is_watchlist") or item.get("is_watchlist")
        )
        if item.get("portfolio_weight") is not None:
            existing["portfolio_weight"] = item.get("portfolio_weight")
        if existing.get("source") != item.get("source"):
            existing["source"] = existing.get("source") or item.get("source")
        for alias in item.get("aliases") or []:
            if alias not in existing["aliases"]:
                existing["aliases"].append(alias)
    return [merged[key] for key in order]


def _terms_for(items):

    terms = []
    for item in items:
        for alias in item.get("aliases") or []:
            _add_term(terms, alias)
    return terms


def _load_research_theses(path=None):

    rows = []
    try:
        with Path(path or DEFAULT_THESES_PATH).open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as handle:
            for row in csv.DictReader(handle):
                ticker = _safe_text(row.get("ticker")).upper()
                thesis = _safe_text(row.get("thesis"))
                if not ticker:
                    continue
                rows.append({
                    "ticker": ticker,
                    "name": "",
                    "category": "",
                    "expense_ratio": None,
                    "thesis": thesis,
                    "thesis_status": _safe_text(row.get("thesis_status")),
                    "conviction": _safe_text(row.get("conviction"))
                })
    except (OSError, csv.Error):
        return []
    return rows


def _merge_thesis_terms(items, theses):

    by_ticker = {
        _safe_text(item.get("ticker")).upper(): item
        for item in items
        if _safe_text(item.get("ticker"))
    }
    for thesis in theses:
        item = by_ticker.get(thesis["ticker"])
        if not item:
            continue
        for token in _term_tokens(thesis.get("thesis"))[:8]:
            _add_term(item["aliases"], token)
        item["aliases"] = item["aliases"][:16]


def build_market_coverage(user_query=None, max_security_master_terms=40):

    warnings = []
    holdings = load_current_holdings()
    watchlist = load_watchlist()
    weights = _portfolio_weights(holdings)
    items = []

    for row in holdings:
        ticker = _safe_text(row.get("ticker")).upper()
        if ticker == "CASH0":
            continue
        items.append(_item(
            row,
            "holding",
            is_holding=True,
            portfolio_weight=round(weights.get(ticker, 0.0), 4)
        ))

    for row in watchlist:
        ticker = _safe_text(row.get("ticker")).upper()
        if ticker == "CASH0":
            continue
        items.append(_item(row, "watchlist", is_watchlist=True))

    theses = _load_research_theses()
    thesis_tickers = {
        _safe_text(row.get("ticker")).upper()
        for row in theses
        if _safe_text(row.get("ticker"))
    }
    known_tickers = {
        _safe_text(item.get("ticker")).upper()
        for item in items
        if _safe_text(item.get("ticker"))
    }
    if thesis_tickers:
        for row in load_security_master():
            ticker = _safe_text(row.get("ticker")).upper()
            if ticker not in thesis_tickers or ticker in known_tickers or ticker == "CASH0":
                continue
            items.append(_item(row, "security_master"))
            known_tickers.add(ticker)

    intent = classify_investment_intent(user_query or "")
    query_matches = []
    if user_query:
        search = search_security_master(
            user_query,
            tickers=intent.get("tickers"),
            categories=intent.get("categories"),
            max_results=max_security_master_terms
        )
        query_matches = search.get("matches") or []
        warnings.extend(search.get("warnings") or [])
        for match in query_matches:
            items.append(_item(match, "query"))

    category_terms = []
    for value in intent.get("categories") or []:
        _add_term(category_terms, value)

    security_master_terms = []
    if user_query:
        for match in query_matches:
            for alias in _aliases(
                match.get("ticker"),
                match.get("name"),
                match.get("category")
            ):
                _add_term(security_master_terms, alias)
    else:
        for row in load_security_master()[:max_security_master_terms]:
            for alias in _aliases(row.get("ticker"), row.get("name"), row.get("category"))[:3]:
                _add_term(security_master_terms, alias)

    universe = _merge_universe(items)
    _merge_thesis_terms(universe, theses)
    holding_items = [item for item in universe if item.get("is_current_holding")]
    watch_items = [item for item in universe if item.get("is_watchlist")]
    query_items = [item for item in universe if item.get("source") == "query"]

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "holdings_terms": _terms_for(holding_items),
        "watchlist_terms": _terms_for(watch_items),
        "query_terms": _terms_for(query_items),
        "security_master_terms": security_master_terms,
        "sector_category_terms": category_terms,
        "coverage_universe": universe,
        "warnings": warnings
    }


def render_market_coverage_text(coverage):

    lines = [
        "MARKET COVERAGE",
        "",
        f"Generated At: {coverage.get('generated_at')}",
        f"Holdings Terms: {len(coverage.get('holdings_terms') or [])}",
        f"Watchlist Terms: {len(coverage.get('watchlist_terms') or [])}",
        f"Query Terms: {len(coverage.get('query_terms') or [])}",
        f"Security Master Terms: {len(coverage.get('security_master_terms') or [])}",
        f"Universe Size: {len(coverage.get('coverage_universe') or [])}",
        "",
        "Coverage Universe"
    ]
    for item in (coverage.get("coverage_universe") or [])[:80]:
        lines.append(
            f"- {item.get('ticker') or 'UNKNOWN'} | {item.get('name') or ''} | "
            f"{item.get('category') or ''} | source {item.get('source')} | "
            f"holding {item.get('is_current_holding')} | watchlist {item.get('is_watchlist')} | "
            f"weight {item.get('portfolio_weight')}"
        )
    if not coverage.get("coverage_universe"):
        lines.append("None")
    lines.extend(["", "Warnings"])
    lines.extend(coverage.get("warnings") or ["None"])
    return "\n".join(lines) + "\n"


def write_market_coverage_json(coverage, path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def write_market_coverage_text(coverage, path=None):

    path = Path(path or DEFAULT_TEXT_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_market_coverage_text(coverage), encoding="utf-8")
    except OSError as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def read_market_coverage(path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_market_coverage()
    return value if isinstance(value, dict) else build_market_coverage()


def build_and_write_market_coverage(user_query=None):

    coverage = build_market_coverage(user_query)
    return {
        "coverage": coverage,
        "json_result": write_market_coverage_json(coverage),
        "text_result": write_market_coverage_text(coverage)
    }
