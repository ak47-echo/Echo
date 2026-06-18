from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
AGENT_ROUTING_JSON_PATH = REPORTS_DIR / "echo_agent_routing.json"
AGENT_ROUTING_TEXT_PATH = REPORTS_DIR / "echo_agent_routing.txt"
ACTIVE_AGENTS = ("portfolio", "research", "news", "macro")

AGENT_KEYWORDS = {
    "portfolio": {
        "portfolio",
        "holding",
        "holdings",
        "allocation",
        "exposure",
        "risk",
        "concentration",
        "monte carlo",
        "stress test",
        "account",
        "roth",
        "brokerage",
        "position",
        "positions"
    },
    "research": {
        "thesis",
        "conviction",
        "watchlist",
        "company",
        "ticker",
        "stock",
        "valuation",
        "coverage",
        "weak holding",
        "buy",
        "sell",
        "research"
    },
    "news": {
        "news",
        "headline",
        "headlines",
        "narrative",
        "market event",
        "article",
        "current event",
        "breaking",
        "story",
        "stories"
    },
    "macro": {
        "macro",
        "fed",
        "rates",
        "rate",
        "inflation",
        "recession",
        "unemployment",
        "gdp",
        "treasury",
        "yield",
        "regime",
        "economy"
    }
}

MEMORY_TERMS = (
    "what changed",
    "what matters",
    "top priority",
    "current priority",
    "what should i focus on",
    "focus on",
    "what is persistent",
    "persistent",
    "persisted"
)

PORTFOLIO_CHANGE_TERMS = (
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
)

INVESTMENT_QUERY_CLASSES = {
    "portfolio_movement",
    "holding_news",
    "ticker_question",
    "ticker_news",
    "market_opportunities",
    "market_risks",
    "watchlist_management",
    "security_master_search",
    "paper_allocation_future"
}

SYNTHESIS_TERMS = (
    "synthesis",
    "overall picture",
    "executive summary",
    "cross-agent",
    "cross agent",
    "broad diagnosis",
    "diagnosis",
    "big picture",
    "all agents",
    "across agents"
)

CONVERSATIONAL_TERMS = (
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "what's up",
    "whats up",
    "thanks",
    "thank you",
    "tell me a joke",
    "joke",
    "make me laugh",
    "say something funny",
    "chat with me"
)


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _tokens(text):

    return set(re.findall(r"[a-z0-9]+", _safe_text(text).casefold()))


def _has_phrase(text, phrases):

    lowered = _safe_text(text).casefold()
    return any(phrase in lowered for phrase in phrases)


def _is_conversational_query(query):

    normalized = _safe_text(query).casefold().strip(" ?!.")

    exact_terms = {
        term for term in CONVERSATIONAL_TERMS
        if " " not in term
    }
    phrase_terms = tuple(
        term for term in CONVERSATIONAL_TERMS
        if " " in term
    )

    if normalized in exact_terms:
        return True

    return _has_phrase(query, phrase_terms)


def _available_agents(available_agents):

    if isinstance(available_agents, (list, tuple, set)):
        agents = [
            str(agent).strip().casefold()
            for agent in available_agents
            if str(agent).strip().casefold() in ACTIVE_AGENTS
        ]
        return agents or list(ACTIVE_AGENTS)

    return list(ACTIVE_AGENTS)


def _matched_agents(query, available_agents):

    lowered = _safe_text(query).casefold()
    tokens = _tokens(query)
    matched = []

    for agent in available_agents:
        keywords = AGENT_KEYWORDS.get(agent, set())

        if any(" " in keyword and keyword in lowered for keyword in keywords):
            matched.append(agent)
            continue

        if tokens & {keyword for keyword in keywords if " " not in keyword}:
            matched.append(agent)

    return matched


def _include_full_report(agent, role, budget_level):

    if budget_level == "minimal":
        return False

    if budget_level == "standard":
        return role == "primary"

    if budget_level == "expanded":
        return role in {"primary", "secondary"}

    if budget_level == "full":
        return True

    return False


def _context_sources(agent, role, include_full_report):

    sources = ["memory_context", f"{agent}_snapshot"]

    if include_full_report:
        sources.append(f"{agent}_full_report")

    if role == "secondary":
        sources.append("memory_context_summary")

    return sources


def _portfolio_change_plan():

    return [{
        "agent": "portfolio",
        "role": "primary",
        "context_sources": [
            "portfolio_change_detection",
            "portfolio_ingestion",
            "portfolio_snapshot"
        ],
        "include_full_report": False,
        "reason": "Portfolio-change query needs holdings-level change context."
    }]


