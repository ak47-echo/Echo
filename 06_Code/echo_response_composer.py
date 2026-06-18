from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
RESPONSE_COMPOSER_JSON_PATH = REPORTS_DIR / "echo_response_composer.json"
RESPONSE_COMPOSER_TEXT_PATH = REPORTS_DIR / "echo_response_composer.txt"

RAW_TOOL_NAMES = (
    "echo_get_context_budget",
    "echo_get_agent_routing",
    "echo_get_memory_context",
    "echo_get_context_assembly",
    "echo_get_change_detection",
    "echo_get_state_delta",
    "echo_get_state_history",
    "echo_get_portfolio_change_detection",
    "echo_search_security_master",
    "echo_get_market_opportunity_scan",
    "echo_get_portfolio_auto_import"
)

def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _dict(value):

    return value if isinstance(value, dict) else {}


def _list(value):

    return value if isinstance(value, list) else []


def _tokens(text):

    return set(re.findall(r"[a-z0-9]+", _safe_text(text).casefold()))


def _has_any(text, terms):

    lowered = _safe_text(text).casefold()
    tokens = _tokens(text)

    for term in terms:
        term = str(term).casefold()

        if " " in term and term in lowered:
            return True

        if " " not in term and term in tokens:
            return True

    return False


def _title(value):

    if isinstance(value, dict):
        for key in (
            "title",
            "label",
            "name",
            "theme_title",
            "action",
            "representative_headline",
            "top_priority"
        ):
            text = _safe_text(value.get(key))
            if text:
                return text

    return _safe_text(value)


def _metadata(item):

    return _dict(_dict(item).get("metadata"))


def _item_reason(item):

    item = _dict(item)
    metadata = _metadata(item)

    for source in (item, metadata):
        for key in ("reason", "description", "theme_reason"):
            text = _safe_text(source.get(key))
            if text:
                return text

    return ""


def _first_label(items):

    for item in _list(items):
        label = _title(item)
        if label:
            return label

    return ""


def _top_labels(items, limit=3):

    labels = []

    for item in _list(items):
        label = _title(item)

        if label and label not in labels:
            labels.append(label)

        if len(labels) >= limit:
            break

    return labels


def _join_labels(labels):

    labels = [label for label in labels if label]

    if not labels:
        return "None identified."

    if len(labels) == 1:
        return labels[0]

    return "; ".join(labels)


def _debug_summary(context_budget, agent_routing, context_assembly):

    assembly_summary = _dict(_dict(context_assembly).get("context_summary"))

    return {
        "query_class": _dict(context_budget).get("query_class"),
        "budget_level": _dict(context_budget).get("budget_level"),
        "routing_mode": _dict(agent_routing).get("routing_mode"),
        "assembly_mode": _dict(context_assembly).get("assembly_mode"),
        "full_reports_included": bool(
            assembly_summary.get("full_reports_included")
        )
    }


def _current_state(memory_context):

    return _dict(_dict(memory_context).get("operating_context")).get(
        "current_state",
        {}
    )


def _operating(memory_context):

    return _dict(_dict(memory_context).get("operating_context"))


def _summary(memory_context):

    return _dict(_dict(memory_context).get("summary"))


def _block_sources(context_assembly):

    sources = []

    for block in _list(_dict(context_assembly).get("context_blocks")):
        source = _safe_text(_dict(block).get("source"))

        if source and source not in sources:
            sources.append(source)

    return sources


def _block_texts(context_assembly, source):

    texts = []

    for block in _list(_dict(context_assembly).get("context_blocks")):
        block = _dict(block)

        if block.get("source") == source:
            text = _safe_text(block.get("content"))
            if text:
                texts.append(text)

    return texts


def _block_json(context_assembly, source):

    for text in _block_texts(context_assembly, source):
        try:
            value = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

        if isinstance(value, dict):
            return value

    return {}


def _clean_answer(answer):

    clean = _safe_text(answer)

    for tool_name in RAW_TOOL_NAMES:
        clean = clean.replace(tool_name, "internal context")

    return clean


