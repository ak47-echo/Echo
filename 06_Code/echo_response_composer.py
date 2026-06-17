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
    "echo_get_state_history"
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

    if intent in {
        "priority_status",
        "change_status",
        "persistence_status",
        "attention_status"
    }:
        return "memory"

    if intent in {"cross_agent_synthesis"} or routing_mode == "all_agents":
        return "multi_agent_summary"

    if intent in {"agent_summary", "risk_explanation"}:
        return "agent_summary"

    return "fallback"


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
    elif intent == "change_status":
        answer, supporting_points, caveats = _change_response(memory_context)
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
            "I do not have a specific deterministic answer for that query yet. "
            "The compact memory context is available, but the request did not "
            "map cleanly to priority, change, persistence, attention, agent, "
            "risk, or synthesis intent."
        )
        response_mode = "fallback"
        caveats = ["Ask for priority, changes, persistence, attention, or an agent summary."]

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