def _investment_plan(query_class):

    plans = {
        "portfolio_movement": [(
            "portfolio",
            "primary",
            ["portfolio_change_detection", "portfolio_snapshot", "portfolio_report"],
            False,
            "Portfolio movement needs holdings change detection and current portfolio context."
        )],
        "holding_news": [
            (
                "portfolio",
                "primary",
                ["portfolio_snapshot", "market_coverage"],
                False,
                "Current holdings define affected securities."
            ),
            (
                "news",
                "secondary",
                ["dynamic_news_coverage", "news_snapshot", "news_report"],
                True,
                "Local news narratives supply event context."
            ),
            (
                "macro",
                "secondary",
                ["macro_snapshot"],
                False,
                "Macro regime supplies broad exposure context."
            )
        ],
        "ticker_question": [
            (
                "research",
                "primary",
                ["security_master_search", "market_coverage", "research_snapshot"],
                False,
                "Ticker question needs local security and research context."
            )
        ],
        "ticker_news": [
            (
                "news",
                "primary",
                [
                    "security_master_search",
                    "market_coverage",
                    "dynamic_news_coverage",
                    "news_snapshot"
                ],
                False,
                "Ticker news question needs local news context."
            ),
            (
                "research",
                "secondary",
                ["research_snapshot"],
                False,
                "Research context helps qualify local ticker coverage."
            )
        ],
        "market_opportunities": [
            (
                "research",
                "primary",
                [
                    "market_opportunity_scan",
                    "market_coverage",
                    "dynamic_news_coverage",
                    "research_snapshot",
                    "security_master_search"
                ],
                False,
                "Opportunity query needs conservative research candidates."
            ),
            (
                "news",
                "secondary",
                ["news_snapshot"],
                False,
                "News narratives provide source signals."
            ),
            (
                "macro",
                "secondary",
                ["macro_snapshot"],
                False,
                "Macro context provides source signals."
            )
        ],
        "market_risks": [
            (
                "portfolio",
                "primary",
                ["market_opportunity_scan", "market_coverage", "portfolio_snapshot"],
                False,
                "Risk query should include held-position risk candidates."
            ),
            (
                "news",
                "secondary",
                ["news_snapshot"],
                False,
                "News narratives provide downside signals."
            ),
            (
                "macro",
                "secondary",
                ["macro_snapshot"],
                False,
                "Macro regime provides downside signals."
            )
        ],
        "watchlist_management": [(
            "research",
            "primary",
            [
                "research_snapshot",
                "market_opportunity_scan",
                "market_coverage",
                "dynamic_news_coverage",
                "news_snapshot",
                "macro_snapshot"
            ],
            False,
            "Watchlist query belongs to research context."
        )],
        "security_master_search": [(
            "research",
            "primary",
            ["security_master_search", "market_coverage"],
            False,
            "Security master search uses the broad local security universe."
        )],
        "paper_allocation_future": [(
            "research",
            "primary",
            ["research_snapshot", "market_opportunity_scan"],
            False,
            "Paper allocation is future-mode only; use research candidates as context."
        )]
    }
    plan = []
    for agent, role, sources, include_full, reason in plans.get(query_class, []):
        plan.append({
            "agent": agent,
            "role": role,
            "context_sources": sources,
            "include_full_report": include_full,
            "reason": reason
        })
    return plan


def _plan(primary_agents, secondary_agents, budget_level):

    plan = []

    for role, agents in (
        ("primary", primary_agents),
        ("secondary", secondary_agents)
    ):
        for agent in agents:
            include_full_report = _include_full_report(
                agent,
                role,
                budget_level
            )
            plan.append({
                "agent": agent,
                "role": role,
                "context_sources": _context_sources(
                    agent,
                    role,
                    include_full_report
                ),
                "include_full_report": include_full_report,
                "reason": (
                    f"{agent} matched as {role} context under "
                    f"{budget_level} budget."
                )
            })

    return plan