def _intent(user_query, context_budget, agent_routing):

    query = _safe_text(user_query)
    query_class = _dict(context_budget).get("query_class")
    routing_mode = _dict(agent_routing).get("routing_mode")
    primary_agents = _list(_dict(agent_routing).get("primary_agents"))

    if query_class == "conversational":
        return "conversational"

    if query_class in {
        "portfolio_movement",
        "holding_news",
        "ticker_question",
        "ticker_news",
        "market_opportunities",
        "market_risks",
        "watchlist_management",
        "security_master_search",
        "paper_allocation_future"
    }:
        return query_class

    if query_class == "portfolio_change" or _has_any(query, (
        "what changed in my portfolio",
        "portfolio changed",
        "portfolio changes",
        "new positions",
        "new position",
        "removed positions",
        "removed position",
        "what did i buy",
        "what did i sell",
        "changed from last report",
        "changes from last report",
        "since last report",
        "from last report",
        "concentration change",
        "concentration changed",
        "did my concentration change",
        "did cash change",
        "cash change",
        "cash changed"
    )):
        return "portfolio_change_status"

    if _has_any(query, (
        "changed",
        "change",
        "new",
        "moved",
        "different",
        "shifted",
        "since",
        "material"
    )):
        return "change_status"

    if _has_any(query, (
        "persistent",
        "persisted",
        "recurring",
        "repeated",
        "ongoing",
        "longest",
        "keeps",
        "stable"
    )):
        return "persistence_status"

    if _has_any(query, (
        "attention",
        "focus",
        "urgent",
        "watch",
        "action",
        "done",
        "next",
        "care"
    )):
        return "attention_status"

    if _has_any(query, (
        "top priority",
        "main priority",
        "current priority",
        "biggest issue",
        "biggest problem",
        "highest concern",
        "primary risk",
        "matters most",
        "most important"
    )):
        return "priority_status"

    if _has_any(query, (
        "risky",
        "risk",
        "exposed",
        "exposure",
        "driving",
        "why",
        "affect",
        "impact"
    )):
        if len(primary_agents) > 1 or routing_mode == "all_agents":
            return "cross_agent_synthesis"
        return "risk_explanation"

    if _has_any(query, (
        "overall",
        "executive summary",
        "full summary",
        "big picture",
        "synthesis",
        "connect",
        "everything",
        "cross-agent",
        "cross agent",
        "diagnosis"
    )) or query_class == "multi_agent":
        return "cross_agent_synthesis"

    if len(primary_agents) == 1:
        return "agent_summary"

    if query_class == "memory":
        return "attention_status"

    return "fallback_general"


def _response_mode(intent, agent_routing):

    routing_mode = _dict(agent_routing).get("routing_mode")

    if intent == "conversational":
        return "conversational"

    if intent in {
        "priority_status",
        "change_status",
        "portfolio_change_status",
        "portfolio_movement",
        "holding_news",
        "ticker_question",
        "ticker_news",
        "market_opportunities",
        "market_risks",
        "watchlist_management",
        "security_master_search",
        "paper_allocation_future",
        "persistence_status",
        "attention_status"
    }:
        return "memory"

    if intent in {"cross_agent_synthesis"} or routing_mode == "all_agents":
        return "multi_agent_summary"

    if intent in {"agent_summary", "risk_explanation"}:
        return "agent_summary"

    return "fallback"


def _conversational_response(user_query):

    query = _safe_text(user_query).casefold().strip(" ?!.")

    if query in {"hi", "hello", "hey", "good morning", "good afternoon",
                 "good evening", "what's up", "whats up"}:
        return (
            "I'm here. Ask me what changed, what matters, or which area you "
            "want to inspect.",
            [],
            []
        )

    if query in {"thanks", "thank you"}:
        return "You're welcome.", [], []

    if "joke" in query or "funny" in query:
        return (
            "Portfolio managers do not panic; they just rebalance their "
            "facial expressions.",
            [],
            []
        )

    return (
        "I'm here. Ask me naturally, and I will use Echo context when it is "
        "relevant.",
        [],
        []
    )


def _priority_response(memory_context):

    summary = _summary(memory_context)
    current = _dict(_current_state(memory_context))
    operating = _operating(memory_context)
    top_priority = (
        _safe_text(summary.get("top_priority"))
        or _title(current.get("top_priority"))
    )
    top_priority_data = _dict(current.get("top_priority"))
    reason = (
        _safe_text(top_priority_data.get("reason"))
        or _item_reason(top_priority_data)
    )
    persistent = _top_labels(operating.get("persistent_patterns"), 1)
    secondary = (
        _safe_text(summary.get("top_signal"))
        or _first_label(operating.get("top_signals"))
    )

    if not top_priority:
        return (
            "I do not have a current top priority in the compact memory "
            "context.",
            [],
            ["Run Echo again if this should be populated."]
        )

    persistence_note = (
        f"It appears persistent because {_join_labels(persistent)} is still "
        "showing up."
        if persistent
        else "I do not see a persistence marker attached to it."
    )
    secondary_note = f"Secondary signal: {secondary}." if secondary else ""
    answer = (
        f"Your current top priority is {top_priority}. "
        f"{persistence_note} {secondary_note}"
    )
    points = [point for point in (reason, secondary) if point]

    return answer, points, []


