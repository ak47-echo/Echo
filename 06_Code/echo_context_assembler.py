from datetime import datetime
import json
from pathlib import Path


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
CONTEXT_ASSEMBLY_JSON_PATH = REPORTS_DIR / "echo_context_assembly.json"
CONTEXT_ASSEMBLY_TEXT_PATH = REPORTS_DIR / "echo_context_assembly.txt"

AGENT_REPORT_SOURCES = {
    "portfolio": "portfolio_report",
    "research": "research_report",
    "news": "news_report",
    "macro": "macro_report"
}

SPECIAL_REPORT_SOURCES = {
    "portfolio_change_detection": "Portfolio Change Detection",
    "portfolio_ingestion": "Portfolio Ingestion",
    "security_resolution": "Security Resolution",
    "live_research": "Live Security Research",
    "security_intelligence": "Security Intelligence",
    "research_evidence_store": "Research Evidence Store",
    "thesis_refresh": "Thesis Refresh",
    "security_comparison": "Security Comparison",
    "security_master_search": "Security Master Search",
    "market_coverage": "Market Coverage",
    "dynamic_news_coverage": "Dynamic News Coverage",
    "research_snapshot": "Legacy Research Snapshot",
    "market_opportunity_scan": "Market Opportunity Scan",
    "portfolio_auto_import": "Portfolio Auto Import"
}

INVESTMENT_SOURCE_PRIORITIES = {
    "live_research": 145,
    "security_resolution": 150,
    "thesis_refresh": 140,
    "research_evidence_store": 135,
    "security_intelligence": 130,
    "security_comparison": 128,
    "security_master_search": 120,
    "market_coverage": 110,
    "dynamic_news_coverage": 105,
    "macro_snapshot": 95,
    "news_snapshot": 90,
    "research_snapshot": 40
}


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _dict(value):

    return value if isinstance(value, dict) else {}


def _list(value):

    return value if isinstance(value, list) else []


def _content(value, limit=1800):

    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=True, sort_keys=True)
        except (TypeError, ValueError):
            text = str(value)

    text = _safe_text(text)

    if len(text) > limit:
        return text[:limit - 3].rstrip() + "..."

    return text


def _report_text(report):

    if isinstance(report, dict):
        lines = []

        for key in ("executive_brief", "summary", "full_report"):
            value = report.get(key)

            if isinstance(value, str):
                lines.extend(value.splitlines())
            elif isinstance(value, list):
                lines.extend(str(item) for item in value)

        return "\n".join(line for line in lines if _safe_text(line))

    if isinstance(report, list):
        return "\n".join(str(item) for item in report if _safe_text(item))

    return _safe_text(report)


def _block(source, role, title, content, priority, limit=1800):

    text = _content(content, limit)

    if not text:
        return None

    return {
        "source": source,
        "role": role,
        "title": _safe_text(title),
        "content": text,
        "priority": int(priority or 0)
    }


def _add_block(blocks, block, seen):

    if not isinstance(block, dict):
        return False

    key = (
        block.get("source"),
        block.get("role"),
        block.get("title"),
        block.get("content")
    )

    if key in seen:
        return False

    seen.add(key)
    blocks.append(block)
    return True


def _memory_summary(memory_context):

    memory_context = _dict(memory_context)
    summary = _dict(memory_context.get("summary"))
    current = _dict(
        _dict(memory_context.get("operating_context")).get("current_state")
    )

    return {
        "summary": summary,
        "current_state": current
    }


def _memory_attention(memory_context):

    operating = _dict(_dict(memory_context).get("operating_context"))

    return {
        "recommended_attention": _list(
            operating.get("recommended_attention")
        ),
        "important_changes": _list(operating.get("important_changes")),
        "persistent_patterns": _list(operating.get("persistent_patterns"))
    }


def _memory_graph(memory_context):

    operating = _dict(_dict(memory_context).get("operating_context"))

    return {
        "connected_entities": _list(operating.get("connected_entities")),
        "top_signals": _list(operating.get("top_signals"))
    }


def _portfolio_change_report(reports):

    return _dict(reports).get("portfolio_change_detection")


def _special_report(reports, source):

    return _dict(reports).get(source)


