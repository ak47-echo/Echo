import csv
import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from live_research import live_research_enabled
from security_master_search import (
    DEFAULT_HOLDINGS_PATH,
    DEFAULT_SECURITY_MASTER_PATH,
    DEFAULT_WATCHLIST_PATH,
    load_current_holdings,
    load_security_master,
    load_watchlist
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "02_Data"
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_ALIAS_PATH = DATA_DIR / "security_aliases.json"
DEFAULT_HISTORY_PATH = DATA_DIR / "security_ticker_history.json"
DEFAULT_LIVE_CANDIDATES_PATH = REPORTS_DIR / "security_resolution_live_candidates.json"
DEFAULT_NEWS_CANDIDATES_PATH = REPORTS_DIR / "security_resolution_news_candidates.json"
SECURITY_RESOLUTION_JSON_PATH = REPORTS_DIR / "security_resolution.json"
SECURITY_RESOLUTION_TEXT_PATH = REPORTS_DIR / "security_resolution.txt"

FRESH_TERMS = (
    "ipo",
    "newly listed",
    "new listing",
    "ticker debut",
    "debuted",
    "current exchange listing",
    "listed on",
    "began trading",
    "public listing"
)

STALE_TERMS = (
    "old ticker",
    "ticker changed",
    "renamed",
    "delisted",
    "liquidated",
    "inactive",
    "no longer trading",
    "formerly traded",
    "fund closed"
)

SECURITY_TYPE_TERMS = {
    "etf": ("etf", "fund", "trust"),
    "fund": ("etf", "fund", "index"),
    "stock": ("stock", "company", "corp", "inc", "class"),
    "company": ("stock", "company", "corp", "inc", "class"),
    "crypto": ("crypto", "bitcoin", "token")
}

STOPWORDS = {
    "compare",
    "research",
    "what",
    "do",
    "you",
    "think",
    "about",
    "update",
    "thesis",
    "bull",
    "bear",
    "case",
    "for",
    "vs",
    "versus",
    "and",
    "the",
    "security",
    "stock",
    "ticker"
}


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _norm(value):

    return _safe_text(value).casefold()


def _read_json(path, fallback=None):

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return fallback if fallback is not None else {}
    return value


def _write_json(data, path):

    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": _safe_text(error)}
    return {"success": True, "path": str(path), "error": ""}


def _write_text(text, path):

    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text), encoding="utf-8")
    except OSError as error:
        return {"success": False, "path": str(path), "error": _safe_text(error)}
    return {"success": True, "path": str(path), "error": ""}


def _read_csv_rows(path):

    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return []


def _query_terms(query):

    return [
        token
        for token in re.findall(r"[a-z0-9.]+", _norm(query))
        if token and token not in STOPWORDS
    ]


def _ticker_tokens(query):

    return [
        token.upper()
        for token in re.findall(r"\b[A-Z][A-Z0-9.]{0,9}\b", str(query or ""))
        if token.upper() not in {"I", "A", "ETF", "ETFS", "IRA", "USD", "CASH"}
    ]


def extract_security_mentions(query):

    text = _safe_text(query)
    tickers = _ticker_tokens(text)
    if tickers:
        return tickers

    cleaned = re.sub(
        r"\b(compare|research|update thesis on|what do you think about|bull case for|bear case for)\b",
        " ",
        text,
        flags=re.IGNORECASE
    )
    parts = re.split(r"\bvs\.?|\bversus\b|,|/|\band\b", cleaned, flags=re.IGNORECASE)
    mentions = [_safe_text(part) for part in parts if _safe_text(part)]
    return mentions or ([text] if text else [])


def _security_type(name, category="", explicit=""):

    explicit = _safe_text(explicit).casefold()
    if explicit:
        return explicit
    text = f"{name} {category}".casefold()
    if "etf" in text:
        return "etf"
    if "fund" in text or "index" in text:
        return "fund"
    if "bitcoin" in text or "crypto" in text:
        return "crypto"
    if name:
        return "stock"
    return "unknown"


def _candidate_key(candidate):

    return (
        _safe_text(candidate.get("ticker")).upper(),
        _norm(candidate.get("name")),
        _norm(candidate.get("source"))
    )