def _change_response(memory_context):

    summary = _summary(memory_context)
    operating = _operating(memory_context)
    changes = _list(operating.get("important_changes"))
    material_count = int(summary.get("material_change_count") or len(changes))
    change_level = _safe_text(summary.get("change_level"))

    if not changes and material_count == 0:
        answer = "No material changes were detected in the compact memory layer."
        points = []

        if change_level:
            points.append(f"Change level: {change_level}.")

        return answer, points, []

    labels = _top_labels(changes, 4)
    top_signal = _safe_text(summary.get("top_signal"))
    answer = (
        f"Echo detected {material_count or len(labels)} material change(s). "
        f"Most relevant: {_join_labels(labels)}."
    )

    if top_signal:
        answer = f"{answer} Top signal: {top_signal}."

    return answer, labels, []


def _change_label(change):

    account = _safe_text(change.get("account"))
    ticker = _safe_text(change.get("ticker"))

    if account and ticker:
        return f"{account} {ticker}"

    return ticker or account or _safe_text(change)


def _portfolio_change_response(user_query, context_assembly):

    report = _block_json(context_assembly, "portfolio_change_detection")

    if not report:
        return (
            "I do not have a portfolio change detection report available.",
            [],
            ["Run Echo after importing a portfolio CSV to populate this report."]
        )

    query = _safe_text(user_query).casefold()
    summary = _dict(report.get("summary"))
    material_count = int(summary.get("material_change_count") or 0)
    change_count = int(summary.get("change_count") or 0)
    total_delta = float(summary.get("total_market_value_change") or 0)
    new_positions = _list(report.get("new_positions"))
    removed_positions = _list(report.get("removed_positions"))
    quantity_changes = _list(report.get("quantity_changes"))
    value_changes = _list(report.get("market_value_changes"))
    concentration_changes = _list(report.get("concentration_changes"))
    cash_changes = _list(report.get("cash_changes"))

    if "new position" in query or "what did i buy" in query:
        labels = [_change_label(change) for change in new_positions]
        label_text = _join_labels(labels).rstrip(".")
        answer = (
            f"New positions since the previous normalized snapshot: "
            f"{label_text}."
        )
        return answer, labels, []

    if "removed position" in query or "what did i sell" in query:
        labels = [_change_label(change) for change in removed_positions]
        label_text = _join_labels(labels).rstrip(".")
        answer = (
            f"Removed positions since the previous normalized snapshot: "
            f"{label_text}."
        )
        return answer, labels, []

    if "cash" in query:
        labels = [
            (
                f"{_change_label(change)} cash "
                f"{float(change.get('delta_cash') or 0):+.2f}"
            )
            for change in cash_changes
        ]
        answer = f"Cash changes: {_join_labels(labels).rstrip('.')}."
        return answer, labels, []

    if "concentration" in query:
        labels = [
            (
                f"{_change_label(change)} weight "
                f"{float(change.get('delta_weight') or 0):+.2f} pts"
            )
            for change in concentration_changes[:5]
        ]
        answer = f"Concentration changes: {_join_labels(labels).rstrip('.')}."
        return answer, labels, []

    top_change = _dict(summary.get("top_change"))
    labels = []

    for group in (
        new_positions,
        removed_positions,
        quantity_changes,
        value_changes,
        concentration_changes,
        cash_changes
    ):
        for change in group:
            label = _change_label(change)
            if label and label not in labels:
                labels.append(label)
            if len(labels) >= 5:
                break
        if len(labels) >= 5:
            break

    if change_count == 0:
        answer = (
            "No holdings-level portfolio changes were detected between the "
            "current normalized holdings and the previous normalized snapshot."
        )
    else:
        top_label = _change_label(top_change) if top_change else "None"
        answer = (
            f"Portfolio change detection found {change_count} holdings-level "
            f"change(s), including {material_count} material change(s). "
            f"Total market value changed ${total_delta:+.2f}. "
            f"Top change: {top_label}."
        )

    return answer, labels, []


def _format_money(value):

    return f"${float(value or 0):,.2f}"


def _format_weight(value):

    return f"{float(value or 0):.2f}%"