def _assembly_mode(context_budget, agent_routing):

    budget_level = _dict(context_budget).get("budget_level") or "standard"
    query_class = _dict(context_budget).get("query_class") or "unknown"
    routing_mode = _dict(agent_routing).get("routing_mode") or "none"

    if budget_level == "minimal":
        return "minimal"

    if query_class == "portfolio_change":
        return "portfolio_change"

    if query_class in {
        "portfolio_movement",
        "holding_news",
        "security_resolution",
        "ticker_question",
        "ticker_news",
        "market_opportunities",
        "market_risks",
        "watchlist_management",
        "security_master_search",
        "paper_allocation_future"
    }:
        return "investment_query"

    if query_class == "memory" or routing_mode == "none":
        return "memory_only"

    if budget_level == "full":
        return "full"

    if routing_mode in {"multi_agent", "all_agents"}:
        return "multi_agent"

    if routing_mode == "live_security_research":
        return "investment_query"

    if routing_mode in {"single_agent", "investment_query"}:
        return "agent_focused"

    return "memory_only"


def _report_allowed(plan_item, mode, budget_level):

    if budget_level == "minimal":
        return False

    if mode == "memory_only":
        return False

    if mode == "agent_focused":
        return bool(plan_item.get("include_full_report"))

    if mode == "investment_query":
        return bool(plan_item.get("include_full_report"))

    if mode == "multi_agent":
        return budget_level in {"expanded", "full"} and bool(
            plan_item.get("include_full_report")
        )

    if mode == "full":
        return True

    return False


def _max_blocks(context_budget):

    try:
        return max(int(_dict(context_budget).get("max_context_items") or 0), 0)
    except (TypeError, ValueError):
        return 0


def assemble_echo_context(user_query, memory_context, context_budget,
                          agent_routing, reports=None):

    query = _safe_text(user_query)
    memory_context = _dict(memory_context)
    context_budget = _dict(context_budget)
    agent_routing = _dict(agent_routing)
    reports = _dict(reports)
    mode = _assembly_mode(context_budget, agent_routing)
    budget_level = context_budget.get("budget_level") or "standard"
    max_blocks = _max_blocks(context_budget)
    blocks = []
    seen = set()
    excluded_sources = set()

    if mode in {"portfolio_change", "investment_query"}:
        change_report = _portfolio_change_report(reports)
        if change_report and mode == "portfolio_change":
            _add_block(
                blocks,
                _block(
                    "portfolio_change_detection",
                    "primary",
                    "Portfolio Change Detection",
                    change_report,
                    120,
                    12000
                ),
                seen
            )
        else:
            if mode == "portfolio_change":
                excluded_sources.add("portfolio_change_detection")

    if mode == "investment_query":
        preferred_sources = context_budget.get("preferred_context_sources") or []
        for source in preferred_sources:
            if source not in SPECIAL_REPORT_SOURCES:
                continue
            content = _special_report(reports, source)
            if not content:
                excluded_sources.add(source)
                continue
            _add_block(
                blocks,
                _block(
                    source,
                    "primary" if source in preferred_sources[:2] else "secondary",
                    SPECIAL_REPORT_SOURCES[source],
                    content,
                    INVESTMENT_SOURCE_PRIORITIES.get(source, 70),
                    12000
                ),
                seen
            )

    _add_block(
        blocks,
        _block(
            "memory_context",
            "primary",
            "Memory Summary",
            _memory_summary(memory_context),
            100
        ),
        seen
    )

    if mode in {
        "memory_only",
        "agent_focused",
        "multi_agent",
        "full",
        "portfolio_change",
        "investment_query"
    }:
        _add_block(
            blocks,
            _block(
                "memory_context",
                "primary",
                "Recommended Attention And Persistence",
                _memory_attention(memory_context),
                90
            ),
            seen
        )

    if mode in {"multi_agent", "full"}:
        _add_block(
            blocks,
            _block(
                "change_detection",
                "secondary",
                "Change And Signal Summary",
                _memory_attention(memory_context),
                80
            ),
            seen
        )
        _add_block(
            blocks,
            _block(
                "knowledge_graph",
                "secondary",
                "Connected Entity Summary",
                _memory_graph(memory_context),
                75
            ),
            seen
        )

    included_agents = set()
    excluded_agents = set(agent_routing.get("excluded_agents") or [])

    for item in _list(agent_routing.get("agent_context_plan")):
        agent = item.get("agent")
        source = AGENT_REPORT_SOURCES.get(agent)

        if not source:
            continue

        if agent in excluded_agents and mode != "full":
            excluded_sources.add(source)
            continue

        if not _report_allowed(item, mode, budget_level):
            excluded_sources.add(source)
            continue

        report_text = _report_text(reports.get(agent))

        if not report_text:
            excluded_sources.add(source)
            continue

        role = item.get("role") if item.get("role") in {"primary", "secondary"} else "secondary"
        _add_block(
            blocks,
            _block(
                source,
                role,
                f"{agent.title()} Report",
                report_text,
                70 if role == "primary" else 55
            ),
            seen
        )
        included_agents.add(agent)

    if mode == "full":
        executive = reports.get("executive")

        if executive:
            _add_block(
                blocks,
                _block(
                    "executive_report",
                    "fallback",
                    "Executive Report",
                    _report_text(executive),
                    50
                ),
                seen
            )
        else:
            excluded_sources.add("executive_report")

    for agent in excluded_agents:
        source = AGENT_REPORT_SOURCES.get(agent)

        if source and agent not in included_agents:
            excluded_sources.add(source)

    blocks = sorted(
        blocks,
        key=lambda block: (-block["priority"], block["source"], block["title"])
    )

    if max_blocks:
        excluded_count = max(len(blocks) - max_blocks, 0)
        blocks = blocks[:max_blocks]

        if excluded_count:
            excluded_sources.add(f"{excluded_count}_context_blocks_over_budget")

    included_sources = []

    for block in blocks:
        source = block["source"]

        if source not in included_sources:
            included_sources.append(source)

    full_reports_included = any(
        block["source"].endswith("_report")
        for block in blocks
    )

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "assembly_mode": mode,
        "included_sources": included_sources,
        "excluded_sources": sorted(excluded_sources),
        "context_blocks": blocks,
        "context_summary": {
            "block_count": len(blocks),
            "estimated_size": sum(len(block.get("content") or "") for block in blocks),
            "memory_first": bool(blocks and blocks[0]["source"] == "memory_context"),
            "full_reports_included": full_reports_included
        },
        "reason": (
            f"Assembled {mode} context from memory, budget "
            f"{budget_level}, and routed agent plan."
        )
    }


