from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
CONTEXT_BUDGET_JSON_PATH = REPORTS_DIR / "echo_context_budget.json"
CONTEXT_BUDGET_TEXT_PATH = REPORTS_DIR / "echo_context_budget.txt"

BUDGET_LEVEL_ITEMS = {
    "minimal": 5,
    "standard": 20,
    "expanded": 40,
    "full": 80
}

AGENT_SOURCE_MAP = {
    "portfolio": ("portfolio_report", "portfolio_snapshot"),
    "research": ("research_report", "research_snapshot"),
    "news": ("news_report", "news_snapshot"),
    "macro": ("macro_report", "macro_snapshot")
}


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _tokens(text):

    return set(re.findall(r"[a-z0-9]+", _safe_text(text).casefold()))


def _has_any(text, terms):

    lowered = _safe_text(text).casefold()
    return any(term in lowered for term in terms)


def _available_tools(available_tools):

    if isinstance(available_tools, (list, tuple, set)):
        return [str(tool) for tool in available_tools if str(tool)]

    return []


def _agent_terms(query):

    tokens = _tokens(query)
    agents = []

    if tokens & {"portfolio", "allocation", "concentration", "holding",
                 "holdings", "rebalance", "stress", "tax"}:
        agents.append("portfolio")

    if tokens & {"research", "thesis", "conviction", "coverage",
                 "watchlist"}:
        agents.append("research")

    if tokens & {"news", "headline", "headlines", "market", "narrative",
                 "world"}:
        agents.append("news")

    if tokens & {"macro", "inflation", "rates", "rate", "fed", "yield",
                 "energy", "regime"}:
        agents.append("macro")

    return agents


def _is_greeting_or_status(query):

    normalized = _safe_text(query).casefold().strip(" ?!.")
    tokens = _tokens(query)

    if normalized in {"hi", "hello", "hey", "thanks", "thank you"}:
        return True

    if normalized in {"status", "system status", "are you working"}:
        return True

    return bool(tokens & {"health", "status"}) and len(tokens) <= 5


def _is_deep_dive(query):

    return _has_any(query, (
        "deep dive",
        "detailed",
        "detail",
        "full breakdown",
        "breakdown",
        "diagnose",
        "diagnosis",
        "explain why",
        "reasoning",
        "walk me through",
        "full report",
        "comprehensive"
    ))


def _is_memory_query(query):

    return _has_any(query, (
        "what changed",
        "changed",
        "change",
        "what matters",
        "matters",
        "top priority",
        "current priority",
        "priority",
        "persistent",
        "persisted",
        "persistent risks",
        "remember",
        "attention"
    ))


def _is_multi_agent(query, agents):

    if len(set(agents)) >= 2:
        return True

    return _has_any(query, (
        "synthesis",
        "cross-agent",
        "across agents",
        "overall",
        "big picture",
        "connect",
        "connected",
        "relationship",
        "relationships",
        "everything",
        "portfolio and macro",
        "portfolio and news",
        "macro and news",
        "research and portfolio"
    ))


def _base_budget(query, agents):

    if _is_greeting_or_status(query):
        return (
            "simple",
            "minimal",
            ["memory_context"],
            ["full_reports", "knowledge_graph", "change_detection"],
            ["echo_get_memory_context"],
            "Greeting/status query; minimal memory context is sufficient."
        )

    if _is_deep_dive(query):
        return (
            "deep_dive",
            "full",
            [
                "memory_context",
                "change_detection",
                "delta",
                "history",
                "knowledge_graph",
                "full_reports"
            ],
            [],
            [
                "echo_get_memory_context",
                "echo_get_change_detection",
                "echo_get_knowledge_graph"
            ],
            "Deep-dive wording requests detailed secondary context."
        )

    if _is_multi_agent(query, agents):
        return (
            "multi_agent",
            "expanded",
            [
                "memory_context",
                "change_detection",
                "knowledge_graph",
                "relevant_reports"
            ],
            ["unrelated_full_reports"],
            [
                "echo_get_memory_context",
                "echo_get_change_detection",
                "echo_get_knowledge_graph"
            ],
            "Broad synthesis query spans multiple agents or relationship layers."
        )

    if len(agents) == 1:
        agent = agents[0]
        report_source, snapshot_source = AGENT_SOURCE_MAP[agent]
        return (
            "agent_specific",
            "expanded" if agent == "portfolio" else "standard",
            ["memory_context", snapshot_source, report_source],
            ["unrelated_reports"],
            [
                "echo_get_memory_context",
                f"echo_get_{agent}_snapshot"
            ],
            f"Query is specific to the {agent} agent context."
        )

    if _is_memory_query(query):
        return (
            "memory",
            "standard",
            ["memory_context", "change_detection", "delta", "history"],
            ["full_reports"],
            [
                "echo_get_memory_context",
                "echo_get_change_detection",
                "echo_get_state_delta",
                "echo_get_state_history"
            ],
            "Query asks for current memory, changes, or persistence."
        )

    return (
        "unknown",
        "standard",
        ["memory_context"],
        ["full_reports_unless_needed"],
        ["echo_get_memory_context"],
        "No specific routing pattern matched; use standard memory-first context."
    )