def _position_detail(change, current=True):

    account = _safe_text(change.get("account"))
    ticker = _safe_text(change.get("ticker"))
    quantity_key = "current_quantity" if current else "previous_quantity"
    value_key = "current_market_value" if current else "previous_market_value"
    quantity = change.get(quantity_key, change.get("quantity"))
    market_value = change.get(value_key, change.get("market_value"))
    return (
        f"{account} {ticker} | qty {float(quantity or 0):g} | "
        f"value {_format_money(market_value)}"
    )


def _portfolio_movement_response(context_assembly):

    report = _block_json(context_assembly, "portfolio_change_detection")
    if not report:
        return (
            "I do not have portfolio movement data yet.",
            [],
            ["Run Echo after importing holdings to populate movement attribution."]
        )

    summary = _dict(report.get("summary"))
    quantity_changes = _list(report.get("quantity_changes"))
    value_changes = _list(report.get("market_value_changes"))
    concentration_changes = _list(report.get("concentration_changes"))
    cash_changes = _list(report.get("cash_changes"))
    total_delta = float(summary.get("total_market_value_change") or 0)
    driver = (
        "holdings changes and market value changes"
        if quantity_changes else
        "market value and concentration changes, not buys or sells"
    )
    movers = sorted(
        value_changes,
        key=lambda item: abs(float(item.get("delta_market_value") or 0)),
        reverse=True
    )[:5]
    labels = [
        (
            f"{_change_label(item)} value "
            f"{float(item.get('delta_market_value') or 0):+.2f}"
        )
        for item in movers
    ]
    concentration = [
        (
            f"{_change_label(item)} weight "
            f"{float(item.get('delta_weight') or 0):+.2f} pts"
        )
        for item in concentration_changes[:3]
    ]
    cash = [
        (
            f"{_change_label(item)} cash "
            f"{float(item.get('delta_cash') or 0):+.2f}"
        )
        for item in cash_changes[:3]
    ]
    answer = (
        f"Portfolio value changed {_format_money(total_delta)}. "
        f"The movement was driven by {driver}. "
        f"Largest value movers: {_join_labels(labels).rstrip('.')}. "
        f"Concentration movers: {_join_labels(concentration).rstrip('.')}. "
        f"Cash movement: {_join_labels(cash).rstrip('.')}."
    )
    return answer, labels + concentration + cash, []


def _enhanced_portfolio_change_response(user_query, context_assembly):

    report = _block_json(context_assembly, "portfolio_change_detection")
    if not report:
        return _portfolio_change_response(user_query, context_assembly)

    query = _safe_text(user_query).casefold()
    new_positions = _list(report.get("new_positions"))
    removed_positions = _list(report.get("removed_positions"))
    quantity_changes = _list(report.get("quantity_changes"))
    value_changes = _list(report.get("market_value_changes"))
    concentration_changes = _list(report.get("concentration_changes"))
    cash_changes = _list(report.get("cash_changes"))

    if "new position" in query:
        labels = [_position_detail(item, True) for item in new_positions]
        return (
            f"New positions: {_join_labels(labels).rstrip('.')}.",
            labels,
            []
        )

    if "removed position" in query or "what did i sell" in query:
        labels = [_position_detail(item, False) for item in removed_positions]
        return (
            f"Removed positions: {_join_labels(labels).rstrip('.')}.",
            labels,
            []
        )

    if "concentration" in query:
        labels = [
            (
                f"{_change_label(item)} "
                f"{_format_weight(item.get('previous_weight'))} -> "
                f"{_format_weight(item.get('current_weight'))} "
                f"({float(item.get('delta_weight') or 0):+.2f} pts)"
            )
            for item in concentration_changes[:6]
        ]
        return f"Concentration changes: {_join_labels(labels).rstrip('.')}.", labels, []

    if "cash" in query:
        labels = [
            f"{_change_label(item)} {float(item.get('delta_cash') or 0):+.2f}"
            for item in cash_changes
        ]
        return f"Cash changes: {_join_labels(labels).rstrip('.')}.", labels, []

    if not new_positions and not removed_positions and not quantity_changes:
        if value_changes or concentration_changes or cash_changes:
            answer = (
                "No new positions, removed positions, or quantity changes "
                "were detected. The movement came from market value, "
                "concentration, or cash changes."
            )
        else:
            answer = (
                "No new positions, removed positions, quantity changes, "
                "market value changes, concentration changes, or cash changes "
                "were detected."
            )
        labels = [
            f"{_change_label(item)} value {float(item.get('delta_market_value') or 0):+.2f}"
            for item in value_changes[:3]
        ]
        labels.extend(
            f"{_change_label(item)} weight {float(item.get('delta_weight') or 0):+.2f} pts"
            for item in concentration_changes[:3]
        )
        return answer, labels, []

    labels = []
    labels.extend(f"New: {_position_detail(item, True)}" for item in new_positions[:4])
    labels.extend(f"Removed: {_position_detail(item, False)}" for item in removed_positions[:4])
    for item in quantity_changes[:4]:
        delta = float(item.get("delta_quantity") or 0)
        direction = "buy" if delta > 0 else "sell"
        labels.append(f"{direction}: {_change_label(item)} qty {delta:+g}")
    answer = (
        "Transaction and holding changes: "
        f"{_join_labels(labels).rstrip('.')}. "
        "Market value, concentration, and cash changes are tracked separately."
    )
    return answer, labels, []


