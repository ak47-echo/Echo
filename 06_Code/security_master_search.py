import csv
import json
import re
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "02_Data"
DEFAULT_SECURITY_MASTER_PATH = DATA_DIR / "security_master.csv"
DEFAULT_WATCHLIST_PATH = DATA_DIR / "watchlist.csv"
DEFAULT_HOLDINGS_PATH = DATA_DIR / "portfolio_current" / "holdings_normalized.csv"


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _norm(value):

    return _safe_text(value).casefold()


def _tokens(value):

    return [
        token for token in re.findall(r"[a-z0-9]+", _norm(value))
        if token not in {
            "what",
            "about",
            "find",
            "search",
            "for",
            "the",
            "do",
            "you",
            "think",
            "is",
            "are",
            "in",
            "my",
            "worth",
            "researching",
            "stocks",
            "stock",
            "based",
            "recent",
            "news",
            "could",
            "go",
            "up",
            "down"
        }
    ]


def _float_or_none(value):

    text = _safe_text(value)
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _read_csv(path):

    path = Path(path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return []


def load_security_master(path=None):

    rows = []
    for row in _read_csv(path or DEFAULT_SECURITY_MASTER_PATH):
        ticker = _safe_text(row.get("ticker")).upper()
        name = _safe_text(row.get("name"))
        category = _safe_text(row.get("category"))
        if not ticker and not name:
            continue
        rows.append({
            "ticker": ticker,
            "name": name,
            "category": category,
            "expense_ratio": _float_or_none(row.get("expense_ratio"))
        })
    return rows


def load_watchlist(path=None):

    rows = []
    for row in _read_csv(path or DEFAULT_WATCHLIST_PATH):
        ticker = _safe_text(row.get("ticker")).upper()
        if not ticker:
            continue
        rows.append({
            "ticker": ticker,
            "name": _safe_text(row.get("name")),
            "category": _safe_text(row.get("category")),
            "expense_ratio": _float_or_none(row.get("expense_ratio")),
            "priority": _safe_text(row.get("priority")),
            "conviction": _safe_text(row.get("conviction")),
            "notes": _safe_text(row.get("notes"))
        })
    return rows


def load_current_holdings(path=None):

    rows = []
    for row in _read_csv(path or DEFAULT_HOLDINGS_PATH):
        ticker = _safe_text(row.get("ticker")).upper()
        if not ticker:
            continue
        rows.append({
            "account": _safe_text(row.get("account")),
            "ticker": ticker,
            "name": _safe_text(row.get("security_name")),
            "security_name": _safe_text(row.get("security_name")),
            "category": _safe_text(row.get("category")),
            "quantity": _float_or_none(row.get("quantity")) or 0.0,
            "market_value": _float_or_none(row.get("market_value")) or 0.0,
            "expense_ratio": None
        })
    return rows


def _match_record(record, query, tickers, categories):

    ticker = _safe_text(record.get("ticker")).upper()
    name = _safe_text(record.get("name") or record.get("security_name"))
    category = _safe_text(record.get("category"))
    query_norm = _norm(query)
    query_tokens = _tokens(query)
    haystack = f"{ticker} {name} {category}".casefold()
    score = 0
    reasons = []

    if ticker and ticker in tickers:
        score += 120
        reasons.append("ticker")

    for category_query in categories:
        if category_query and category_query in _norm(category):
            score += 70
            reasons.append("category")

    for token in query_tokens:
        if token == ticker.casefold():
            score += 100
            reasons.append("ticker")
        elif token and token in _norm(name):
            score += 35
            reasons.append("name")
        elif token and token in _norm(category):
            score += 30
            reasons.append("category")
        elif token and token in haystack:
            score += 10
            reasons.append("text")

    if "etf" in query_norm or "fund" in query_norm:
        if "etf" in _norm(name) or "fund" in _norm(name):
            score += 45
            reasons.append("fund")
        elif score > 0:
            score = max(score - 20, 0)

    return score, ", ".join(sorted(set(reasons))) or ""


def _result_record(record, reason, score, source):

    return {
        "ticker": _safe_text(record.get("ticker")).upper(),
        "name": _safe_text(record.get("name") or record.get("security_name")),
        "category": _safe_text(record.get("category")),
        "expense_ratio": record.get("expense_ratio"),
        "match_reason": f"{source}:{reason}" if reason else source,
        "score": int(score)
    }


def search_security_master(query, tickers=None, categories=None,
                           max_results=25, path=None):

    query = _safe_text(query)
    tickers = {
        _safe_text(ticker).upper()
        for ticker in (tickers or [])
        if _safe_text(ticker)
    }
    categories = [_norm(category) for category in (categories or [])]
    max_results = max(int(max_results or 25), 1)
    warnings = []
    matches = []
    seen = set()

    source_layers = (
        ("holding", load_current_holdings()),
        ("watchlist", load_watchlist()),
        ("security_master", load_security_master(path))
    )

    if not source_layers[-1][1]:
        warnings.append("security_master.csv could not be read or was empty.")

    for source, records in source_layers:
        for record in records:
            score, reason = _match_record(record, query, tickers, categories)
            if score <= 0:
                continue

            ticker = _safe_text(record.get("ticker")).upper()
            key = ticker or _norm(record.get("name"))
            if key in seen:
                continue
            seen.add(key)
            matches.append(_result_record(record, reason, score, source))

    matches = sorted(
        matches,
        key=lambda item: (-item["score"], item["ticker"], item["name"])
    )[:max_results]

    if not matches:
        warnings.append(
            "Echo does not have enough local security master data for that security."
        )

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "matches": matches,
        "match_count": len(matches),
        "warnings": warnings
    }


def read_security_master_search(path=None):

    path = Path(path or DEFAULT_SECURITY_MASTER_PATH)
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": "",
        "matches": [],
        "match_count": 0,
        "warnings": [
            f"Security master search is query-scoped; source path is {path}."
        ]
    }


def dumps_result(result):

    return json.dumps(result, indent=2, sort_keys=True)