def render_context_assembly_text(context_assembly):

    assembly = _dict(context_assembly)
    summary = _dict(assembly.get("context_summary"))
    lines = [
        "ECHO CONTEXT ASSEMBLY",
        "=====================",
        "",
        f"Schema Version: {assembly.get('schema_version') or 'unknown'}",
        f"Generated At: {assembly.get('generated_at') or 'unknown'}",
        f"Query: {assembly.get('query') or ''}",
        f"Assembly Mode: {assembly.get('assembly_mode') or 'memory_only'}",
        f"Block Count: {summary.get('block_count') or 0}",
        f"Estimated Size: {summary.get('estimated_size') or 0}",
        (
            "Full Reports Included: "
            f"{'Yes' if summary.get('full_reports_included') else 'No'}"
        ),
        "",
        "Included Sources:"
    ]
    included = assembly.get("included_sources") or []
    lines.extend([f"- {source}" for source in included] or ["None"])
    lines.extend(["", "Excluded Sources:"])
    excluded = assembly.get("excluded_sources") or []
    lines.extend([f"- {source}" for source in excluded] or ["None"])
    lines.extend(["", "Context Blocks:"])

    for block in _list(assembly.get("context_blocks")):
        lines.append(
            f"- {block.get('source')} | {block.get('role')} | "
            f"{block.get('title')} | priority {block.get('priority')}"
        )

    if not assembly.get("context_blocks"):
        lines.append("None")

    lines.extend(["", f"Reason: {assembly.get('reason') or 'None'}"])

    return "\n".join(lines) + "\n"


def write_context_assembly_json(context_assembly, path=None):

    path = Path(path) if path else CONTEXT_ASSEMBLY_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(context_assembly, indent=2, sort_keys=True),
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


def write_context_assembly_text(context_assembly, path=None):

    path = Path(path) if path else CONTEXT_ASSEMBLY_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_context_assembly_text(context_assembly),
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


def read_context_assembly(path=None):

    path = Path(path) if path else CONTEXT_ASSEMBLY_JSON_PATH

    try:
        context_assembly = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return assemble_echo_context("", {}, {}, {}, {})

    return (
        context_assembly
        if isinstance(context_assembly, dict)
        else assemble_echo_context("", {}, {}, {}, {})
    )