def _security_master_response(user_query, context_assembly):

    result = _block_json(context_assembly, "security_master_search")
    matches = _list(result.get("matches"))
    if not matches:
        warning = _join_labels(result.get("warnings") or [])
        return (
            f"Echo does not have enough local security master data for that security. {warning}",
            [],
            []
        )
    labels = [
        (
            f"{item.get('ticker')} | {item.get('name')} | "
            f"{item.get('category') or 'uncategorized'} | "
            f"expense ratio {item.get('expense_ratio')}"
        )
        for item in matches[:8]
    ]
    answer = (
        f"Security master matches for '{_safe_text(user_query)}': "
        f"{_join_labels(labels).rstrip('.')}."
    )
    return answer, labels, []


def _ticker_response(user_query, context_assembly):

    result = _block_json(context_assembly, "security_master_search")
    matches = _list(result.get("matches"))
    if not matches:
        return (
            "I do not have enough local data for that ticker yet. "
            "It can be added as a research or watchlist candidate before I "
            "make a stronger local assessment.",
            [],
            []
        )
    first = matches[0]
    reason = _safe_text(first.get("match_reason"))
    relation = "currently held" if "holding" in reason else "not currently held"
    if "watchlist" in reason and "holding" not in reason:
        relation = "on the watchlist but not currently held"
    answer = (
        f"{first.get('ticker')} is {relation} in Echo's local data. "
        f"Local reference: {first.get('name')} | "
        f"{first.get('category') or 'uncategorized'}"
    )
    if first.get("expense_ratio") is not None:
        answer = f"{answer} | expense ratio {first.get('expense_ratio')}."
    else:
        answer = f"{answer}."
    answer = (
        f"{answer} I do not have verified current company-specific news unless "
        "it appears in the local News Agent output."
    )
    return answer, [json.dumps(item, sort_keys=True) for item in matches[:5]], []


def _market_scan_response(query_class, context_assembly):

    scan = _block_json(context_assembly, "market_opportunity_scan")
    if not scan:
        return (
            "I do not have a market opportunity scan available yet.",
            [],
            ["Run Echo to generate the local opportunity and risk scan."]
        )
    key = (
        "risk_candidates"
        if query_class == "market_risks" else "opportunity_candidates"
    )
    label = "Risk candidates" if key == "risk_candidates" else "Research candidates"
    candidates = _list(scan.get(key))
    labels = [
        (
            f"{item.get('ticker') or 'UNKNOWN'} | {item.get('direction')} | "
            f"{item.get('reason')}"
        )
        for item in candidates[:6]
    ]
    if not labels:
        labels = scan.get("warnings") or []
    answer = (
        f"{label}: {_join_labels(labels).rstrip('.')}. "
        "These are research candidates only; no trades are being placed."
    )
    return answer, labels, []


def _holding_news_response(memory_context, context_assembly):

    current = _dict(_current_state(memory_context))
    news = _title(current.get("news_top_narrative"))
    macro = _title(current.get("macro_regime"))
    theme = _title(current.get("dominant_theme"))
    portfolio_texts = _block_texts(context_assembly, "portfolio_report")
    affected = []
    for ticker in ("UNH", "SMCI", "IBIT", "VNOM", "ECO", "MSTR", "SCHG"):
        blob = " ".join(portfolio_texts + [news, macro, theme]).casefold()
        if ticker.casefold() in blob:
            affected.append(ticker)
    if not affected:
        affected = ["current holdings"]
    answer = (
        f"Current local news/macro context points to {news or 'no direct local news narrative'} "
        f"and {macro or 'no macro regime in memory'}. "
        f"Holdings most exposed from local context: {_join_labels(affected)}. "
        "No direct company-specific news is assumed unless it appears in the local News Agent output."
    )
    return answer, [point for point in (news, macro, theme) if point], []