def _candidate(ticker, name, security_type, source, confidence, match_reason,
               score=0, status="", source_date="", category=""):

    return {
        "ticker": _safe_text(ticker).upper(),
        "name": _safe_text(name),
        "security_type": _safe_text(security_type) or _security_type(name, category),
        "source": _safe_text(source),
        "confidence": _safe_text(confidence).upper() or "LOW",
        "match_reason": _safe_text(match_reason),
        "score": int(score or 0),
        "status": _safe_text(status),
        "source_date": _safe_text(source_date),
        "category": _safe_text(category)
    }


def _context_security_type(query):

    text = _norm(query)
    for security_type, terms in SECURITY_TYPE_TERMS.items():
        if any(term in text for term in terms):
            return security_type
    return ""


def _context_bonus(candidate, query):

    wanted = _context_security_type(query)
    if not wanted:
        return 0, []
    actual = _norm(candidate.get("security_type"))
    if wanted == actual or wanted in actual:
        return 12, [f"user wording matched {wanted} context"]
    if wanted in {"stock", "company"} and actual in {"etf", "fund"}:
        return -18, [f"user wording conflicts with {actual} candidate"]
    if wanted in {"etf", "fund"} and actual in {"stock", "company"}:
        return -18, [f"user wording conflicts with {actual} candidate"]
    return 0, []


def _freshness_score(candidate):

    text = " ".join([
        _safe_text(candidate.get("name")),
        _safe_text(candidate.get("match_reason")),
        _safe_text(candidate.get("status")),
        _safe_text(candidate.get("source"))
    ]).casefold()
    score = 0
    reasons = []
    if any(term in text for term in FRESH_TERMS):
        score += 24
        reasons.append("fresh listing language")
    if (
        any(term in text for term in STALE_TERMS)
        and "historical_ticker_table" not in _norm(candidate.get("source"))
    ):
        score -= 32
        reasons.append("stale or inactive language")
    source_date = _safe_text(candidate.get("source_date"))
    if source_date:
        try:
            year = int(source_date[:4])
            current_year = datetime.now(timezone.utc).year
            if year >= current_year - 1:
                score += 12
                reasons.append("recent source date")
            elif year <= current_year - 5:
                score -= 12
                reasons.append("old source date")
        except ValueError:
            pass
    return score, reasons


def _similarity(query, name, ticker=""):

    query_norm = _norm(query)
    name_norm = _norm(name)
    ticker_norm = _norm(ticker)
    if ticker_norm and ticker_norm == query_norm:
        return 1.0
    if not query_norm or not name_norm:
        return 0.0
    query_terms = set(_query_terms(query_norm))
    name_terms = set(_query_terms(name_norm))
    overlap = len(query_terms & name_terms) / max(len(query_terms), 1)
    ratio = SequenceMatcher(None, query_norm, name_norm).ratio()
    return max(ratio, overlap)


def _score_candidate(candidate, query):

    score = int(candidate.get("score") or 0)
    reasons = [_safe_text(candidate.get("match_reason"))]
    query_tickers = set(_ticker_tokens(query))
    ticker = _safe_text(candidate.get("ticker")).upper()
    source = _norm(candidate.get("source"))

    if ticker and ticker in query_tickers:
        score += 35
        reasons.append("exact ticker match")
    if "holding" in source:
        score += 30
        reasons.append("current holding match")
    if "watchlist" in source:
        score += 22
        reasons.append("watchlist match")
    if "security_master" in source:
        score += 18
        reasons.append("security master match")
    if "alias" in source:
        score += 36
        reasons.append("alias table match")
    if "historical" in source:
        score += 35
        reasons.append("historical ticker table match")
    if "live" in source:
        score += 30
        reasons.append("live research candidate")
    if "news" in source:
        score += 20
        reasons.append("recent-news candidate")

    name_similarity = _similarity(query, candidate.get("name"), ticker)
    if _norm(query) and _norm(query) in _norm(candidate.get("name")):
        score += 15
        reasons.append("query text appears in security name")
    if name_similarity >= 0.85:
        score += 22
        reasons.append("strong name similarity")
    elif name_similarity >= 0.55:
        score += 12
        reasons.append("name similarity")

    context_delta, context_reasons = _context_bonus(candidate, query)
    score += context_delta
    reasons.extend(context_reasons)
    fresh_delta, fresh_reasons = _freshness_score(candidate)
    score += fresh_delta
    reasons.extend(fresh_reasons)

    candidate = dict(candidate)
    candidate["score"] = max(score, 0)
    candidate["match_reason"] = "; ".join(
        item for item in dict.fromkeys(reasons) if item
    )
    if candidate["score"] >= 80:
        candidate["confidence"] = "HIGH"
    elif candidate["score"] >= 50:
        candidate["confidence"] = "MEDIUM"
    else:
        candidate["confidence"] = "LOW"
    return candidate