def build_context_budget(user_query, memory_context=None, available_tools=None):

    query = _safe_text(user_query)
    tools = _available_tools(available_tools)
    agents = _agent_terms(query)
    (
        query_class,
        budget_level,
        preferred_sources,
        excluded_sources,
        tool_hints,
        reason
    ) = _base_budget(query, agents)

    tool_hints = [
        tool for tool in tool_hints
        if not tools or tool in tools
    ]

    if isinstance(memory_context, dict) and memory_context:
        memory_budget = memory_context.get("context_budget") or {}
        memory_max = memory_budget.get("max_items")
        try:
            memory_max = int(memory_max)
        except (TypeError, ValueError):
            memory_max = None

        if memory_max and budget_level in {"minimal", "standard"}:
            max_context_items = min(BUDGET_LEVEL_ITEMS[budget_level], memory_max)
        else:
            max_context_items = BUDGET_LEVEL_ITEMS[budget_level]
    else:
        max_context_items = BUDGET_LEVEL_ITEMS[budget_level]

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "query_class": query_class,
        "budget_level": budget_level,
        "max_context_items": max_context_items,
        "preferred_context_sources": preferred_sources,
        "excluded_context_sources": excluded_sources,
        "tool_hints": tool_hints,
        "reason": reason
    }


def render_context_budget_text(context_budget):

    budget = context_budget if isinstance(context_budget, dict) else {}
    lines = [
        "ECHO CONTEXT BUDGET",
        "===================",
        "",
        f"Schema Version: {budget.get('schema_version') or 'unknown'}",
        f"Generated At: {budget.get('generated_at') or 'unknown'}",
        f"Query: {budget.get('query') or ''}",
        f"Query Class: {budget.get('query_class') or 'unknown'}",
        f"Budget Level: {budget.get('budget_level') or 'standard'}",
        f"Max Context Items: {budget.get('max_context_items') or 0}",
        "",
        "Preferred Context Sources:"
    ]

    preferred = budget.get("preferred_context_sources") or []
    lines.extend([f"- {source}" for source in preferred] or ["None"])
    lines.extend(["", "Excluded Context Sources:"])
    excluded = budget.get("excluded_context_sources") or []
    lines.extend([f"- {source}" for source in excluded] or ["None"])
    lines.extend(["", "Tool Hints:"])
    hints = budget.get("tool_hints") or []
    lines.extend([f"- {tool}" for tool in hints] or ["None"])
    lines.extend(["", f"Reason: {budget.get('reason') or 'None'}"])

    return "\n".join(lines) + "\n"


def write_context_budget_json(context_budget, path=None):

    path = Path(path) if path else CONTEXT_BUDGET_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(context_budget, indent=2, sort_keys=True),
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


def write_context_budget_text(context_budget, path=None):

    path = Path(path) if path else CONTEXT_BUDGET_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_context_budget_text(context_budget),
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


def read_context_budget(path=None):

    path = Path(path) if path else CONTEXT_BUDGET_JSON_PATH

    try:
        context_budget = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_context_budget("", None)

    return (
        context_budget
        if isinstance(context_budget, dict)
        else build_context_budget("", None)
    )