def _paper_allocation_response():

    return (
        "Paper allocation is a future Echo mode. No real trades will be "
        "placed. Before Echo can simulate allocating capital responsibly, it "
        "needs stronger watchlist coverage, research scoring, paper-tracking, "
        "and performance audit loops. In this phase I can only surface "
        "research candidates.",
        [],
        []
    )


def _persistence_response(memory_context):

    summary = _summary(memory_context)
    operating = _operating(memory_context)
    persistent = _list(operating.get("persistent_patterns"))
    labels = _top_labels(persistent, 4)
    count = int(summary.get("persistent_issue_count") or len(persistent))
    most_common = _safe_text(summary.get("most_common_priority"))

    if not labels and not most_common:
        return (
            "I do not see persistent issues in the compact memory context.",
            [],
            ["Persistence depends on available state history snapshots."]
        )

    anchor = most_common or labels[0]
    answer = (
        f"The most persistent issue is {anchor}. "
        f"Echo currently tracks {count} persistent issue(s). "
        f"Other recurring items: {_join_labels(labels[1:])}."
    )

    return answer, labels, []


def _attention_response(memory_context):

    summary = _summary(memory_context)
    operating = _operating(memory_context)
    attention = _list(operating.get("recommended_attention"))
    labels = _top_labels(attention, 4)
    top_priority = _safe_text(summary.get("top_priority"))
    top_signal = _safe_text(summary.get("top_signal"))

    if not labels and not top_priority:
        return (
            "I do not have a recommended-attention list in memory yet.",
            [],
            ["Run Echo again if the attention layer should be populated."]
        )

    answer = (
        f"Focus first on {top_priority or labels[0]}. "
        f"Watch next: {_join_labels(labels)}."
    )

    if top_signal:
        answer = f"{answer} Current top signal: {top_signal}."

    return answer, labels, []


def _portfolio_response(memory_context, context_assembly):

    current = _dict(_current_state(memory_context))
    risk = _title(current.get("portfolio_current_risk"))
    scenario = _title(current.get("portfolio_worst_stress_scenario"))
    top_priority = _title(current.get("top_priority"))
    points = [point for point in (risk, scenario, top_priority) if point]

    if not points:
        points = _block_texts(context_assembly, "portfolio_report")[:1]

    if not points:
        return (
            "I do not have enough portfolio context to summarize the current risk.",
            [],
            ["Portfolio summary requires memory context or a routed portfolio block."]
        )

    answer = (
        f"Portfolio read: the main risk is {risk or top_priority}. "
        f"Worst stress scenario: {scenario or 'not identified in memory'}."
    )

    return answer, points[:4], []


def _macro_response(memory_context):

    current = _dict(_current_state(memory_context))
    regime = _dict(current.get("macro_regime"))
    name = _safe_text(regime.get("name")) or _title(regime)
    reason = _safe_text(regime.get("reason"))
    top_priority = _safe_text(regime.get("top_priority"))
    points = [point for point in (reason, top_priority) if point]

    if not name:
        return (
            "I do not have a current macro regime in memory.",
            [],
            ["Macro summary requires the macro state artifact."]
        )

    answer = f"Macro read: the current regime is {name}."

    if reason:
        answer = f"{answer} Main driver: {reason}"

    return answer, points, []


def _news_response(memory_context):

    current = _dict(_current_state(memory_context))
    narrative = _dict(current.get("news_top_narrative"))
    title = _safe_text(narrative.get("title")) or _title(narrative)
    reason = _safe_text(narrative.get("reason"))
    headline = _safe_text(narrative.get("representative_headline"))
    points = [point for point in (reason, headline) if point]

    if not title:
        return (
            "I do not have a current news narrative in memory.",
            [],
            ["News summary requires the news state artifact."]
        )

    answer = f"News read: the top narrative is {title}."

    if reason:
        answer = f"{answer} {reason}"

    return answer, points, []


def _research_response(memory_context, context_assembly):

    operating = _operating(memory_context)
    research_like = [
        label
        for label in _top_labels(operating.get("recommended_attention"), 6)
        if any(term in label.casefold() for term in (
            "conviction",
            "coverage",
            "research",
            "watchlist",
            "thesis",
            "reevaluate"
        ))
    ]

    if not research_like:
        research_like = _block_texts(context_assembly, "research_report")[:1]

    if not research_like:
        return (
            "I do not have a structured research summary in the selected context.",
            [],
            ["Research summary requires research memory or a routed research block."]
        )

    answer = (
        "Research read: the main research items are "
        f"{_join_labels(research_like[:3])}."
    )

    return answer, research_like[:4], []