def _add_candidate(candidates, candidate):

    key = _candidate_key(candidate)
    for index, existing in enumerate(candidates):
        if _candidate_key(existing) == key:
            if int(candidate.get("score") or 0) > int(existing.get("score") or 0):
                candidates[index] = candidate
            return
    candidates.append(candidate)


def _candidate_from_record(record, source, reason, score=0):

    name = _safe_text(record.get("name") or record.get("security_name"))
    category = _safe_text(record.get("category"))
    return _candidate(
        record.get("ticker"),
        name,
        _security_type(name, category),
        source,
        "MEDIUM",
        reason,
        score,
        category=category
    )


def _local_candidates(query, security_master_path=None, holdings_path=None,
                      watchlist_path=None):

    query_norm = _norm(query)
    query_tickers = set(_ticker_tokens(query))
    candidates = []
    source_layers = (
        ("current_holding", load_current_holdings(holdings_path or DEFAULT_HOLDINGS_PATH)),
        ("watchlist", load_watchlist(watchlist_path or DEFAULT_WATCHLIST_PATH)),
        ("security_master", load_security_master(security_master_path or DEFAULT_SECURITY_MASTER_PATH))
    )
    for source, records in source_layers:
        for record in records:
            ticker = _safe_text(record.get("ticker")).upper()
            name = _safe_text(record.get("name") or record.get("security_name"))
            category = _safe_text(record.get("category"))
            if ticker and ticker in query_tickers:
                _add_candidate(
                    candidates,
                    _candidate_from_record(record, source, "exact ticker candidate", 20)
                )
                continue
            similarity = _similarity(query, name, ticker)
            if query_norm and similarity >= 0.55:
                base_score = 35 if query_norm in _norm(name) else int(similarity * 20)
                _add_candidate(
                    candidates,
                    _candidate_from_record(record, source, "name similarity candidate", base_score)
                )
            elif any(term in _norm(f"{name} {category}") for term in _query_terms(query)):
                _add_candidate(
                    candidates,
                    _candidate_from_record(record, source, "name/category token candidate", 8)
                )
    return candidates


def _normal_candidate_records(value):

    if isinstance(value, dict):
        value = value.get("candidates") or value.get("profiles") or []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _external_candidates(query, value, source):

    candidates = []
    query_tickers = set(_ticker_tokens(query))
    terms = set(_query_terms(query))
    for item in _normal_candidate_records(value):
        ticker = _safe_text(item.get("ticker")).upper()
        name = _safe_text(item.get("name") or item.get("company_name"))
        reason = _safe_text(
            item.get("match_reason")
            or item.get("reason")
            or item.get("company_summary")
            or item.get("summary")
        )
        haystack = _norm(" ".join([
            ticker,
            name,
            reason,
            _safe_text(item.get("status")),
            _safe_text(item.get("security_type"))
        ]))
        if ticker in query_tickers or terms & set(re.findall(r"[a-z0-9.]+", haystack)):
            _add_candidate(
                candidates,
                _candidate(
                    ticker,
                    name,
                    item.get("security_type") or item.get("asset_type"),
                    source,
                    item.get("confidence") or "MEDIUM",
                    reason or f"{source} candidate",
                    item.get("score") or 0,
                    item.get("status") or item.get("listing_status"),
                    item.get("source_date") or item.get("as_of"),
                    item.get("category")
                )
            )
    return candidates


