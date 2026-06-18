from datetime import datetime
import json
from pathlib import Path
import re

from echo_investment_intent import classify_investment_intent


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
                 "holdings", "rebalance", "stress", "tax", "risk",
                 "exposed", "exposure"}:
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


def _is_conversational_query(query):

    normalized = _safe_text(query).casefold().strip(" ?!.")

    if normalized in {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "what's up",
        "whats up",
        "thanks",
        "thank you"
    }:
        return True

    return _has_any(query, (
        "tell me a joke",
        "joke",
        "make me laugh",
        "say something funny",
        "chat with me"
    ))


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


def _is_portfolio_change_query(query):

    return _has_any(query, (
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
        "from last report",
        "since last report",
        "concentration change",
        "concentration changed",
        "did my concentration change",
        "did cash change",
        "cash change",
        "cash changed"
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
    if _is_conversational_query(query):
        return (
            "conversational",
            "minimal",
            ["memory_context"],
            ["full_reports", "agent_reports", "knowledge_graph"],
            ["echo_get_memory_context"],
            "Conversational prompt; keep agent context light unless requested."
        )

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

    if _is_portfolio_change_query(query):
        return (
            "portfolio_change",
            "standard",
            [
                "portfolio_change_detection",
                "portfolio_ingestion",
                "portfolio_snapshot"
            ],
            ["generic_state_delta"],
            [
                "echo_get_portfolio_change_detection",
                "echo_get_portfolio_ingestion"
            ],
            "Query asks about holdings-level portfolio changes."
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

    investment_intent = classify_investment_intent(query)
    intent = investment_intent.get("investment_intent")

    if intent == "portfolio_change":
        return (
            "portfolio_change",
            "standard",
            [
                "portfolio_change_detection",
                "portfolio_ingestion",
                "portfolio_snapshot"
            ],
            ["generic_state_delta"],
            [
                "echo_get_portfolio_change_detection",
                "echo_get_portfolio_ingestion"
            ],
            "Query asks about holdings-level portfolio changes."
        )

    if intent == "portfolio_movement":
        return (
            "portfolio_movement",
            "standard",
            [
                "portfolio_change_detection",
                "portfolio_snapshot",
                "portfolio_report"
            ],
            ["generic_state_delta"],
            [
                "echo_get_portfolio_change_detection",
                "echo_get_portfolio_snapshot"
            ],
            "Query asks what drove portfolio movement."
        )

    if intent == "holding_news":
        return (
            "holding_news",
            "expanded",
            [
                "portfolio_snapshot",
                "market_coverage",
                "dynamic_news_coverage",
                "news_snapshot",
                "macro_snapshot"
            ],
            ["generic_state_delta"],
            [
                "echo_get_portfolio_snapshot",
                "echo_get_market_coverage",
                "echo_get_dynamic_news_coverage",
                "echo_get_news_snapshot",
                "echo_get_macro_snapshot"
            ],
            "Query asks which news or macro themes affect current holdings."
        )

    if intent in {"ticker_question", "ticker_news"}:
        ticker_sources = [
            "security_intelligence",
            "research_evidence_store",
            "thesis_refresh",
            "security_master_search",
            "market_coverage",
            "dynamic_news_coverage",
            "portfolio_snapshot",
            "research_snapshot",
            "news_snapshot"
        ]
        if len(investment_intent.get("tickers") or []) >= 2:
            ticker_sources.insert(1, "security_comparison")
        return (
            intent,
            "standard",
            ticker_sources,
            ["generic_state_delta"],
            [
                "echo_get_security_intelligence",
                "echo_get_live_research",
                "echo_get_thesis_refresh",
                "echo_compare_securities",
                "echo_search_security_master",
                "echo_get_market_coverage",
                "echo_get_dynamic_news_coverage",
                "echo_get_research_snapshot",
                "echo_get_news_snapshot"
            ],
            "Query asks about a specific ticker or security."
        )

    if intent in {"market_opportunities", "market_risks"}:
        return (
            intent,
            "expanded",
            [
                "market_opportunity_scan",
                "security_intelligence",
                "research_evidence_store",
                "thesis_refresh",
                "market_coverage",
                "dynamic_news_coverage",
                "news_snapshot",
                "macro_snapshot",
                "research_snapshot",
                "security_master_search"
            ],
            ["generic_state_delta"],
            [
                "echo_get_market_opportunity_scan",
                "echo_get_security_intelligence",
                "echo_get_live_research",
                "echo_get_thesis_refresh",
                "echo_get_market_coverage",
                "echo_get_dynamic_news_coverage",
                "echo_search_security_master",
                "echo_get_news_snapshot",
                "echo_get_macro_snapshot",
                "echo_get_research_snapshot"
            ],
            "Query asks for market opportunity or risk research candidates."
        )

    if intent == "security_master_search":
        return (
            "security_master_search",
            "standard",
            [
                "security_master_search",
                "security_intelligence",
                "research_evidence_store",
                "thesis_refresh",
                "market_coverage"
            ],
            ["generic_state_delta", "full_reports"],
            [
                "echo_get_security_intelligence",
                "echo_get_live_research",
                "echo_get_thesis_refresh",
                "echo_search_security_master",
                "echo_get_market_coverage"
            ],
            "Query asks to search the local security master."
        )

    if intent == "watchlist_management":
        return (
            "watchlist_management",
            "expanded",
            [
                "research_snapshot",
                "market_opportunity_scan",
                "market_coverage",
                "dynamic_news_coverage",
                "news_snapshot",
                "macro_snapshot"
            ],
            ["generic_state_delta"],
            [
                "echo_get_research_snapshot",
                "echo_get_market_opportunity_scan",
                "echo_get_market_coverage",
                "echo_get_dynamic_news_coverage",
                "echo_get_news_snapshot",
                "echo_get_macro_snapshot"
            ],
            "Query asks for watchlist review or management."
        )

    if intent == "paper_allocation_future":
        return (
            "paper_allocation_future",
            "minimal",
            ["research_snapshot", "market_opportunity_scan"],
            ["trading", "brokerage", "generic_state_delta"],
            ["echo_get_market_opportunity_scan", "echo_get_research_snapshot"],
            "Query asks about future paper allocation mode."
        )

    if intent == "portfolio_snapshot":
        return (
            "agent_specific",
            "expanded",
            ["memory_context", "portfolio_snapshot", "portfolio_report"],
            ["unrelated_reports"],
            ["echo_get_memory_context", "echo_get_portfolio_snapshot"],
            "Query asks about current portfolio holdings or allocation."
        )

    if intent == "general_market_question":
        return (
            "multi_agent",
            "standard",
            ["news_snapshot", "macro_snapshot", "memory_context"],
            ["unrelated_full_reports"],
            [
                "echo_get_news_snapshot",
                "echo_get_macro_snapshot",
                "echo_get_memory_context"
            ],
            "Query asks a broad market or macro question."
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
    agents = [] if _is_conversational_query(query) else _agent_terms(query)
    investment_intent = classify_investment_intent(
        query,
        memory_context=memory_context
    )
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
        "investment_intent": investment_intent,
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