def _cross_agent_response(memory_context):

    summary = _summary(memory_context)
    current = _dict(_current_state(memory_context))
    operating = _operating(memory_context)
    priority = _safe_text(summary.get("top_priority")) or _title(
        current.get("top_priority")
    )
    change_level = _safe_text(summary.get("change_level"))
    top_signal = _safe_text(summary.get("top_signal"))
    theme = _safe_text(summary.get("dominant_theme")) or _title(
        current.get("dominant_theme")
    )
    macro = _title(current.get("macro_regime"))
    news = _title(current.get("news_top_narrative"))
    portfolio = _title(current.get("portfolio_current_risk"))
    attention = _top_labels(operating.get("recommended_attention"), 3)

    if not any((priority, theme, macro, news, portfolio, top_signal)):
        return (
            "I do not have enough assembled context for a cross-agent summary.",
            [],
            ["Run Echo again if memory, routing, and assembly should be populated."]
        )

    answer = (
        f"Overall picture: start with {priority or top_signal}. "
        f"Change level is {change_level or 'not specified'}; dominant theme is "
        f"{theme or 'not specified'}. Portfolio: {portfolio or 'not specified'}. "
        f"Macro: {macro or 'not specified'}. News: {news or 'not specified'}. "
        f"Watch next: {_join_labels(attention)}."
    )
    points = [
        point for point in (priority, top_signal, theme, portfolio, macro, news)
        if point
    ]

    return answer, points, []


def _risk_response(user_query, memory_context, agent_routing):

    primary_agents = _list(_dict(agent_routing).get("primary_agents"))
    asks_macro = _has_any(user_query, (
        "macro",
        "inflation",
        "rates",
        "rate",
        "fed",
        "regime",
        "economy",
        "recession"
    ))
    asks_portfolio = _has_any(user_query, (
        "portfolio",
        "holding",
        "holdings",
        "allocation",
        "position",
        "exposed",
        "exposure"
    ))

    if asks_macro and asks_portfolio:
        return _cross_agent_response(memory_context)

    if asks_macro:
        return _macro_response(memory_context)

    if primary_agents == ["portfolio"]:
        return _portfolio_response(memory_context, {})

    if primary_agents == ["macro"]:
        return _macro_response(memory_context)

    return _cross_agent_response(memory_context)


def _agent_response(agent, memory_context, context_assembly):

    if agent == "portfolio":
        return _portfolio_response(memory_context, context_assembly)

    if agent == "macro":
        return _macro_response(memory_context)

    if agent == "news":
        return _news_response(memory_context)

    if agent == "research":
        return _research_response(memory_context, context_assembly)

    return _cross_agent_response(memory_context)