def route_query_to_agents(user_query, context_budget=None, memory_context=None,
                          available_agents=None):

    query = _safe_text(user_query)
    context_budget = context_budget if isinstance(context_budget, dict) else {}
    budget_level = context_budget.get("budget_level") or "standard"
    query_class = context_budget.get("query_class") or "unknown"
    agents = _available_agents(available_agents)
    matched = _matched_agents(query, agents)

    if query_class == "conversational" or _is_conversational_query(query):
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": [],
            "secondary_agents": [],
            "excluded_agents": agents,
            "routing_mode": "none",
            "confidence": "high",
            "agent_context_plan": [],
            "reason": "Conversational prompt; no agent report routing needed."
        }

    if _has_phrase(query, PORTFOLIO_CHANGE_TERMS) or query_class == "portfolio_change":
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": ["portfolio"],
            "secondary_agents": [],
            "excluded_agents": [
                agent for agent in agents if agent != "portfolio"
            ],
            "routing_mode": "single_agent",
            "confidence": "high",
            "agent_context_plan": _portfolio_change_plan(),
            "reason": (
                "Portfolio-change query should be answered from normalized "
                "holdings change detection."
            )
        }

    if query_class in INVESTMENT_QUERY_CLASSES:
        plan = _investment_plan(query_class)
        primary_agents = [
            item["agent"] for item in plan if item.get("role") == "primary"
        ]
        secondary_agents = [
            item["agent"] for item in plan if item.get("role") == "secondary"
        ]
        included = set(primary_agents + secondary_agents)
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": primary_agents,
            "secondary_agents": secondary_agents,
            "excluded_agents": [
                agent for agent in agents if agent not in included
            ],
            "routing_mode": "investment_query",
            "confidence": "high",
            "agent_context_plan": plan,
            "reason": (
                "Universal investment query routed by investment intent "
                f"{query_class}."
            )
        }

    if _has_phrase(query, MEMORY_TERMS) or query_class == "memory":
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": [],
            "secondary_agents": [],
            "excluded_agents": agents,
            "routing_mode": "none",
            "confidence": "high",
            "agent_context_plan": [],
            "reason": "Memory/meta query should be answered from Echo memory first."
        }

    if query_class == "multi_agent" and matched and not _has_phrase(
        query,
        SYNTHESIS_TERMS
    ):
        excluded_agents = [
            agent for agent in agents
            if agent not in matched
        ]
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": matched,
            "secondary_agents": [],
            "excluded_agents": excluded_agents,
            "routing_mode": "multi_agent",
            "confidence": "high",
            "agent_context_plan": _plan(matched, [], budget_level),
            "reason": (
                "Multi-agent query matched specific active agents; routing "
                "only those relevant contexts."
            )
        }

    if _has_phrase(query, SYNTHESIS_TERMS) or query_class == "multi_agent":
        plan = _plan(agents, [], budget_level)
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": agents,
            "secondary_agents": [],
            "excluded_agents": [],
            "routing_mode": "all_agents",
            "confidence": "high",
            "agent_context_plan": plan,
            "reason": "Broad synthesis query needs all active agent contexts."
        }

    if not matched:
        return {
            "schema_version": "1.0",
            "generated_at": _now(),
            "query": query,
            "primary_agents": [],
            "secondary_agents": [],
            "excluded_agents": agents,
            "routing_mode": "none",
            "confidence": "low",
            "agent_context_plan": [],
            "reason": "No active agent keyword matched; use Echo memory first."
        }

    primary_agents = matched[:1]
    secondary_agents = matched[1:]

    if query_class in {"deep_dive", "multi_agent"} and len(matched) == 1:
        secondary_agents = [
            agent for agent in agents
            if agent not in primary_agents
        ]

    excluded_agents = [
        agent for agent in agents
        if agent not in primary_agents and agent not in secondary_agents
    ]
    routing_mode = "single_agent" if len(primary_agents) == 1 and not secondary_agents else "multi_agent"
    confidence = "high" if primary_agents else "medium"

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "primary_agents": primary_agents,
        "secondary_agents": secondary_agents,
        "excluded_agents": excluded_agents,
        "routing_mode": routing_mode,
        "confidence": confidence,
        "agent_context_plan": _plan(
            primary_agents,
            secondary_agents,
            budget_level
        ),
        "reason": (
            "Matched active agent keywords and applied context budget "
            f"{budget_level}."
        )
    }


def render_agent_routing_text(agent_routing):

    routing = agent_routing if isinstance(agent_routing, dict) else {}
    lines = [
        "ECHO AGENT ROUTING",
        "==================",
        "",
        f"Schema Version: {routing.get('schema_version') or 'unknown'}",
        f"Generated At: {routing.get('generated_at') or 'unknown'}",
        f"Query: {routing.get('query') or ''}",
        f"Routing Mode: {routing.get('routing_mode') or 'none'}",
        f"Confidence: {routing.get('confidence') or 'low'}",
        "",
        "Primary Agents:"
    ]
    primary = routing.get("primary_agents") or []
    lines.extend([f"- {agent}" for agent in primary] or ["None"])
    lines.extend(["", "Secondary Agents:"])
    secondary = routing.get("secondary_agents") or []
    lines.extend([f"- {agent}" for agent in secondary] or ["None"])
    lines.extend(["", "Excluded Agents:"])
    excluded = routing.get("excluded_agents") or []
    lines.extend([f"- {agent}" for agent in excluded] or ["None"])
    lines.extend(["", "Agent Context Plan:"])

    plan = routing.get("agent_context_plan") or []
    if plan:
        for item in plan:
            sources = ", ".join(item.get("context_sources") or [])
            lines.append(
                f"- {item.get('agent')} | {item.get('role')} | "
                f"Full Report: {item.get('include_full_report')} | "
                f"Sources: {sources}"
            )
    else:
        lines.append("None")

    lines.extend(["", f"Reason: {routing.get('reason') or 'None'}"])

    return "\n".join(lines) + "\n"


def write_agent_routing_json(agent_routing, path=None):

    path = Path(path) if path else AGENT_ROUTING_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(agent_routing, indent=2, sort_keys=True),
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


def write_agent_routing_text(agent_routing, path=None):

    path = Path(path) if path else AGENT_ROUTING_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_agent_routing_text(agent_routing),
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


def read_agent_routing(path=None):

    path = Path(path) if path else AGENT_ROUTING_JSON_PATH

    try:
        agent_routing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return route_query_to_agents("")

    return (
        agent_routing
        if isinstance(agent_routing, dict)
        else route_query_to_agents("")
    )