def _alias_candidates(query, alias_path=None):

    data = _read_json(alias_path or DEFAULT_ALIAS_PATH, {})
    query_norm = _norm(query)
    candidates = []
    if not isinstance(data, dict):
        return candidates
    for alias, records in data.items():
        alias_norm = _norm(alias)
        if not alias_norm:
            continue
        if alias_norm != query_norm and alias_norm not in query_norm:
            continue
        for item in _normal_candidate_records(records):
            _add_candidate(
                candidates,
                _candidate(
                    item.get("ticker"),
                    item.get("name"),
                    item.get("security_type"),
                    "alias_table",
                    item.get("confidence") or "HIGH",
                    f"alias '{alias}'",
                    item.get("score") or 45,
                    item.get("status"),
                    item.get("source_date"),
                    item.get("category")
                )
            )
    return candidates


def _historical_candidates(query, history_path=None):

    data = _read_json(history_path or DEFAULT_HISTORY_PATH, {})
    query_norm = _norm(query)
    query_tickers = set(_ticker_tokens(query))
    candidates = []
    records = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        item = dict(item)
                        item.setdefault("query", key)
                        records.append(item)
            elif isinstance(value, dict):
                value = dict(value)
                value.setdefault("query", key)
                records.append(value)
    for item in records:
        query_key = _safe_text(item.get("query")).upper()
        if query_key and query_key not in query_tickers and _norm(query_key) not in query_norm:
            continue
        ticker = item.get("current_ticker") or item.get("ticker")
        name = item.get("current_name") or item.get("name")
        reason = item.get("reason") or item.get("status") or "historical ticker match"
        _add_candidate(
            candidates,
            _candidate(
                ticker,
                name,
                item.get("security_type"),
                "historical_ticker_table",
                item.get("confidence") or "MEDIUM",
                reason,
                item.get("score") or 35,
                item.get("status"),
                item.get("source_date"),
                item.get("category")
            )
        )
    return candidates


def _rank_candidates(query, candidates):

    ranked = [_score_candidate(candidate, query) for candidate in candidates]
    return sorted(
        ranked,
        key=lambda item: (-int(item.get("score") or 0), item.get("ticker"), item.get("name"))
    )


def _ambiguous(ranked):

    if not ranked:
        return True
    top = ranked[0]
    if top.get("confidence") != "HIGH":
        return True
    if len(ranked) < 2:
        return False
    second = ranked[1]
    margin = int(top.get("score") or 0) - int(second.get("score") or 0)
    same_ticker_same_name = (
        top.get("ticker")
        and top.get("ticker") == second.get("ticker")
        and _norm(top.get("name")) == _norm(second.get("name"))
    )
    if same_ticker_same_name:
        return False
    same_ticker_different_name = (
        top.get("ticker")
        and top.get("ticker") == second.get("ticker")
        and _norm(top.get("name")) != _norm(second.get("name"))
    )
    if same_ticker_different_name:
        return margin < 45
    return margin < 25