def compose_echo_response(user_query, context_budget, agent_routing,
                          context_assembly, memory_context=None):

    query = _safe_text(user_query)
    context_budget = _dict(context_budget)
    agent_routing = _dict(agent_routing)
    context_assembly = _dict(context_assembly)
    memory_context = _dict(memory_context)
    intent = _intent(query, context_budget, agent_routing)
    response_mode = _response_mode(intent, agent_routing)
    primary_agents = _list(agent_routing.get("primary_agents"))
    answer = ""
    supporting_points = []
    caveats = []

    if intent == "priority_status":
        answer, supporting_points, caveats = _priority_response(memory_context)
    elif intent == "conversational":
        answer, supporting_points, caveats = _conversational_response(query)
    elif intent == "change_status":
        answer, supporting_points, caveats = _change_response(memory_context)
    elif intent == "portfolio_change_status":
        answer, supporting_points, caveats = _enhanced_portfolio_change_response(
            query,
            context_assembly
        )
    elif intent == "portfolio_movement":
        answer, supporting_points, caveats = _portfolio_movement_response(
            context_assembly
        )
    elif intent == "holding_news":
        answer, supporting_points, caveats = _holding_news_response(
            memory_context,
            context_assembly
        )
    elif intent in {"ticker_question", "ticker_news"}:
        answer, supporting_points, caveats = _ticker_response(
            query,
            context_assembly
        )
    elif intent == "security_master_search":
        answer, supporting_points, caveats = _security_master_response(
            query,
            context_assembly
        )
    elif intent in {"market_opportunities", "market_risks"}:
        answer, supporting_points, caveats = _market_scan_response(
            intent,
            context_assembly
        )
    elif intent == "watchlist_management":
        answer, supporting_points, caveats = _market_scan_response(
            "market_opportunities",
            context_assembly
        )
    elif intent == "paper_allocation_future":
        answer, supporting_points, caveats = _paper_allocation_response()
    elif intent == "persistence_status":
        answer, supporting_points, caveats = _persistence_response(
            memory_context
        )
    elif intent == "attention_status":
        answer, supporting_points, caveats = _attention_response(memory_context)
    elif intent == "cross_agent_synthesis":
        answer, supporting_points, caveats = _cross_agent_response(
            memory_context
        )
    elif intent == "risk_explanation":
        answer, supporting_points, caveats = _risk_response(
            query,
            memory_context,
            agent_routing
        )
    elif intent == "agent_summary" and primary_agents:
        answer, supporting_points, caveats = _agent_response(
            primary_agents[0],
            memory_context,
            context_assembly
        )
    else:
        answer = (
            "I'm here. Ask me what changed, what matters, or which area you "
            "want to inspect."
        )
        response_mode = "fallback"
        caveats = []

    answer = _clean_answer(answer)
    supporting_points = [
        _clean_answer(point)
        for point in supporting_points
        if _safe_text(point)
    ][:6]
    caveats = [_clean_answer(caveat) for caveat in caveats if _safe_text(caveat)]
    used_sources = _block_sources(context_assembly)

    if not used_sources and memory_context:
        used_sources = ["memory_context"]

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "response_mode": response_mode,
        "answer": answer,
        "supporting_points": supporting_points,
        "caveats": caveats,
        "used_sources": used_sources,
        "debug_summary": _debug_summary(
            context_budget,
            agent_routing,
            context_assembly
        )
    }


def render_response_composer_text(response_composer):

    composer = _dict(response_composer)
    debug = _dict(composer.get("debug_summary"))
    lines = [
        "ECHO RESPONSE COMPOSER",
        "======================",
        "",
        f"Schema Version: {composer.get('schema_version') or 'unknown'}",
        f"Generated At: {composer.get('generated_at') or 'unknown'}",
        f"Query: {composer.get('query') or ''}",
        f"Response Mode: {composer.get('response_mode') or 'fallback'}",
        "",
        "Answer:",
        composer.get("answer") or "",
        "",
        "Supporting Points:"
    ]
    lines.extend(
        [f"- {point}" for point in _list(composer.get("supporting_points"))]
        or ["None"]
    )
    lines.extend(["", "Caveats:"])
    lines.extend(
        [f"- {caveat}" for caveat in _list(composer.get("caveats"))]
        or ["None"]
    )
    lines.extend(["", "Used Sources:"])
    lines.extend(
        [f"- {source}" for source in _list(composer.get("used_sources"))]
        or ["None"]
    )
    lines.extend([
        "",
        "Debug Summary:",
        f"- Query Class: {debug.get('query_class')}",
        f"- Budget Level: {debug.get('budget_level')}",
        f"- Routing Mode: {debug.get('routing_mode')}",
        f"- Assembly Mode: {debug.get('assembly_mode')}",
        f"- Full Reports Included: {debug.get('full_reports_included')}"
    ])

    return "\n".join(lines) + "\n"


def write_response_composer_json(response_composer, path=None):

    path = Path(path) if path else RESPONSE_COMPOSER_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(response_composer, indent=2, sort_keys=True),
            encoding="utf-8"
        )
    except (OSError, TypeError, ValueError) as error:
        return {
            "success": False,
            "path": str(path),
            "error": _safe_text(error)[:180]
        }

    return {
        "success": True,
        "path": str(path),
        "error": ""
    }


def write_response_composer_text(response_composer, path=None):

    path = Path(path) if path else RESPONSE_COMPOSER_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_response_composer_text(response_composer),
            encoding="utf-8"
        )
    except (OSError, TypeError, ValueError) as error:
        return {
            "success": False,
            "path": str(path),
            "error": _safe_text(error)[:180]
        }

    return {
        "success": True,
        "path": str(path),
        "error": ""
    }


def read_response_composer(path=None):

    path = Path(path) if path else RESPONSE_COMPOSER_JSON_PATH

    try:
        response_composer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return compose_echo_response("", {}, {}, {}, {})

    return (
        response_composer
        if isinstance(response_composer, dict)
        else compose_echo_response("", {}, {}, {}, {})
    )