def build_security_resolution(query, security_master_path=None,
                              holdings_path=None, watchlist_path=None,
                              alias_path=None, history_path=None,
                              live_candidates=None, news_candidates=None,
                              live_candidates_path=None,
                              news_candidates_path=None,
                              execution_tier=None):

    query = _safe_text(query)
    reasoning = []
    candidates = []
    execution_tier = execution_tier if isinstance(execution_tier, dict) else {}
    tier_name = str(execution_tier.get("execution_tier") or "").upper()
    explicit_current = any(
        term in query.casefold()
        for term in ("latest", "current", "live", "up to date")
    )

    for candidate in _local_candidates(
        query,
        security_master_path,
        holdings_path,
        watchlist_path
    ):
        _add_candidate(candidates, candidate)
    reasoning.append("Checked exact ticker, holdings, watchlist, and security master matches.")

    for candidate in _alias_candidates(query, alias_path):
        _add_candidate(candidates, candidate)
    reasoning.append("Checked configurable alias table.")

    for candidate in _historical_candidates(query, history_path):
        _add_candidate(candidates, candidate)
    reasoning.append("Checked configurable historical ticker table.")

    local_ranked = _rank_candidates(query, candidates)
    local_ambiguous = _ambiguous(local_ranked)
    external_allowed = (
        live_candidates is not None
        or news_candidates is not None
        or not local_ranked
        or local_ambiguous
        or explicit_current
        or tier_name == "DEEP_RESEARCH"
    )

    if external_allowed:
        if live_candidates is None:
            live_candidates = _read_json(live_candidates_path or DEFAULT_LIVE_CANDIDATES_PATH, {})
        for candidate in _external_candidates(query, live_candidates, "live_research_candidate"):
            _add_candidate(candidates, candidate)
        if live_research_enabled() or live_candidates:
            reasoning.append("Checked live research candidates for newer listings and IPO language.")
        else:
            reasoning.append("Live research candidate search unavailable; LIVE_RESEARCH_ENABLED is false.")

        if news_candidates is None:
            news_candidates = _read_json(news_candidates_path or DEFAULT_NEWS_CANDIDATES_PATH, {})
        for candidate in _external_candidates(query, news_candidates, "recent_news_candidate"):
            _add_candidate(candidates, candidate)
        reasoning.append("Checked recent-news candidates for current listing evidence.")
    else:
        reasoning.append("Skipped live/news candidate search because local resolution was sufficient.")

    ranked = _rank_candidates(query, candidates)
    ambiguity_detected = _ambiguous(ranked)
    selected = {} if ambiguity_detected else ranked[0]
    resolved = bool(selected)
    confidence = selected.get("confidence") if selected else ("LOW" if not ranked else ranked[0].get("confidence"))

    if ambiguity_detected and ranked:
        reasoning.append(
            f"I found multiple possible matches for {query}. I need to resolve the security before researching it."
        )
    elif not ranked:
        reasoning.append(f"No reliable security candidates were found for {query}.")
    else:
        reasoning.append(
            f"Selected {selected.get('ticker')} because {selected.get('match_reason')}."
        )

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "resolved": resolved,
        "confidence": confidence or "LOW",
        "selected_security": selected,
        "candidates": ranked,
        "ambiguity_detected": bool(ambiguity_detected),
        "reasoning": reasoning
    }


def resolve_many(query, **kwargs):

    return [
        build_security_resolution(mention, **kwargs)
        for mention in extract_security_mentions(query)
    ]


def render_security_resolution_text(resolution):

    lines = [
        "SECURITY RESOLUTION",
        "",
        f"Generated At: {resolution.get('generated_at')}",
        f"Query: {resolution.get('query')}",
        f"Resolved: {resolution.get('resolved')}",
        f"Confidence: {resolution.get('confidence')}",
        f"Ambiguity Detected: {resolution.get('ambiguity_detected')}",
        ""
    ]
    selected = resolution.get("selected_security") or {}
    if selected:
        lines.extend([
            "Selected Security:",
            (
                f"- {selected.get('ticker')} | {selected.get('name')} | "
                f"{selected.get('security_type')} | {selected.get('source')} | "
                f"{selected.get('confidence')}"
            ),
            f"  Reason: {selected.get('match_reason')}",
            ""
        ])
    lines.append("Candidates:")
    for item in resolution.get("candidates") or []:
        lines.append(
            f"- {item.get('ticker')} | {item.get('name')} | {item.get('security_type')} | "
            f"{item.get('source')} | {item.get('confidence')} | score {item.get('score')} | "
            f"{item.get('match_reason')}"
        )
    if not resolution.get("candidates"):
        lines.append("None")
    lines.extend(["", "Reasoning:"])
    lines.extend([f"- {item}" for item in resolution.get("reasoning") or []] or ["None"])
    return "\n".join(lines) + "\n"


def write_security_resolution_json(resolution, path=None):

    return _write_json(resolution, path or SECURITY_RESOLUTION_JSON_PATH)


def write_security_resolution_text(resolution, path=None):

    return _write_text(
        render_security_resolution_text(resolution),
        path or SECURITY_RESOLUTION_TEXT_PATH
    )


def read_security_resolution(path=None):

    value = _read_json(path or SECURITY_RESOLUTION_JSON_PATH, {})
    return value if isinstance(value, dict) and value else build_security_resolution("")


def build_and_write_security_resolution(query):

    resolution = build_security_resolution(query)
    return {
        "security_resolution": resolution,
        "json_result": write_security_resolution_json(resolution),
        "text_result": write_security_resolution_text(resolution)
    }
