from agents.news_agent import get_news_report
from agents.macro_agent import get_macro_report
from agents.portfolio_manager import get_portfolio_report
from agents.research_agent import get_research_agent_report
from agents.policy_agent import get_policy
from datetime import datetime
from echo_state import build_echo_state, write_echo_state
from echo_state_delta import (
    build_echo_state_delta,
    load_previous_state,
    read_state_delta,
    save_state_snapshot,
    write_state_delta_json,
    write_state_delta_text
)
from echo_state_history import (
    STATE_ARCHIVE_DIR,
    build_echo_state_history,
    read_state_history,
    write_state_history_json,
    write_state_history_text
)
from echo_change_detection import (
    build_echo_change_detection,
    read_change_detection,
    write_change_detection_json,
    write_change_detection_text
)
from echo_knowledge_graph import (
    build_echo_knowledge_graph,
    read_knowledge_graph,
    write_knowledge_graph_json,
    write_knowledge_graph_text
)
from echo_memory_context import (
    build_echo_memory_context,
    read_memory_context,
    write_memory_context_json,
    write_memory_context_text
)
from echo_context_budget import (
    build_context_budget,
    read_context_budget,
    write_context_budget_json,
    write_context_budget_text
)
from echo_agent_router import (
    read_agent_routing,
    route_query_to_agents,
    write_agent_routing_json,
    write_agent_routing_text
)
from echo_context_assembler import (
    assemble_echo_context,
    read_context_assembly,
    write_context_assembly_json,
    write_context_assembly_text
)
from echo_response_composer import (
    compose_echo_response,
    read_response_composer,
    write_response_composer_json,
    write_response_composer_text
)
from echo_intent_reasoning import (
    classify_reasoning_intent,
    read_intent_reasoning,
    write_intent_reasoning_json,
    write_intent_reasoning_text
)
import json
import os
from pathlib import Path
import re
import shutil
from time import perf_counter


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
REPORT_ARCHIVE_ENABLED = True
REPORT_ARCHIVE_KEEP_COUNT = 10
REPORT_ARCHIVE_DIR = REPORTS_DIR / "archive"

AGENT_REGISTRY = (
    {
        "agent_name": "News Agent",
        "role": "Intelligence Officer",
        "status": "ACTIVE",
        "health": "UNKNOWN",
        "report_mode": "SUPPORTED",
        "query_mode": "SUPPORTED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "NEWS AGENT EXECUTIVE BRIEF",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Macro Agent",
        "role": "Macro Strategist",
        "status": "ACTIVE",
        "health": "UNKNOWN",
        "report_mode": "SUPPORTED",
        "query_mode": "SUPPORTED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "MACRO AGENT EXECUTIVE BRIEF",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Portfolio Manager",
        "role": "Chief Investment Officer",
        "status": "ACTIVE",
        "health": "UNKNOWN",
        "report_mode": "SUPPORTED",
        "query_mode": "SUPPORTED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "PORTFOLIO MANAGER EXECUTIVE BRIEF",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Research Agent",
        "role": "Research Analyst",
        "status": "ACTIVE",
        "health": "UNKNOWN",
        "report_mode": "SUPPORTED",
        "query_mode": "SUPPORTED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "RESEARCH AGENT EXECUTIVE BRIEF",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Calendar Agent",
        "role": "Scheduling Officer",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Email Agent",
        "role": "Communications Officer",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Project Manager Agent",
        "role": "Project Manager",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Knowledge Agent",
        "role": "Knowledge Manager",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Career Agent",
        "role": "Career Strategist",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Health Agent",
        "role": "Health Analyst",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    },
    {
        "agent_name": "Deal Flow Agent",
        "role": "Opportunity Scout",
        "status": "PLACEHOLDER",
        "health": "UNKNOWN",
        "report_mode": "NOT_SUPPORTED",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "",
        "failure_message": "",
        "notes": ""
    }
)

AGENT_QUERY_CAPABILITIES = {
    "Portfolio Manager": {
        "supported_query_types": (
            "risk",
            "concentration",
            "allocation",
            "opportunity",
            "tax",
            "stress test"
        ),
        "planned_query_types": (),
        "example_queries": (
            "What is my concentration risk?",
            "What is the top portfolio risk?",
            "What is the tax situation?"
        )
    },
    "News Agent": {
        "supported_query_types": (
            "market narrative",
            "macro news",
            "world event",
            "portfolio news",
            "watchlist news"
        ),
        "planned_query_types": (),
        "example_queries": (
            "What is the top market narrative?",
            "What is the top macro news?",
            "What world event matters most?"
        )
    },
    "Macro Agent": {
        "supported_query_types": (
            "regime",
            "inflation",
            "rates",
            "labor",
            "yield curve",
            "energy"
        ),
        "planned_query_types": (),
        "example_queries": (
            "What is the current regime?",
            "What is happening with inflation?",
            "What is the energy signal?"
        )
    },
    "Research Agent": {
        "supported_query_types": (
            "thesis",
            "conviction",
            "research gaps",
            "weak holdings",
            "watchlist"
        ),
        "planned_query_types": (),
        "example_queries": (
            "Which holdings have weak conviction?",
            "What are the research gaps?",
            "What is on the watchlist?"
        )
    }
}

FUTURE_AGENT_QUERY_CAPABILITY = {
    "supported_query_types": (),
    "planned_query_types": ("basic future capability description",),
    "example_queries": ("What capabilities are planned for this agent?",)
}

AGENT_NAME_ALIASES = {
    "echo": "Echo",
    "chief of staff": "Echo",
    "system": "Echo",
    "news": "News Agent",
    "macro": "Macro Agent",
    "portfolio": "Portfolio Manager",
    "portfolio agent": "Portfolio Manager",
    "research": "Research Agent",
    "calendar": "Calendar Agent",
    "email": "Email Agent",
    "project manager": "Project Manager Agent",
    "project": "Project Manager Agent",
    "knowledge": "Knowledge Agent",
    "career": "Career Agent",
    "health": "Health Agent",
    "deal flow": "Deal Flow Agent"
}

QUERY_INTERFACE_AGENT_ORDER = (
    "Portfolio Manager",
    "News Agent",
    "Macro Agent",
    "Research Agent",
    "Calendar Agent",
    "Email Agent",
    "Project Manager Agent",
    "Knowledge Agent",
    "Career Agent",
    "Health Agent",
    "Deal Flow Agent"
)

ACTIVE_REPORT_AGENTS = (
    "News Agent",
    "Macro Agent",
    "Research Agent",
    "Portfolio Manager"
)

PRIORITY_SEVERITY_SCORES = {
    "CRITICAL": 100,
    "HIGH": 75,
    "MEDIUM": 50,
    "LOW": 25,
    "INFO": 10
}

PRIORITY_AGENT_RANKS = {
    "Portfolio Manager": 0,
    "Research Agent": 1,
    "Macro Agent": 2,
    "News Agent": 3,
    "Agent Registry": 4
}

SIGNAL_SOURCE_WEIGHTS = {
    "Portfolio Manager": 10,
    "Research Agent": 8,
    "Macro Agent": 6,
    "News Agent": 4,
    "Agent Registry": 10
}

SIGNAL_CONFIDENCE_WEIGHTS = {
    "HIGH": 5,
    "MEDIUM": 2,
    "LOW": 0,
    "UNKNOWN": 0
}

SIGNAL_CATEGORY_WEIGHTS = {
    "Portfolio Risk": 10,
    "Research Gap": 8,
    "Macro Risk": 7,
    "Market Event": 5,
    "Portfolio Opportunity": 4,
    "Macro Environment": 3,
    "Agent Health": 10,
    "System Infrastructure": 3
}

THEME_CATEGORY_IMPORTANCE = {
    "Inflation/Energy Risk": 18,
    "Fed/Rates Risk": 16,
    "Recession/Growth Slowdown Risk": 16,
    "Portfolio Concentration Risk": 15,
    "Research Quality Risk": 14,
    "Tax/Capital Deployment Theme": 10,
    "Market/Regulatory Event Theme": 10,
    "Agent Health/System Theme": 18
}

THEME_TITLE_ORDER = (
    "Inflation/Energy Risk",
    "Fed/Rates Risk",
    "Recession/Growth Slowdown Risk",
    "Portfolio Concentration Risk",
    "Research Quality Risk",
    "Tax/Capital Deployment Theme",
    "Market/Regulatory Event Theme",
    "Agent Health/System Theme"
)

THEME_SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "HIGH": 14,
    "MEDIUM": 8,
    "LOW": 3,
    "INFO": 1
}

THEME_RISK_CHANNELS = {
    "Inflation/Energy Risk": (
        "oil prices, inflation pressure, rates expectations"
    ),
    "Fed/Rates Risk": (
        "discount rates, liquidity, valuation multiples"
    ),
    "Recession/Growth Slowdown Risk": (
        "earnings expectations, risk appetite, drawdown risk"
    ),
    "Portfolio Concentration Risk": (
        "single-name drawdown concentration"
    ),
    "Research Quality Risk": (
        "position size unsupported by thesis quality"
    ),
    "Tax/Capital Deployment Theme": (
        "tax drag, opportunity cost, capital allocation"
    ),
    "Market/Regulatory Event Theme": (
        "headline risk, regulatory pressure, market repricing"
    ),
    "Agent Health/System Theme": (
        "report reliability, monitoring coverage, execution confidence"
    )
}


def add_section(title, items):

    section = ""

    section += f"{title}\n"
    section += "-" * len(title)
    section += "\n\n"

    for item in items:

        if item == "":
            section += "\n"
        elif item.isupper():
            section += f"\n{item}\n"
            section += "-" * len(item)
            section += "\n\n"
        else:
            section += f"{item}\n"

    section += "\n"

    return section


def _report_lines(report):

    if isinstance(report, dict):
        lines = report.get("executive_brief", [])
    else:
        lines = report or []

    if isinstance(lines, str):
        lines = lines.splitlines()

    return [str(line).strip() for line in lines]


def _full_report_lines(report):

    if isinstance(report, dict):
        lines = report.get("full_report", [])
    else:
        lines = report or []

    if isinstance(lines, str):
        lines = lines.splitlines()

    return [str(line).strip() for line in lines]


def _combined_report_lines(report):

    if isinstance(report, dict):
        return _report_lines(report) + _full_report_lines(report)

    return _report_lines(report)


def _field_value(lines, label):

    prefix = f"{label}:"

    for line in lines:
        if line.startswith(prefix):
            value = line[len(prefix):].strip()

            if value and value.casefold() not in {
                "none",
                "n/a",
                "unknown"
            }:
                return value

    return ""


def _report_section(lines, heading):

    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []

    section = []

    for line in lines[start:]:
        if line and line.isupper():
            break

        if line:
            section.append(line)

    return section


def _sentence(text):

    text = " ".join(str(text or "").split()).rstrip(".")
    return f"{text}." if text else ""


def _concise(text, limit=180):

    text = " ".join(str(text or "").split())

    if len(text) <= limit:
        return text

    return text[:limit - 3].rstrip() + "..."


def score_priority(severity):

    return PRIORITY_SEVERITY_SCORES.get(
        str(severity or "").strip().upper(),
        0
    )


def normalize_signal(
    source_agent,
    signal_type,
    severity,
    title,
    description,
    confidence="UNKNOWN",
    category="System Infrastructure",
    metadata=None,
    magnitude_value=None,
    magnitude_unit="none",
    magnitude_score=0,
    magnitude_basis="No magnitude adjustment."
):

    source_agent = " ".join(str(source_agent or "").split())
    signal_type = " ".join(str(signal_type or "").split()).upper()
    title = " ".join(str(title or "").split())
    description = " ".join(str(description or "").split())
    severity = str(severity or "").strip().upper()
    confidence = str(confidence or "UNKNOWN").strip().upper()
    category = " ".join(str(category or "").split())

    if (
        not source_agent
        or not signal_type
        or not title
        or severity not in PRIORITY_SEVERITY_SCORES
    ):
        return None

    if confidence not in {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}:
        confidence = "UNKNOWN"

    base_score = score_priority(severity)
    weighted_score = (
        base_score
        + SIGNAL_SOURCE_WEIGHTS.get(source_agent, 0)
        + SIGNAL_CONFIDENCE_WEIGHTS.get(confidence, 0)
        + SIGNAL_CATEGORY_WEIGHTS.get(category, 0)
    )

    return {
        "source_agent": source_agent,
        "signal_type": signal_type,
        "severity": severity,
        "title": _concise(title),
        "description": _concise(description or title, limit=240),
        "confidence": confidence,
        "category": category or "System Infrastructure",
        "score": base_score,
        "metadata": dict(metadata) if isinstance(metadata, dict) else {},
        "magnitude_value": magnitude_value,
        "magnitude_unit": magnitude_unit or "none",
        "magnitude_score": int(magnitude_score or 0),
        "magnitude_basis": (
            " ".join(str(magnitude_basis or "").split())
            or "No magnitude adjustment."
        ),
        "weighted_score": weighted_score,
        "magnitude_adjusted_score": (
            weighted_score + int(magnitude_score or 0)
        )
    }


def _append_signal(signals, *args, **kwargs):

    signal = normalize_signal(*args, **kwargs)

    if signal is not None:
        signals.append(signal)


def build_portfolio_signals(portfolio):

    lines = _report_lines(portfolio)
    signals = []
    concentration = _report_section(lines, "CONCENTRATION RISK DETAILS")

    for line in concentration:
        parts = [part.strip() for part in line.split("|")]

        if len(parts) >= 3 and parts[0] in {"HIGH", "MEDIUM"}:
            title = f"{parts[1]} {parts[2].lower()}"
            _append_signal(
                signals,
                "Portfolio Manager",
                "CONCENTRATION_RISK",
                "HIGH",
                title,
                line,
                "HIGH",
                "Portfolio Risk",
                {"reported_severity": parts[0], "ticker": parts[1]}
            )

    stress = _report_section(lines, "STRESS TEST SUMMARY")
    worst_scenario = _field_value(stress, "Worst Scenario")

    if worst_scenario:
        _append_signal(
            signals,
            "Portfolio Manager",
            "STRESS_TEST_RISK",
            "HIGH",
            f"Stress-test exposure: {worst_scenario}",
            "Portfolio Manager identified this as the worst stress-test "
            "exposure.",
            "HIGH",
            "Scenario Risk",
            {
                "worst_scenario": worst_scenario,
                "current_relevance": "LOW",
                "risk_timeframe": "scenario"
            }
        )

    monte_carlo = _report_section(lines, "MONTE CARLO V2 SUMMARY")
    downside = _field_value(monte_carlo, "Probability Negative")

    if downside:
        try:
            downside_value = float(downside.rstrip("%"))
        except ValueError:
            downside_value = 0

        if downside_value >= 40:
            _append_signal(
                signals,
                "Portfolio Manager",
                "MONTE_CARLO_DOWNSIDE",
                "HIGH",
                f"Monte Carlo downside probability {downside}",
                "Modeled probability of a negative outcome is elevated.",
                "MEDIUM",
                "Portfolio Risk",
                {"probability_negative": downside_value}
            )

    tax_summary = _report_section(lines, "TAX OPTIMIZATION SUMMARY")

    for label in (
        "Tax Loss Harvest Candidates",
        "Large Taxable Gain Positions"
    ):
        value = _field_value(tax_summary, label)

        if value and value != "0":
            _append_signal(
                signals,
                "Portfolio Manager",
                "TAX_RISK",
                "MEDIUM",
                f"{label}: {value}",
                "Portfolio Manager identified a tax optimization warning.",
                "HIGH",
                "Portfolio Risk",
                {"metric": label, "value": value}
            )

    committee = _report_section(lines, "INVESTMENT COMMITTEE SUMMARY")

    for label, signal_type in (
        ("Top Replacement Plan", "REPLACEMENT_CANDIDATE"),
        ("Top Capital Deployment", "DEPLOYMENT_OPPORTUNITY")
    ):
        value = _field_value(committee, label)

        if value:
            _append_signal(
                signals,
                "Portfolio Manager",
                signal_type,
                "MEDIUM",
                value,
                f"Portfolio Manager {label.lower()}.",
                "HIGH",
                "Portfolio Opportunity",
                {"source_field": label}
            )

    return signals


def build_research_signals(research):

    executive = _report_lines(research)
    full_report = _full_report_lines(research)
    signals = []
    health_issues = _report_section(full_report, "Research Health Issues:")

    for line in health_issues:
        parts = [part.strip() for part in line.split("|")]

        if len(parts) < 3 or parts[0] not in {"HIGH", "MEDIUM", "LOW"}:
            continue

        ticker = parts[1]
        issue = parts[2].removeprefix("Issue ").strip()
        recommendation = (
            parts[3].removeprefix("Recommendation ").strip()
            if len(parts) >= 4
            else issue
        )
        severity = (
            "HIGH"
            if "low conviction holding" in issue.casefold()
            else parts[0]
        )
        signal_type = (
            "LOW_CONVICTION"
            if "low conviction" in issue.casefold()
            else "RESEARCH_HEALTH_ISSUE"
        )
        _append_signal(
            signals,
            "Research Agent",
            signal_type,
            severity,
            f"{ticker}: {issue}",
            recommendation,
            "HIGH",
            "Research Gap",
            {"ticker": ticker, "reported_severity": parts[0]}
        )

    coverage = _report_section(full_report, "Coverage Summary:")

    for ticker in _field_value(coverage, "Uncovered Holdings").split(","):
        ticker = ticker.strip()

        if ticker and ticker.casefold() != "none":
            _append_signal(
                signals,
                "Research Agent",
                "UNCOVERED_HOLDING",
                "HIGH",
                f"{ticker}: Research coverage missing",
                "Holding does not have research coverage.",
                "HIGH",
                "Research Gap",
                {"ticker": ticker}
            )

    for ticker in _field_value(coverage, "Uncovered Watchlist").split(","):
        ticker = ticker.strip()

        if ticker and ticker.casefold() != "none":
            _append_signal(
                signals,
                "Research Agent",
                "UNCOVERED_WATCHLIST",
                "MEDIUM",
                f"{ticker}: Watchlist research coverage missing",
                "Watchlist candidate does not have research coverage.",
                "HIGH",
                "Research Gap",
                {"ticker": ticker}
            )

    holding_quality = _report_section(full_report, "Holding Thesis Quality:")

    for line in holding_quality:
        if "Research Status MISSING" not in line:
            continue

        ticker = line.split("|", 1)[0].strip()
        _append_signal(
            signals,
            "Research Agent",
            "MISSING_THESIS",
            "HIGH",
            f"{ticker}: Missing thesis",
            line,
            "HIGH",
            "Research Gap",
            {"ticker": ticker}
        )

    top_priority = _field_value(executive, "Top Research Priority")

    if (
        top_priority
        and "no urgent research priority" not in top_priority.casefold()
    ):
        _append_signal(
            signals,
            "Research Agent",
            "RESEARCH_HEALTH_ISSUE",
            "MEDIUM",
            top_priority,
            "Research Agent identified this as its top research priority.",
            "HIGH",
            "Research Gap",
            {"source_field": "Top Research Priority"}
        )

    return signals


def build_macro_signals(macro):

    lines = _report_lines(macro)
    signals = []
    regime = _field_value(lines, "Current Macro Regime")
    top_priority = _field_value(lines, "Top Macro Priority")
    top_reason = _field_value(lines, "Top Macro Reason")
    regime_key = regime.casefold().replace("_", " ").replace("-", " ")

    if regime:
        high_risk_regime = any(
            risk in regime_key
            for risk in ("recession", "stagflation", "inflation shock")
        ) or regime in {
            "Inflation Stress",
            "Growth Slowdown",
            "Recession Risk",
            "Liquidity Stress",
            "Rate Shock",
            "Credit Stress",
            "Energy Shock",
            "Geopolitical Macro Shock"
        }
        priority_tier = _field_value(lines, "Priority Tier")
        high_priority = (
            "Priority Tier HIGH" in top_priority
            or priority_tier == "HIGH"
        )
        _append_signal(
            signals,
            "Macro Agent",
            "MACRO_REGIME",
            "HIGH" if high_risk_regime and high_priority else (
                "MEDIUM" if high_risk_regime else "INFO"
            ),
            top_priority or f"Macro regime: {regime}",
            (
                top_reason
                if top_reason
                else "Macro Agent identified a high-risk macro regime."
                if high_risk_regime
                else "Macro Agent reported the current macro regime."
            ),
            "MEDIUM",
            "Macro Risk" if high_risk_regime else "Macro Environment",
            {"regime": regime, "top_priority": top_priority}
        )

    yield_curve = _field_value(lines, "Yield Curve")

    if "invert" in yield_curve.casefold():
        _append_signal(
            signals,
            "Macro Agent",
            "YIELD_CURVE_INVERTED",
            "HIGH",
            f"Yield curve: {yield_curve}",
            "Macro Agent identified an inverted yield curve.",
            "MEDIUM",
            "Macro Risk",
            {"yield_curve": yield_curve}
        )

    inflation = _field_value(lines, "Inflation Trend")

    if "ris" in inflation.casefold() or "accelerat" in inflation.casefold():
        _append_signal(
            signals,
            "Macro Agent",
            "INFLATION_RISING",
            "MEDIUM",
            f"Inflation trend: {inflation}",
            "Macro Agent identified rising inflation.",
            "MEDIUM",
            "Macro Risk",
            {"inflation_trend": inflation}
        )

    labor = _field_value(lines, "Labor Market")

    if any(term in labor.casefold() for term in ("weak", "deteriorat")):
        _append_signal(
            signals,
            "Macro Agent",
            "LABOR_WEAK",
            "MEDIUM",
            f"Labor market: {labor}",
            "Macro Agent identified labor-market weakness.",
            "MEDIUM",
            "Macro Risk",
            {"labor_market": labor}
        )

    policy = _field_value(lines, "Policy Rate")

    if "restrict" in policy.casefold():
        _append_signal(
            signals,
            "Macro Agent",
            "POLICY_RESTRICTIVE",
            "MEDIUM",
            f"Policy rate: {policy}",
            "Macro Agent identified restrictive monetary policy.",
            "MEDIUM",
            "Macro Risk",
            {"policy_rate": policy}
        )

    energy = _field_value(lines, "Energy")

    if "ris" in energy.casefold() or "accelerat" in energy.casefold():
        _append_signal(
            signals,
            "Macro Agent",
            "ENERGY_RISING",
            "MEDIUM",
            f"Energy trend: {energy}",
            "Macro Agent identified rising energy pressure.",
            "MEDIUM",
            "Macro Risk",
            {"energy": energy}
        )

    return signals


def build_news_signals(news):

    lines = _report_lines(news)
    signals = []
    top_narrative = _field_value(lines, "Top Market Narrative")
    supporting_articles = _field_value(lines, "Supporting Articles")
    narrative_score = _field_value(lines, "Top Narrative Score")
    representative_headline = _field_value(lines, "Representative Headline")
    narrative_reason = _field_value(lines, "Top Narrative Reason")
    high_relevance = _field_value(lines, "High Relevance Stories")

    try:
        high_relevance_count = int(high_relevance)
    except ValueError:
        high_relevance_count = 0

    try:
        supporting_article_count = int(supporting_articles)
    except ValueError:
        supporting_article_count = 0

    if top_narrative:
        _append_signal(
            signals,
            "News Agent",
            "NEWS_NARRATIVE",
            "MEDIUM",
            top_narrative,
            narrative_reason or (
                f"News Agent grouped {supporting_article_count} "
                "supporting articles into the top market narrative."
            ),
            "MEDIUM",
            "Market Event",
            {
                "narrative_title": top_narrative,
                "narrative_score": narrative_score,
                "supporting_article_count": supporting_article_count,
                "representative_headline": representative_headline,
                "high_relevance_story_count": high_relevance_count
            }
        )
    elif high_relevance_count > 0:
        top_story = _field_value(lines, "Top Market Story")
        _append_signal(
            signals,
            "News Agent",
            "HIGH_RELEVANCE_STORY",
            "MEDIUM",
            top_story or f"{high_relevance_count} high-relevance stories",
            f"News Agent identified {high_relevance_count} "
            "high-relevance stories.",
            "MEDIUM",
            "Market Event",
            {"story_count": high_relevance_count}
        )

    for label, signal_type in (
        ("Top Portfolio Story", "PORTFOLIO_NEWS"),
        ("Top World Event Story", "WORLD_EVENT"),
        ("Top Macro Story", "MACRO_NEWS")
    ):
        value = _field_value(lines, label)

        if value:
            _append_signal(
                signals,
                "News Agent",
                signal_type,
                "MEDIUM",
                value,
                f"News Agent identified this as the {label.lower()}.",
                "MEDIUM",
                "Market Event",
                {"source_field": label}
            )

    return signals


def build_registry_signals(registry):

    signals = []

    for agent in registry or []:
        agent_name = str(agent.get("agent_name") or "Unknown Agent").strip()
        last_run = str(agent.get("last_run_status") or "").strip().upper()
        health = str(agent.get("health") or "").strip().upper()
        status = str(agent.get("status") or "").strip().upper()
        failure = str(agent.get("failure_message") or "").strip()

        if last_run == "FAILED" or status == "ERROR":
            signal_type = "AGENT_FAILURE"
            severity = "HIGH"
            title = f"{agent_name} failed"
        elif status == "OFFLINE":
            signal_type = "AGENT_OFFLINE"
            severity = "HIGH"
            title = f"{agent_name} offline"
        elif health == "DEGRADED":
            signal_type = "AGENT_DEGRADED"
            severity = "MEDIUM"
            title = f"{agent_name} degraded"
        else:
            continue

        _append_signal(
            signals,
            "Agent Registry",
            signal_type,
            severity,
            title,
            failure or f"Agent Registry reports {agent_name} as {status}.",
            "HIGH",
            "Agent Health",
            {"agent_name": agent_name, "last_run_status": last_run}
        )

    return signals


def _extract_numeric_values(text, pattern):

    return [
        float(value.replace(",", ""))
        for value in re.findall(pattern, str(text or ""), flags=re.IGNORECASE)
    ]


def _extract_portfolio_allocations(portfolio):

    allocations = {}
    allocation_lines = _report_section(
        _combined_report_lines(portfolio),
        "TICKER ALLOCATION"
    )

    for line in allocation_lines:
        match = re.search(
            r"^([A-Z0-9.]+):.*?\bAllocation\s+(-?\d+(?:\.\d+)?)%",
            line
        )

        if match:
            allocations[match.group(1)] = float(match.group(2))

    return allocations


def _attach_signal_allocations(signals, allocations):

    for signal in signals:
        metadata = signal.setdefault("metadata", {})
        ticker = str(metadata.get("ticker") or "").strip().upper()

        if not ticker and signal.get("signal_type") == "REPLACEMENT_CANDIDATE":
            match = re.search(
                r"\bSell\s+([A-Z0-9.]+)\b",
                signal.get("title", ""),
                flags=re.IGNORECASE
            )
            ticker = match.group(1).upper() if match else ""

        if not ticker:
            first_token = str(signal.get("title") or "").split(":", 1)[0]
            first_token = first_token.strip().upper()
            ticker = first_token if first_token in allocations else ""

        if ticker in allocations:
            metadata["ticker"] = ticker
            metadata["allocation_percent"] = allocations[ticker]


def _threshold_score(value, thresholds):

    for threshold, score in thresholds:
        if value >= threshold:
            return score

    return 0


def _signal_magnitude(signal):

    signal_type = signal.get("signal_type", "")
    text = f"{signal.get('title', '')} {signal.get('description', '')}"
    metadata = signal.get("metadata", {})
    value = None
    unit = "none"
    score = 0
    basis = "No numeric magnitude available."

    if signal_type == "CONCENTRATION_RISK":
        percentages = _extract_numeric_values(
            text,
            r"(-?\d+(?:\.\d+)?)\s*%"
        )

        if percentages:
            value = max(percentages)
            unit = "percent"
            score = _threshold_score(
                value,
                ((40, 35), (30, 25), (25, 20), (20, 12), (15, 8))
            )
            basis = f"Concentration {value:g}%."

    elif signal_type == "STRESS_TEST_RISK":
        impacts = _extract_numeric_values(
            text,
            r"Impact\s+(-?\d+(?:\.\d+)?)\s*%"
        )
        downside = min((impact for impact in impacts if impact < 0), default=0)

        if downside:
            value = downside
            unit = "percent"
            score = _threshold_score(
                abs(downside),
                ((50, 35), (40, 28), (30, 20), (20, 12), (10, 5))
            )
            basis = f"Stress-test downside {downside:g}%."

    elif signal_type in {"LOW_CONVICTION", "RESEARCH_HEALTH_ISSUE"}:
        allocation = metadata.get("allocation_percent")

        if isinstance(allocation, (int, float)):
            value = float(allocation)
            unit = "percent"
            score = _threshold_score(
                value,
                ((20, 25), (10, 15), (5, 8), (1, 3))
            )
            basis = f"Holding allocation {value:g}%."

    elif signal_type == "TAX_RISK":
        dollar_values = _extract_numeric_values(
            text,
            r"\$\s*([\d,]+(?:\.\d+)?)"
        )
        count_values = _extract_numeric_values(
            str(metadata.get("value") or text),
            r"\b(\d+(?:\.\d+)?)\b"
        )
        dollar_value = max(dollar_values, default=0)
        count_value = max(count_values, default=0)
        dollar_score = _threshold_score(
            dollar_value,
            ((5000, 20), (2500, 12), (1000, 8), (500, 4))
        )
        count_score = _threshold_score(
            count_value,
            ((5, 8), (3, 5), (1, 2))
        )

        if dollar_score >= count_score and dollar_value:
            value = dollar_value
            unit = "dollars"
            score = dollar_score
            basis = f"Tax amount ${dollar_value:g}."
        elif count_value:
            value = count_value
            unit = "count"
            score = count_score
            basis = f"Tax item count {count_value:g}."

    elif signal_type == "DEPLOYMENT_OPPORTUNITY":
        dollar_values = _extract_numeric_values(
            text,
            r"\$\s*([\d,]+(?:\.\d+)?)"
        )

        if dollar_values:
            value = max(dollar_values)
            unit = "dollars"
            score = _threshold_score(
                value,
                ((5000, 15), (2500, 10), (1000, 6), (500, 3))
            )
            basis = f"Deployment amount ${value:g}."

    elif signal_type == "REPLACEMENT_CANDIDATE":
        allocation = metadata.get("allocation_percent")

        if isinstance(allocation, (int, float)):
            value = float(allocation)
            unit = "percent"
            score = _threshold_score(
                value,
                ((20, 20), (10, 12), (5, 6), (1, 3))
            )
            basis = f"Replacement source allocation {value:g}%."

    elif signal_type in {
        "INFLATION_RISING",
        "ENERGY_RISING",
        "YIELD_CURVE_INVERTED",
        "POLICY_RESTRICTIVE",
        "LABOR_WEAK"
    }:
        score = {
            "INFLATION_RISING": 8,
            "ENERGY_RISING": 6,
            "YIELD_CURVE_INVERTED": 12,
            "POLICY_RESTRICTIVE": 6,
            "LABOR_WEAK": 10
        }[signal_type]
        basis = f"Deterministic {signal_type.lower()} adjustment."

    elif signal_type == "MACRO_REGIME":
        regime = str(metadata.get("regime") or text).casefold()
        score = (
            15
            if any(
                term in regime
                for term in ("recession", "stagflation", "inflation shock")
            )
            else 3
        )
        basis = "High-risk macro regime." if score == 15 else (
            "Standard macro regime."
        )

    elif signal_type in {
        "HIGH_RELEVANCE_STORY",
        "PORTFOLIO_NEWS",
        "MACRO_NEWS",
        "WORLD_EVENT"
    }:
        score = {
            "HIGH_RELEVANCE_STORY": 5,
            "PORTFOLIO_NEWS": 6,
            "MACRO_NEWS": 5,
            "WORLD_EVENT": 7
        }[signal_type]
        basis = f"Deterministic {signal_type.lower()} adjustment."

    return value, unit, score, basis


def apply_signal_magnitude(signal):

    normalized = normalize_signal(
        signal.get("source_agent"),
        signal.get("signal_type"),
        signal.get("severity"),
        signal.get("title"),
        signal.get("description"),
        signal.get("confidence"),
        signal.get("category"),
        signal.get("metadata")
    )

    if normalized is None:
        return None

    value, unit, magnitude_score, basis = _signal_magnitude(normalized)
    normalized["magnitude_value"] = value
    normalized["magnitude_unit"] = unit
    normalized["magnitude_score"] = magnitude_score
    normalized["magnitude_basis"] = basis
    normalized["weighted_score"] = get_signal_weight(normalized)
    normalized["magnitude_adjusted_score"] = (
        normalized["weighted_score"] + magnitude_score
    )

    return normalized


def deduplicate_signals(signals):

    unique_signals = {}

    for signal in signals or []:
        if not isinstance(signal, dict):
            continue

        normalized = normalize_signal(
            signal.get("source_agent"),
            signal.get("signal_type"),
            signal.get("severity"),
            signal.get("title"),
            signal.get("description"),
            signal.get("confidence"),
            signal.get("category"),
            signal.get("metadata"),
            signal.get("magnitude_value"),
            signal.get("magnitude_unit", "none"),
            signal.get("magnitude_score", 0),
            signal.get("magnitude_basis", "No magnitude adjustment.")
        )

        if normalized is None:
            continue

        key = (
            normalized["source_agent"].casefold(),
            normalized["signal_type"],
            normalized["title"].casefold().rstrip(".")
        )
        current = unique_signals.get(key)

        if current is None or normalized["score"] > current["score"]:
            unique_signals[key] = normalized

    return list(unique_signals.values())


def rank_signals(signals):

    return sorted(
        deduplicate_signals(signals),
        key=lambda signal: (
            -signal["score"],
            PRIORITY_AGENT_RANKS.get(signal["source_agent"], 99),
            signal["title"].casefold()
        )
    )


def build_agent_signals(portfolio, research, macro, news, registry):

    signals = (
        build_portfolio_signals(portfolio)
        + build_research_signals(research)
        + build_macro_signals(macro)
        + build_news_signals(news)
        + build_registry_signals(registry)
    )
    _attach_signal_allocations(
        signals,
        _extract_portfolio_allocations(portfolio)
    )

    return rank_weighted_signals(signals)


def build_agent_signal_bus_report(signals):

    ranked_signals = rank_signals(signals)
    severity_counts = {
        severity: sum(
            signal["severity"] == severity
            for signal in ranked_signals
        )
        for severity in PRIORITY_SEVERITY_SCORES
    }
    emitting_agents = {
        signal["source_agent"]
        for signal in ranked_signals
    }
    summary = [
        "Signal Bus Status: ACTIVE",
        f"Total Signals: {len(ranked_signals)}",
        f"Critical Signals: {severity_counts['CRITICAL']}",
        f"High Signals: {severity_counts['HIGH']}",
        f"Medium Signals: {severity_counts['MEDIUM']}",
        f"Low Signals: {severity_counts['LOW']}",
        f"Info Signals: {severity_counts['INFO']}",
        f"Agents Emitting Signals: {len(emitting_agents)}",
        "",
        (
            "Agent Signal Bus normalizes agent outputs into structured "
            "internal signals."
        )
    ]
    details = []

    for number, signal in enumerate(ranked_signals[:15], start=1):
        details.extend([
            f"{number}. {signal['title']}",
            f"   Source: {signal['source_agent']}",
            f"   Type: {signal['signal_type']}",
            f"   Severity: {signal['severity']}",
            f"   Confidence: {signal['confidence']}",
            f"   Category: {signal['category']}",
            f"   Description: {signal['description']}",
            ""
        ])

    if not details:
        details.append("No agent signals available.")

    return {
        "summary": summary,
        "details": details,
        "signals": ranked_signals
    }


def get_signal_weight(signal):

    if not isinstance(signal, dict):
        return 0

    return (
        signal.get("score", 0)
        + SIGNAL_SOURCE_WEIGHTS.get(signal.get("source_agent"), 0)
        + SIGNAL_CONFIDENCE_WEIGHTS.get(signal.get("confidence"), 0)
        + SIGNAL_CATEGORY_WEIGHTS.get(signal.get("category"), 0)
    )


def rank_weighted_signals(signals):

    weighted_signals = []

    for signal in rank_signals(signals):
        weighted_signal = apply_signal_magnitude(signal)

        if weighted_signal is not None:
            weighted_signals.append(weighted_signal)

    return sorted(
        weighted_signals,
        key=lambda signal: (
            -signal["magnitude_adjusted_score"],
            -signal["score"],
            PRIORITY_AGENT_RANKS.get(signal["source_agent"], 99),
            -signal["magnitude_score"],
            signal["title"].casefold()
        )
    )


def select_signal_by_category(signals, categories):

    categories = set(categories or ())

    return next(
        (
            signal for signal in rank_weighted_signals(signals)
            if signal.get("category") in categories
        ),
        None
    )


def _dominant_signal_value(signals, field):

    counts = {}

    for signal in signals:
        value = signal.get(field)

        if value:
            counts[value] = counts.get(value, 0) + 1

    if not counts:
        return "None"

    highest_count = max(counts.values())
    tied_values = {
        value for value, count in counts.items()
        if count == highest_count
    }

    return next(
        signal[field]
        for signal in signals
        if signal.get(field) in tied_values
    )


def build_signal_weighting_report(signals):

    weighted_signals = rank_weighted_signals(signals)
    highest = weighted_signals[0] if weighted_signals else None
    dominant_category = _dominant_signal_value(
        weighted_signals,
        "category"
    )
    dominant_source = _dominant_signal_value(
        weighted_signals,
        "source_agent"
    )
    summary = [
        (
            f"Highest Weighted Signal: {highest['title']}"
            if highest
            else "Highest Weighted Signal: None"
        ),
        (
            f"Source: {highest['source_agent']}"
            if highest
            else "Source: None"
        ),
        (
            f"Weighted Score: {highest['weighted_score']}"
            if highest
            else "Weighted Score: 0"
        ),
        f"Dominant Category: {dominant_category}",
        f"Dominant Source Agent: {dominant_source}",
        "",
        (
            "Signal weighting is deterministic and used to drive Echo "
            "Executive Summary."
        )
    ]
    details = [
        (
            f"{number}. {signal['title']} | "
            f"Source {signal['source_agent']} | "
            f"Category {signal['category']} | "
            f"Severity {signal['severity']} | "
            f"Base Score {signal['score']} | "
            f"Weighted Score {signal['weighted_score']}"
        )
        for number, signal in enumerate(weighted_signals[:10], start=1)
    ]

    if not details:
        details.append("No weighted signals available.")

    return {
        "summary": summary,
        "details": details,
        "signals": weighted_signals
    }


def _signal_theme_titles(signal):

    title = str(signal.get("title") or "")
    description = str(signal.get("description") or "")
    signal_type = str(signal.get("signal_type") or "")
    category = str(signal.get("category") or "")
    metadata = signal.get("metadata") or {}
    metadata_text = " ".join(
        str(value)
        for value in metadata.values()
        if value is not None
    )
    text = " ".join(
        (title, description, signal_type, category, metadata_text)
    ).casefold()
    themes = []

    inflation_energy_terms = any(
        term in text
        for term in (
            "inflation",
            "energy",
            "oil",
            "crude",
            "iran",
            "hormuz",
            "middle east",
            "vnom",
            "eco"
        )
    )
    inflation_energy_context = (
        category == "Macro Risk"
        or (
            category == "Market Event"
            and signal_type in {"NEWS_NARRATIVE", "WORLD_EVENT"}
        )
        or (
            category in {"Portfolio Risk", "Portfolio Opportunity"}
            and any(term in text for term in ("energy", "commodity", "vnom", "eco"))
        )
    )

    if inflation_energy_terms and inflation_energy_context:
        themes.append("Inflation/Energy Risk")

    rates_terms = any(
        term in text
        for term in (
            "fed",
            "federal reserve",
            "fomc",
            "powell",
            "warsh",
            "rate",
            "rates",
            "yield",
            "treasury"
        )
    )
    rates_context = category in {
        "Macro Risk",
        "Macro Environment",
        "Market Event",
        "Portfolio Risk"
    }

    if rates_terms and rates_context:
        themes.append("Fed/Rates Risk")

    recession_terms = any(
        term in text
        for term in (
            "recession",
            "growth slowdown",
            "slowdown",
            "labor",
            "unemployment",
            "yield curve",
            "stress-test"
        )
    )
    recession_context = (
        category in {"Macro Risk", "Portfolio Risk"}
        or signal_type in {"STRESS_TEST_RISK", "LABOR_WEAK"}
    )

    if recession_terms and recession_context:
        themes.append("Recession/Growth Slowdown Risk")

    if (
        category == "Portfolio Risk"
        and any(
            term in text
            for term in ("concentration", "overweight", "stress-test")
        )
    ):
        themes.append("Portfolio Concentration Risk")

    if category == "Research Gap" or any(
        term in text
        for term in ("low conviction", "missing thesis", "research")
    ):
        themes.append("Research Quality Risk")

    if any(
        term in text
        for term in (
            "tax",
            "capital deployment",
            "deployment",
            "replacement",
            "buy",
            "sell"
        )
    ):
        themes.append("Tax/Capital Deployment Theme")

    if category == "Market Event" or any(
        term in text
        for term in ("sec", "doj", "regulatory", "antitrust", "lawsuit")
    ):
        themes.append("Market/Regulatory Event Theme")

    if (
        category in {"Agent Health", "System Infrastructure"}
        or signal_type in {"AGENT_FAILURE", "AGENT_OFFLINE"}
        or any(term in text for term in ("offline", "failed", "system"))
    ):
        themes.append("Agent Health/System Theme")

    ordered_unique = []

    for theme in THEME_TITLE_ORDER:
        if theme in themes:
            ordered_unique.append(theme)

    return ordered_unique


def _theme_strength(score):

    if score >= 100:
        return "CRITICAL"

    if score >= 85:
        return "HIGH"

    if score >= 65:
        return "MEDIUM"

    return "LOW"


def _theme_reason(theme):

    agents = ", ".join(theme["supporting_agents"]) or "none"
    return (
        f"{theme['theme_title']} links "
        f"{theme['supporting_signal_count']} signals across "
        f"{len(theme['supporting_agents'])} agent(s): {agents}."
    )


def _theme_sort_key(theme):

    return (
        -theme["theme_score"],
        THEME_TITLE_ORDER.index(theme["theme_title"]),
        theme["theme_title"].casefold()
    )


def build_cross_agent_theme_clusters(signals):

    weighted_signals = rank_weighted_signals(signals)
    grouped_signals = {
        theme_title: []
        for theme_title in THEME_TITLE_ORDER
    }

    for signal in weighted_signals:
        for theme_title in _signal_theme_titles(signal):
            grouped_signals[theme_title].append(signal)

    themes = []

    for theme_title in THEME_TITLE_ORDER:
        supporting_signals = grouped_signals[theme_title]

        if not supporting_signals:
            continue

        supporting_agents = sorted({
            signal["source_agent"]
            for signal in supporting_signals
        })
        highest_score = max(
            signal["magnitude_adjusted_score"]
            for signal in supporting_signals
        )
        highest_severity = max(
            THEME_SEVERITY_WEIGHTS.get(signal["severity"], 0)
            for signal in supporting_signals
        )
        agent_bonus = min(18, max(0, len(supporting_agents) - 1) * 9)
        signal_bonus = min(15, max(0, len(supporting_signals) - 1) * 3)
        category_bonus = THEME_CATEGORY_IMPORTANCE[theme_title]
        theme_score = min(
            100,
            highest_score
            + agent_bonus
            + signal_bonus
            + highest_severity
            + category_bonus
        )
        theme = {
            "theme_title": theme_title,
            "theme_strength": _theme_strength(theme_score),
            "theme_score": theme_score,
            "supporting_agents": supporting_agents,
            "supporting_signal_count": len(supporting_signals),
            "supporting_signals": supporting_signals,
            "theme_reason": ""
        }
        theme["theme_reason"] = _theme_reason(theme)
        themes.append(theme)

    return sorted(themes, key=_theme_sort_key)


def build_cross_agent_theme_report(signals):

    themes = build_cross_agent_theme_clusters(signals)
    dominant = themes[0] if themes else None
    summary = [
        "Theme Synthesis Status: ACTIVE",
        f"Theme Count: {len(themes)}",
        (
            f"Dominant Theme: {dominant['theme_title']}"
            if dominant
            else "Dominant Theme: None"
        ),
        (
            f"Dominant Theme Score: {dominant['theme_score']}"
            if dominant
            else "Dominant Theme Score: 0"
        ),
        (
            f"Dominant Theme Strength: {dominant['theme_strength']}"
            if dominant
            else "Dominant Theme Strength: LOW"
        ),
        (
            f"Dominant Theme Reason: {dominant['theme_reason']}"
            if dominant
            else "Dominant Theme Reason: No cross-agent themes detected."
        ),
        "",
        (
            "Theme synthesis groups existing normalized signals and does "
            "not replace priority ranking."
        )
    ]
    details = []

    for number, theme in enumerate(themes[:8], start=1):
        details.extend([
            f"{number}. {theme['theme_title']}",
            f"   Theme Strength: {theme['theme_strength']}",
            f"   Theme Score: {theme['theme_score']}",
            (
                "   Supporting Agents: "
                f"{', '.join(theme['supporting_agents']) or 'None'}"
            ),
            (
                "   Supporting Signal Count: "
                f"{theme['supporting_signal_count']}"
            ),
            f"   Theme Reason: {theme['theme_reason']}",
            "   Supporting Signals:"
        ])

        for signal in theme["supporting_signals"][:8]:
            details.append(
                f"   - {signal['source_agent']} | "
                f"{signal['signal_type']} | "
                f"{signal['severity']} | "
                f"{signal['title']}"
            )

        details.append("")

    if not details:
        details.append("No cross-agent themes detected.")

    return {
        "summary": summary,
        "details": details,
        "themes": themes
    }


def _unique_preserve_order(items):

    unique_items = []
    seen = set()

    for item in items:
        value = str(item or "").strip()

        if not value:
            continue

        key = value.casefold()

        if key not in seen:
            unique_items.append(value)
            seen.add(key)

    return unique_items


def _extract_portfolio_context(portfolio):

    lines = _combined_report_lines(portfolio)
    allocations = _extract_portfolio_allocations(portfolio)
    classifications = {}
    allocation_details = {}
    allocation_targets = {}
    concentration = []
    exposure_details = []
    factor_details = []
    low_conviction = []
    overweight_holdings = []
    taxable_positions = []
    portfolio_health = _field_value(lines, "Portfolio Health") or "UNKNOWN"
    regime_summary = _report_section(lines, "MACRO REGIME SUMMARY")
    alignment_summary = _report_section(lines, "REGIME ALIGNMENT SUMMARY")
    portfolio_regime = ""
    regime_alignment = ""

    for source_lines in (regime_summary, alignment_summary):
        for line in source_lines:
            regime_match = re.search(
                r"Current Regime:\s*([^|]+)",
                line,
                flags=re.IGNORECASE
            )

            if regime_match and not portfolio_regime:
                portfolio_regime = regime_match.group(1).strip()

            alignment_match = re.search(
                r"(?:Alignment Level|Portfolio Alignment):\s*([^|]+)",
                line,
                flags=re.IGNORECASE
            )

            if alignment_match and not regime_alignment:
                regime_alignment = alignment_match.group(1).strip()

    for line in _report_section(lines, "SECURITY CLASSIFICATION"):
        match = re.search(
            (
                r"^([A-Z0-9.]+)\s+\|\s+Asset Class\s+([^|]+?)\s+\|\s+"
                r"Security Type\s+([^|]+?)\s+\|\s+Risk Bucket\s+([^|]+)"
            ),
            line,
            flags=re.IGNORECASE
        )

        if match:
            ticker = match.group(1).upper()
            classifications[ticker] = {
                "asset_class": match.group(2).strip().casefold(),
                "security_type": match.group(3).strip().casefold(),
                "risk_bucket": match.group(4).strip().casefold()
            }

    for line in _report_section(lines, "TICKER ALLOCATION"):
        match = re.search(
            (
                r"^([A-Z0-9.]+):.*?\bAllocation\s+"
                r"(-?\d+(?:\.\d+)?)%\s+\|\s+Target\s+"
                r"(-?\d+(?:\.\d+)?)%\s+\|\s+Difference\s+"
                r"(-?\d+(?:\.\d+)?)%"
            ),
            line,
            flags=re.IGNORECASE
        )

        if match:
            ticker = match.group(1).upper()
            allocation_targets[ticker] = {
                "allocation": float(match.group(2)),
                "target": float(match.group(3)),
                "difference": float(match.group(4))
            }

    for line in _report_section(lines, "REBALANCE ALERTS"):
        match = re.search(
            r"^([A-Z0-9.]+):\s+OVERWEIGHT\b",
            line,
            flags=re.IGNORECASE
        )

        if match:
            overweight_holdings.append(match.group(1).upper())

    for line in lines:
        match = re.search(
            (
                r"^([A-Z0-9.]+)\s+\|\s+Allocation\s+"
                r"(-?\d+(?:\.\d+)?)%\s+\|\s+Asset Class\s+"
                r"([^|]+?)\s+\|\s+Factor\s+([^|]+?)\s+\|"
            ),
            line,
            flags=re.IGNORECASE
        )

        if match:
            ticker = match.group(1).upper()
            allocation_details[ticker] = {
                "allocation": float(match.group(2)),
                "asset_class": match.group(3).strip().casefold(),
                "factors": [
                    factor.strip().casefold()
                    for factor in match.group(4).split(",")
                    if factor.strip()
                ]
            }

    for line in _report_section(lines, "CONCENTRATION RISK DETAILS"):
        parts = [part.strip() for part in line.split("|")]

        if len(parts) >= 3 and parts[0] in {"HIGH", "MEDIUM", "LOW"}:
            concentration.append({
                "severity": parts[0],
                "ticker": parts[1].upper(),
                "detail": parts[2]
            })

    for line in _report_section(lines, "EXPOSURE DETAILS"):
        match = re.search(r"^([^:]+):\s+(-?\d+(?:\.\d+)?)%", line)

        if match:
            exposure_details.append({
                "name": match.group(1).strip(),
                "allocation": float(match.group(2))
            })

    for line in _report_section(lines, "FACTOR EXPOSURE DETAILS"):
        match = re.search(r"^([^:]+):\s+(-?\d+(?:\.\d+)?)%", line)

        if match:
            factor_details.append({
                "name": match.group(1).strip(),
                "allocation": float(match.group(2))
            })

    research_health_lines = (
        _report_section(lines, "RESEARCH HEALTH DETAILS")
        + _report_section(lines, "RESEARCH HEALTH")
    )

    for line in research_health_lines:
        parts = [part.strip() for part in line.split("|")]

        if len(parts) >= 3 and "low conviction" in line.casefold():
            low_conviction.append(parts[1].upper())

    for line in _report_section(lines, "TAX OPTIMIZATION DETAILS"):
        parts = [part.strip() for part in line.split("|")]

        if len(parts) >= 2:
            ticker = parts[0].upper()
            account_type = parts[1].casefold()

            if ticker in allocations and account_type == "taxable":
                taxable_positions.append(ticker)

    return {
        "allocations": allocations,
        "classifications": classifications,
        "allocation_details": allocation_details,
        "allocation_targets": allocation_targets,
        "concentration": concentration,
        "exposure_details": exposure_details,
        "factor_details": factor_details,
        "low_conviction": _unique_preserve_order(low_conviction),
        "overweight_holdings": _unique_preserve_order(overweight_holdings),
        "taxable_positions": _unique_preserve_order(taxable_positions),
        "portfolio_health": portfolio_health,
        "portfolio_regime": portfolio_regime,
        "regime_alignment": regime_alignment
    }


def _holding_allocation(context, ticker):

    ticker = str(ticker or "").upper()
    detail = context["allocation_details"].get(ticker, {})
    allocation = detail.get("allocation")

    if isinstance(allocation, (int, float)):
        return float(allocation)

    return float(context["allocations"].get(ticker, 0))


def _holdings_by_context(context, asset_classes=(), factors=(),
                         risk_buckets=()):

    asset_classes = {value.casefold() for value in asset_classes}
    factors = {value.casefold() for value in factors}
    risk_buckets = {value.casefold() for value in risk_buckets}
    tickers = []

    for ticker in sorted(context["allocations"]):
        classification = context["classifications"].get(ticker, {})
        detail = context["allocation_details"].get(ticker, {})
        asset_class = (
            detail.get("asset_class")
            or classification.get("asset_class")
            or ""
        )
        holding_factors = set(detail.get("factors") or [])
        risk_bucket = classification.get("risk_bucket") or ""
        matches_asset = asset_class in asset_classes if asset_classes else False
        matches_factor = bool(holding_factors & factors) if factors else False
        matches_risk = risk_bucket in risk_buckets if risk_buckets else False

        if matches_asset or matches_factor or matches_risk:
            tickers.append(ticker)

    return sorted(
        tickers,
        key=lambda ticker: (-_holding_allocation(context, ticker), ticker)
    )


def _matching_exposures(context, names):

    wanted = tuple(name.casefold() for name in names)
    matches = []

    for exposure in context["exposure_details"]:
        exposure_name = exposure["name"]

        if any(name in exposure_name.casefold() for name in wanted):
            matches.append(
                f"{exposure_name} {exposure['allocation']:g}%"
            )

    return matches


def _matching_factors(context, names):

    wanted = tuple(name.casefold() for name in names)
    matches = []

    for factor in context["factor_details"]:
        factor_name = factor["name"]

        if any(name in factor_name.casefold() for name in wanted):
            matches.append(f"{factor_name} {factor['allocation']:g}%")

    return matches


def _signal_tickers(signals):

    tickers = []

    for signal in signals or []:
        metadata = signal.get("metadata") or {}
        ticker = str(metadata.get("ticker") or "").strip().upper()

        if ticker:
            tickers.append(ticker)

        text = f"{signal.get('title', '')} {signal.get('description', '')}"
        tickers.extend(re.findall(r"\b[A-Z][A-Z0-9.]{1,5}\b", text))

    return _unique_preserve_order(tickers)


def _theme_impact_tier(theme, impacted_holdings, impacted_exposures,
                       impacted_factors):

    score = theme.get("theme_score", 0)
    breadth = (
        len(impacted_holdings)
        + len(impacted_exposures)
        + len(impacted_factors)
    )

    if score >= 95 and breadth >= 2:
        return "CRITICAL"

    if score >= 80 and breadth >= 1:
        return "HIGH"

    if score >= 60:
        return "MEDIUM"

    return "LOW"


def _theme_impact_reason(theme_title, impacted_holdings, impacted_exposures,
                         impacted_factors):

    holding_text = (
        "/".join(impacted_holdings[:4])
        if impacted_holdings
        else "no specific holdings"
    )
    exposure_text = (
        ", ".join(impacted_exposures[:3])
        if impacted_exposures
        else "no direct exposure bucket"
    )
    factor_text = (
        ", ".join(impacted_factors[:3])
        if impacted_factors
        else "no direct factor bucket"
    )

    return (
        f"{theme_title} maps to {holding_text}; exposure link: "
        f"{exposure_text}; factor link: {factor_text}."
    )


def _map_theme_to_portfolio_impact(theme, signals, context):

    theme_title = theme["theme_title"]
    supporting_signals = theme.get("supporting_signals", [])
    impacted_holdings = []
    impacted_exposures = []
    impacted_factors = []

    if theme_title == "Inflation/Energy Risk":
        impacted_holdings.extend(
            _holdings_by_context(
                context,
                asset_classes=("commodity",),
                factors=("commodity",)
            )
        )
        impacted_holdings.extend(
            ticker
            for ticker in ("VNOM", "ECO")
            if ticker in context["allocations"]
        )
        impacted_exposures.extend(
            _matching_exposures(context, ("commodity", "energy"))
        )
        impacted_exposures.append("Energy-linked exposure")
        impacted_factors.extend(_matching_factors(context, ("commodity",)))
        impacted_factors.extend(_matching_factors(context, ("growth",)))

    elif theme_title == "Fed/Rates Risk":
        impacted_holdings.extend(
            _holdings_by_context(
                context,
                asset_classes=("bitcoin",),
                factors=("growth", "bitcoin")
            )
        )
        impacted_holdings.extend(
            ticker
            for ticker in ("SMCI", "IBIT", "SCHG", "UNH")
            if ticker in context["allocations"]
        )
        impacted_exposures.extend(
            _matching_exposures(context, ("equity", "bitcoin"))
        )
        impacted_exposures.append("Long-duration equity")
        impacted_factors.extend(
            _matching_factors(context, ("growth", "bitcoin"))
        )

    elif theme_title == "Recession/Growth Slowdown Risk":
        impacted_holdings.extend(
            _holdings_by_context(
                context,
                asset_classes=("equity", "bitcoin"),
                risk_buckets=("high", "speculative")
            )
        )
        impacted_exposures.extend(
            _matching_exposures(context, ("equity", "bitcoin"))
        )
        impacted_factors.extend(
            _matching_factors(context, ("growth", "small", "bitcoin"))
        )

    elif theme_title == "Portfolio Concentration Risk":
        impacted_holdings.extend(
            item["ticker"]
            for item in context["concentration"]
            if item["severity"] in {"HIGH", "MEDIUM"}
        )
        impacted_exposures.extend(
            _matching_exposures(context, ("equity",))
        )
        impacted_exposures.append("Top 3 concentration")
        impacted_factors.extend(_matching_factors(context, ("growth",)))

    elif theme_title == "Research Quality Risk":
        impacted_holdings.extend(context["low_conviction"])
        impacted_holdings.extend(
            ticker
            for ticker in _signal_tickers(supporting_signals)
            if ticker in context["allocations"]
        )
        impacted_exposures.append("Low-conviction holdings")
        impacted_factors.extend(
            _matching_factors(context, ("growth", "commodity", "bitcoin"))
        )

    elif theme_title == "Tax/Capital Deployment Theme":
        impacted_holdings.extend(context["taxable_positions"])
        impacted_holdings.extend(
            ticker
            for ticker in _signal_tickers(supporting_signals)
            if ticker in context["allocations"]
        )
        impacted_exposures.extend(("Taxable account", "Available cash"))

    elif theme_title == "Market/Regulatory Event Theme":
        impacted_holdings.extend(
            ticker
            for ticker in _signal_tickers(supporting_signals)
            if ticker in context["allocations"]
        )
        impacted_exposures.extend(
            _matching_exposures(context, ("equity", "bitcoin", "commodity"))
        )

    elif theme_title == "Agent Health/System Theme":
        impacted_exposures.extend(("Report reliability", "Monitoring coverage"))

    impacted_holdings = _unique_preserve_order(impacted_holdings)
    impacted_exposures = _unique_preserve_order(impacted_exposures)
    impacted_factors = _unique_preserve_order(impacted_factors)
    impact_tier = _theme_impact_tier(
        theme,
        impacted_holdings,
        impacted_exposures,
        impacted_factors
    )

    return {
        "theme_title": theme_title,
        "theme_score": theme.get("theme_score", 0),
        "impacted_holdings": impacted_holdings,
        "impacted_exposures": impacted_exposures,
        "impacted_factors": impacted_factors,
        "risk_channel": THEME_RISK_CHANNELS.get(
            theme_title,
            "portfolio sensitivity, risk appetite, valuation"
        ),
        "impact_reason": _theme_impact_reason(
            theme_title,
            impacted_holdings,
            impacted_exposures,
            impacted_factors
        ),
        "impact_tier": impact_tier
    }


def build_theme_impact_map(themes, signals, portfolio):

    context = _extract_portfolio_context(portfolio)
    impacts = [
        _map_theme_to_portfolio_impact(theme, signals, context)
        for theme in themes or []
    ]

    return sorted(
        impacts,
        key=lambda impact: (
            -impact["theme_score"],
            THEME_TITLE_ORDER.index(impact["theme_title"]),
            impact["theme_title"].casefold()
        )
    )


def _theme_impact_summary(impact):

    if not impact:
        return "No theme-to-portfolio impact mapping available."

    theme_title = impact["theme_title"]
    holdings = impact["impacted_holdings"]
    exposures = impact["impacted_exposures"]
    factors = impact["impacted_factors"]

    if holdings and factors:
        return (
            f"{theme_title} touches {'/'.join(holdings[:3])} directly "
            f"and {', '.join(factors[:2])} indirectly."
        )

    if holdings:
        return (
            f"{theme_title} touches {'/'.join(holdings[:4])} through "
            f"{impact['risk_channel']}."
        )

    if exposures:
        return (
            f"{theme_title} maps mainly to {', '.join(exposures[:3])}."
        )

    return f"{theme_title} has no direct mapped portfolio exposure."


def build_theme_impact_report(themes, signals, portfolio):

    impacts = build_theme_impact_map(themes, signals, portfolio)
    dominant = impacts[0] if impacts else None
    summary = [
        "Theme Impact Mapping Status: ACTIVE",
        f"Mapped Themes: {len(impacts)}",
        (
            f"Dominant Theme Impact: {_theme_impact_summary(dominant)}"
            if dominant
            else "Dominant Theme Impact: None"
        ),
        (
            f"Dominant Impact Tier: {dominant['impact_tier']}"
            if dominant
            else "Dominant Impact Tier: LOW"
        ),
        "",
        (
            "Theme impact mapping connects deterministic cross-agent "
            "themes to existing portfolio holdings, exposures, factors, "
            "and concentration details."
        )
    ]
    details = []

    for number, impact in enumerate(impacts[:8], start=1):
        details.extend([
            f"{number}. {impact['theme_title']}",
            f"   Theme Score: {impact['theme_score']}",
            f"   Impact Tier: {impact['impact_tier']}",
            (
                "   Impacted Holdings: "
                f"{', '.join(impact['impacted_holdings']) or 'None'}"
            ),
            (
                "   Impacted Exposures: "
                f"{', '.join(impact['impacted_exposures']) or 'None'}"
            ),
            (
                "   Impacted Factors: "
                f"{', '.join(impact['impacted_factors']) or 'None'}"
            ),
            f"   Risk Channel: {impact['risk_channel']}",
            f"   Impact Reason: {impact['impact_reason']}",
            ""
        ])

    if not details:
        details.append("No theme impact mappings detected.")

    return {
        "summary": summary,
        "details": details,
        "impacts": impacts
    }


def _theme_titles(themes):

    return {
        str(theme.get("theme_title") or "")
        for theme in themes or []
    }


def _dominant_factor(context):

    if not context["factor_details"]:
        return None

    return sorted(
        context["factor_details"],
        key=lambda factor: (-factor["allocation"], factor["name"].casefold())
    )[0]


def _macro_conflict_regimes(macro, signals):

    lines = _report_lines(macro)
    text = "\n".join(lines).casefold()
    regimes = []

    for label, terms in (
        ("Inflation Stress", ("inflation stress", "inflation shock")),
        ("Recession Risk", ("recession risk", "recession")),
        ("Rate Shock", ("rate shock", "policy restrictive")),
        ("Growth Slowdown", ("growth slowdown", "labor weak")),
        ("Energy Shock", ("energy shock", "energy rising"))
    ):
        if any(term in text for term in terms):
            regimes.append(label)

    for signal in signals or []:
        if signal.get("source_agent") != "Macro Agent":
            continue

        signal_type = signal.get("signal_type")
        metadata = signal.get("metadata") or {}
        regime_text = " ".join(
            str(value)
            for value in (
                signal.get("title"),
                signal.get("description"),
                metadata.get("regime")
            )
            if value
        ).casefold()

        if "inflation stress" in regime_text or signal_type == "INFLATION_RISING":
            regimes.append("Inflation Stress")
        if "recession" in regime_text:
            regimes.append("Recession Risk")
        if "rate shock" in regime_text or signal_type == "POLICY_RESTRICTIVE":
            regimes.append("Rate Shock")
        if "growth slowdown" in regime_text or signal_type == "LABOR_WEAK":
            regimes.append("Growth Slowdown")
        if "energy shock" in regime_text or signal_type == "ENERGY_RISING":
            regimes.append("Energy Shock")

    return _unique_preserve_order(regimes)


def _news_energy_easing(news):

    text = "\n".join(_report_lines(news)).casefold()
    easing_terms = (
        "oil dips",
        "oil falling",
        "oil falls",
        "brent oil dips",
        "hormuz crisis eases",
        "crisis eases",
        "gas prices will come down",
        "gas prices may drop",
        "deal to end",
        "peace agreement"
    )

    return any(term in text for term in easing_terms)


def _has_energy_rising(signals, macro):

    if any(
        signal.get("source_agent") == "Macro Agent"
        and signal.get("signal_type") == "ENERGY_RISING"
        for signal in signals or []
    ):
        return True

    return "energy rising" in "\n".join(_report_lines(macro)).casefold()


def _conflict_sort_key(conflict):

    severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    return (
        severity_rank.get(conflict["conflict_severity"], 9),
        conflict["conflict_title"].casefold()
    )


def _append_conflict(conflicts, title, conflict_type, severity,
                     affected_holdings, evidence, reason, review_area):

    conflicts.append({
        "conflict_title": title,
        "conflict_type": conflict_type,
        "conflict_severity": severity,
        "affected_holdings": _unique_preserve_order(affected_holdings),
        "evidence": _unique_preserve_order(evidence),
        "conflict_reason": reason,
        "suggested_review_area": review_area
    })


def build_theme_conflict_report(themes, theme_impacts, signals, portfolio,
                                macro, news):

    context = _extract_portfolio_context(portfolio)
    theme_titles = _theme_titles(themes)
    theme_titles.update(
        str(impact.get("theme_title") or "")
        for impact in theme_impacts or []
    )
    conflicts = []
    macro_risk_regimes = _macro_conflict_regimes(macro, signals)
    portfolio_regime = context.get("portfolio_regime", "")
    dominant_factor = _dominant_factor(context)
    growth_factor = next(
        (
            factor for factor in context["factor_details"]
            if factor["name"].casefold() == "growth"
        ),
        None
    )

    if (
        macro_risk_regimes
        and portfolio_regime.casefold() in {"expansion", "disinflation"}
    ):
        severity = (
            "HIGH"
            if any(
                regime in macro_risk_regimes
                for regime in ("Inflation Stress", "Recession Risk",
                               "Rate Shock", "Energy Shock")
            )
            else "MEDIUM"
        )
        _append_conflict(
            conflicts,
            "Macro regime risk conflicts with portfolio regime posture",
            "Macro/Portfolio Regime Conflict",
            severity,
            [],
            [
                f"Macro risk regimes: {', '.join(macro_risk_regimes)}",
                f"Portfolio regime: {portfolio_regime}"
            ],
            (
                "Macro signals point to a risk regime while portfolio "
                "classification remains aligned with expansion or "
                "disinflation."
            ),
            "Review macro regime assumptions against portfolio positioning."
        )

    if (
        growth_factor
        and growth_factor["allocation"] >= 50
        and theme_titles & {"Inflation/Energy Risk", "Fed/Rates Risk"}
    ):
        affected_holdings = _holdings_by_context(
            context,
            factors=("growth",),
            asset_classes=("bitcoin",)
        )
        severity = (
            "HIGH"
            if dominant_factor
            and dominant_factor["name"].casefold() == "growth"
            else "MEDIUM"
        )
        _append_conflict(
            conflicts,
            "Growth exposure conflicts with inflation/rates theme",
            "Growth Exposure vs Inflation/Rates Conflict",
            severity,
            affected_holdings,
            [
                f"Growth factor exposure {growth_factor['allocation']:g}%",
                (
                    "Active themes: "
                    f"{', '.join(sorted(theme_titles & {'Inflation/Energy Risk', 'Fed/Rates Risk'}))}"
                )
            ],
            (
                "High growth exposure is sensitive to discount-rate "
                "pressure when inflation, energy, or rates themes are active."
            ),
            "Review growth and rates-sensitive exposure."
        )

    if _has_energy_rising(signals, macro) and _news_energy_easing(news):
        _append_conflict(
            conflicts,
            "Energy macro direction conflicts with easing news narrative",
            "Energy News vs Energy Macro Direction Conflict",
            "LOW",
            _holdings_by_context(
                context,
                asset_classes=("commodity",),
                factors=("commodity",)
            ),
            [
                "Macro indicates energy rising.",
                "News narrative includes oil, gas, Hormuz, or Iran easing."
            ],
            (
                "Macro energy direction and news narrative point in "
                "different directions, which is directional tension rather "
                "than an agent error."
            ),
            "Monitor energy data against the latest news narrative."
        )

    for ticker in context["low_conviction"]:
        allocation = _holding_allocation(context, ticker)
        is_overweight = ticker in context["overweight_holdings"]

        if allocation > 5 or is_overweight:
            severity = "HIGH" if (
                is_overweight
                or any(item["ticker"] == ticker for item in context["concentration"])
            ) else "MEDIUM"
            evidence = [f"{ticker} low conviction"]

            if allocation:
                evidence.append(f"{ticker} allocation {allocation:g}%")

            if is_overweight:
                evidence.append(f"{ticker} overweight flag present")

            _append_conflict(
                conflicts,
                f"{ticker} position size conflicts with research conviction",
                "Research Conviction vs Position Size Conflict",
                severity,
                [ticker],
                evidence,
                (
                    f"{ticker} has weak research conviction while the "
                    "position size or overweight status is material."
                ),
                f"Review {ticker} thesis quality against position size."
            )

    portfolio_health = str(context.get("portfolio_health") or "").casefold()
    cash_target = context["allocation_targets"].get("CASH0", {})
    cash_gap = float(cash_target.get("difference", 0))
    cash_allocation = _holding_allocation(context, "CASH0")
    bond_exposure = next(
        (
            exposure["allocation"]
            for exposure in context["exposure_details"]
            if exposure["name"].casefold() == "bond"
        ),
        0
    )

    if (
        any(term in portfolio_health for term in ("elevated", "high"))
        and (cash_gap <= -3 or bond_exposure < 2)
    ):
        severity = "HIGH" if cash_gap <= -5 and bond_exposure < 2 else "MEDIUM"
        _append_conflict(
            conflicts,
            "Portfolio risk conflicts with defensive allocation gap",
            "Defensive Need vs Cash/Bond Gap Conflict",
            severity,
            ["CASH0"] if "CASH0" in context["allocations"] else [],
            [
                f"Portfolio health: {context.get('portfolio_health')}",
                f"Cash allocation {cash_allocation:g}%",
                f"Cash target gap {cash_gap:g}%",
                f"Bond exposure {bond_exposure:g}%"
            ],
            (
                "Portfolio risk is elevated while cash or bond exposure is "
                "below defensive allocation targets."
            ),
            "Evaluate liquidity buffer and defensive allocation gap."
        )

    conflicts = sorted(conflicts, key=_conflict_sort_key)
    highest = conflicts[0] if conflicts else None
    severity_counts = {
        severity: sum(
            conflict["conflict_severity"] == severity
            for conflict in conflicts
        )
        for severity in ("HIGH", "MEDIUM", "LOW")
    }
    summary = [
        "Theme Conflict Detection Status: ACTIVE",
        f"Detected Conflicts: {len(conflicts)}",
        f"High Conflicts: {severity_counts['HIGH']}",
        f"Medium Conflicts: {severity_counts['MEDIUM']}",
        f"Low Conflicts: {severity_counts['LOW']}",
        (
            f"Key Conflict: {highest['conflict_title']}"
            if highest
            else "Key Conflict: None"
        ),
        (
            f"Key Conflict Reason: {highest['conflict_reason']}"
            if highest
            else "Key Conflict Reason: No deterministic conflicts detected."
        ),
        "",
        (
            "Theme conflict detection flags deterministic tensions between "
            "agent signals, themes, news narratives, macro conditions, and "
            "portfolio positioning."
        )
    ]
    details = []

    for number, conflict in enumerate(conflicts, start=1):
        details.extend([
            f"{number}. {conflict['conflict_title']}",
            f"   Conflict Type: {conflict['conflict_type']}",
            f"   Conflict Severity: {conflict['conflict_severity']}",
            (
                "   Affected Holdings: "
                f"{', '.join(conflict['affected_holdings']) or 'None'}"
            ),
            f"   Conflict Reason: {conflict['conflict_reason']}",
            (
                "   Suggested Review Area: "
                f"{conflict['suggested_review_area']}"
            ),
            "   Evidence:"
        ])
        details.extend(
            f"   - {item}"
            for item in conflict["evidence"]
        )
        details.append("")

    if not details:
        details.append("No deterministic theme conflicts detected.")

    return {
        "summary": summary,
        "details": details,
        "conflicts": conflicts
    }


def build_signal_magnitude_report(signals):

    ranked_signals = rank_weighted_signals(signals)
    signals_with_magnitude = [
        signal for signal in ranked_signals
        if signal["magnitude_score"] > 0
    ]
    highest_magnitude = (
        sorted(
            signals_with_magnitude,
            key=lambda signal: (
                -signal["magnitude_score"],
                -signal["magnitude_adjusted_score"],
                PRIORITY_AGENT_RANKS.get(signal["source_agent"], 99),
                signal["title"].casefold()
            )
        )[0]
        if signals_with_magnitude
        else None
    )
    highest_adjusted = ranked_signals[0] if ranked_signals else None
    summary = [
        "Magnitude Scoring Status: ACTIVE",
        f"Signals With Magnitude Scores: {len(signals_with_magnitude)}",
        (
            f"Highest Magnitude Signal: {highest_magnitude['title']}"
            if highest_magnitude
            else "Highest Magnitude Signal: None"
        ),
        (
            f"Highest Magnitude Score: {highest_magnitude['magnitude_score']}"
            if highest_magnitude
            else "Highest Magnitude Score: 0"
        ),
        (
            "Highest Magnitude Adjusted Signal: "
            f"{highest_adjusted['title']}"
            if highest_adjusted
            else "Highest Magnitude Adjusted Signal: None"
        ),
        (
            "Highest Magnitude Adjusted Score: "
            f"{highest_adjusted['magnitude_adjusted_score']}"
            if highest_adjusted
            else "Highest Magnitude Adjusted Score: 0"
        ),
        "",
        (
            "Signal magnitude scoring adjusts priorities based on risk or "
            "opportunity size."
        )
    ]
    details = [
        (
            f"{number}. {signal['title']} | "
            f"Source {signal['source_agent']} | "
            f"Type {signal['signal_type']} | "
            f"Base Weighted Score {signal['weighted_score']} | "
            f"Magnitude Score {signal['magnitude_score']} | "
            f"Adjusted Score {signal['magnitude_adjusted_score']} | "
            f"Basis {signal['magnitude_basis']}"
        )
        for number, signal in enumerate(ranked_signals[:10], start=1)
    ]

    if not details:
        details.append("No signal magnitude data available.")

    return {
        "summary": summary,
        "details": details,
        "signals": ranked_signals
    }


def build_priority_candidates(signals):

    candidates = []

    for signal in rank_weighted_signals(signals):
        if signal["severity"] == "INFO":
            continue

        candidates.append({
            "source_agent": signal["source_agent"],
            "category": signal["category"],
            "title": signal["title"],
            "description": signal["description"],
            "severity": signal["severity"],
            "score": signal["score"],
            "signal_type": signal["signal_type"],
            "magnitude_score": signal["magnitude_score"],
            "weighted_score": signal["weighted_score"],
            "magnitude_adjusted_score": (
                signal["magnitude_adjusted_score"]
            ),
            "current_relevance": signal.get("metadata", {}).get(
                "current_relevance",
                "NORMAL"
            ),
            "risk_timeframe": signal.get("metadata", {}).get(
                "risk_timeframe",
                "current"
            )
        })

    return candidates


def rank_priorities(candidates):

    unique_priorities = {}

    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue

        title = " ".join(str(candidate.get("title") or "").split())

        if not title:
            continue

        normalized_title = title.casefold().rstrip(".")
        current = unique_priorities.get(normalized_title)

        if current is None:
            unique_priorities[normalized_title] = candidate
            continue

        candidate_key = (
            -candidate.get("magnitude_adjusted_score", 0),
            -candidate.get("score", 0),
            PRIORITY_AGENT_RANKS.get(candidate.get("source_agent"), 99),
            -candidate.get("magnitude_score", 0)
        )
        current_key = (
            -current.get("magnitude_adjusted_score", 0),
            -current.get("score", 0),
            PRIORITY_AGENT_RANKS.get(current.get("source_agent"), 99),
            -current.get("magnitude_score", 0)
        )

        if candidate_key < current_key:
            unique_priorities[normalized_title] = candidate

    return sorted(
        unique_priorities.values(),
        key=lambda priority: (
            -priority.get("magnitude_adjusted_score", 0),
            -priority.get("score", 0),
            PRIORITY_AGENT_RANKS.get(
                priority.get("source_agent"),
                99
            ),
            -priority.get("magnitude_score", 0),
            priority.get("title", "").casefold()
        )
    )


def determine_top_priority(priorities):

    current_priorities = [
        priority for priority in priorities
        if not _is_scenario_risk(priority)
    ]

    if current_priorities:
        return current_priorities[0]

    return priorities[0] if priorities else None


def build_cross_agent_priority_report(signals):

    priorities = rank_priorities(
        build_priority_candidates(signals)
    )
    top_priority = determine_top_priority(priorities)
    severity_counts = {
        severity: sum(
            priority["severity"] == severity
            for priority in priorities
        )
        for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    }
    summary = [
        "Priority Engine Status: ACTIVE",
        "",
        (
            f"Top Priority: {top_priority['title']}"
            if top_priority
            else "Top Priority: None identified."
        ),
        "",
        (
            f"Priority Source: {top_priority['source_agent']}"
            if top_priority
            else "Priority Source: None"
        ),
        "",
        f"Critical Priorities: {severity_counts['CRITICAL']}",
        f"High Priorities: {severity_counts['HIGH']}",
        f"Medium Priorities: {severity_counts['MEDIUM']}",
        f"Low Priorities: {severity_counts['LOW']}",
        "",
        (
            "Cross-Agent Priority Engine ranks issues across all active "
            "agents."
        ),
        (
            "Stress-test scenarios are separated from current live "
            "priorities."
        )
    ]
    details = []

    for number, priority in enumerate(priorities[:10], start=1):
        details.extend([
            f"{number}. {priority['title']}",
            f"   Source: {priority['source_agent']}",
            f"   Severity: {priority['severity']}",
            f"   Category: {priority['category']}",
            f"   Risk Timeframe: {priority.get('risk_timeframe', 'current')}",
            f"   Reason: {priority['description']}",
            ""
        ])

    if not details:
        details.append("No cross-agent priorities identified.")

    return {
        "summary": summary,
        "details": details,
        "priorities": priorities
    }


def determine_system_health(registry):

    failed_agents = sum(
        agent["agent_name"] in ACTIVE_REPORT_AGENTS
        and agent["last_run_status"] == "FAILED"
        for agent in registry
    )

    if failed_agents >= 2:
        return "CRITICAL"

    if failed_agents == 1:
        return "DEGRADED"

    return "HEALTHY"


def determine_top_macro_environment(macro):

    lines = _report_lines(macro)
    top_priority = _field_value(lines, "Top Macro Priority")

    if top_priority:
        return top_priority

    values = [
        _field_value(lines, label)
        for label in (
            "Current Macro Regime",
            "Inflation Trend",
            "Labor Market",
            "Policy Rate"
        )
    ]
    available_values = [value for value in values if value]

    return " | ".join(available_values) if available_values else "Unknown"


def determine_top_portfolio_risk(portfolio):

    lines = _combined_report_lines(portfolio)
    concentration_details = _report_section(
        lines,
        "CONCENTRATION RISK DETAILS"
    )

    for severity in ("HIGH", "MEDIUM"):
        for line in concentration_details:
            parts = [part.strip() for part in line.split("|")]

            if len(parts) >= 3 and parts[0] == severity:
                return _sentence(f"{parts[1]} {parts[2].lower()}")

    stress_summary = _report_section(lines, "STRESS TEST SUMMARY")
    stress_details = _report_section(lines, "STRESS TEST DETAILS")
    worst_scenario = _field_value(stress_summary, "Worst Scenario")

    if worst_scenario:
        scenario_name = worst_scenario.split("|", 1)[0].strip()

        for line in stress_details:
            if line.startswith(f"{scenario_name} |"):
                marker = "Largest Loss Contributor "

                if marker in line:
                    contributor = line.split(marker, 1)[1].split("|", 1)[0]

                    if contributor.strip().casefold() != "none":
                        return _sentence(
                            f"{contributor.strip()} contributes the largest "
                            f"downside exposure in {scenario_name}"
                        )

        return _sentence(f"{worst_scenario} is the largest stress-test risk")

    volatility = _report_section(lines, "VOLATILITY SUMMARY")
    volatility_level = _field_value(volatility, "Volatility Risk Level")
    volatility_contributor = _field_value(
        volatility,
        "Largest Volatility Contributor"
    )

    if volatility_level in {"HIGH", "MEDIUM"} and volatility_contributor:
        return _sentence(
            f"Portfolio volatility is {volatility_level.lower()}; "
            f"largest contributor {volatility_contributor}"
        )

    monte_carlo = _report_section(lines, "MONTE CARLO V2 SUMMARY")
    downside = _field_value(monte_carlo, "Probability Negative")

    if downside:
        return _sentence(f"Monte Carlo downside probability is {downside}")

    return "No major portfolio risk identified."


def determine_top_portfolio_opportunity(portfolio):

    lines = _report_lines(portfolio)
    committee = _report_section(lines, "INVESTMENT COMMITTEE SUMMARY")
    executive = _report_section(
        lines,
        "PORTFOLIO MANAGER EXECUTIVE BRIEF"
    )

    for source, label in (
        (committee, "Top Replacement Plan"),
        (committee, "Top Capital Deployment"),
        (executive, "Largest Opportunity")
    ):
        value = _field_value(source, label)

        if value and "no current opportunity" not in value.casefold():
            return _sentence(value)

    return "No major opportunity identified."


def determine_top_market_development(news):

    lines = _report_lines(news)

    for label in (
        "Top Market Narrative",
        "Top Market Story",
        "Top Macro Story",
        "Top Portfolio Story",
        "Top World Event Story"
    ):
        value = _field_value(lines, label)

        if value:
            return _sentence(value)

    return "No major market development identified."


def build_priority_action_queue(portfolio, macro, news):

    portfolio_lines = _report_lines(portfolio)
    executive = _report_section(
        portfolio_lines,
        "PORTFOLIO MANAGER EXECUTIVE BRIEF"
    )
    actions = []

    try:
        action_start = executive.index("Recommended Actions:") + 1
    except ValueError:
        action_start = len(executive)

    for line in executive[action_start:]:
        if not line[:1].isdigit():
            break

        action = line.split(".", 1)[1].strip() if "." in line else line

        if (
            action
            and "no additional action" not in action.casefold()
            and action not in actions
        ):
            actions.append(_concise(action))

        if len(actions) == 3:
            return actions

    highest_priority = _field_value(executive, "Highest Priority")

    if (
        highest_priority
        and "no immediate action" not in highest_priority.casefold()
        and highest_priority not in actions
    ):
        actions.append(_concise(highest_priority))

    macro_environment = determine_top_macro_environment(macro)

    if len(actions) < 3 and macro_environment != "Unknown":
        actions.append(_concise(f"Monitor macro environment: {macro_environment}"))

    market_development = determine_top_market_development(news)

    if (
        len(actions) < 3
        and market_development != "No major market development identified."
    ):
        actions.append(
            _concise(
                "Monitor market development: "
                f"{market_development.rstrip('.')}"
            )
        )

    return actions[:3]


def determine_signal_driven_system_health(registry, signals):

    health_signals = [
        signal for signal in signals
        if signal.get("category") == "Agent Health"
    ]
    failures = sum(
        signal.get("signal_type") in {"AGENT_FAILURE", "AGENT_OFFLINE"}
        for signal in health_signals
    )

    if failures >= 2:
        return "CRITICAL"

    if failures == 1 or health_signals:
        return "DEGRADED"

    return determine_system_health(registry)


def _select_macro_environment_signal(signals):

    weighted_signals = rank_weighted_signals(signals)
    environment = next(
        (
            signal for signal in weighted_signals
            if signal.get("category") == "Macro Environment"
        ),
        None
    )
    risk = next(
        (
            signal for signal in weighted_signals
            if signal.get("category") == "Macro Risk"
        ),
        None
    )

    if environment and risk:
        if (
            risk["magnitude_adjusted_score"]
            - environment["magnitude_adjusted_score"]
            <= 10
        ):
            return environment

        return risk

    return environment or risk


def _select_market_event_signal(signals):

    weighted_signals = rank_weighted_signals(signals)
    narrative = next(
        (
            signal for signal in weighted_signals
            if signal.get("signal_type") == "NEWS_NARRATIVE"
        ),
        None
    )

    if narrative:
        return narrative

    return select_signal_by_category(weighted_signals, ("Market Event",))


def _is_scenario_risk(signal):

    if not isinstance(signal, dict):
        return False

    metadata = signal.get("metadata", {})

    return (
        signal.get("signal_type") == "STRESS_TEST_RISK"
        or signal.get("category") == "Scenario Risk"
        or metadata.get("risk_timeframe") == "scenario"
    )


def _current_weighted_signals(signals):

    weighted_signals = rank_weighted_signals(signals)
    current_signals = [
        signal for signal in weighted_signals
        if not _is_scenario_risk(signal)
    ]

    return current_signals or weighted_signals


def _select_current_priority_signal(signals):

    current_signals = _current_weighted_signals(signals)
    return current_signals[0] if current_signals else None


def _select_worst_stress_scenario(signals):

    for signal in rank_weighted_signals(signals):
        if signal.get("signal_type") == "STRESS_TEST_RISK":
            return signal

    return None


def _stress_scenario_summary(signal):

    if not signal:
        return "None identified."

    title = str(signal.get("title") or "").strip()
    prefix = "Stress-test exposure:"

    if title.startswith(prefix):
        return title[len(prefix):].strip()

    return title or "None identified."


def _select_portfolio_risk_signal(signals):

    eligible_signals = []
    scenario_signals = []
    holding_research_types = {
        "MISSING_THESIS",
        "LOW_CONVICTION",
        "UNCOVERED_HOLDING"
    }

    for signal in rank_weighted_signals(signals):
        if _is_scenario_risk(signal):
            scenario_signals.append(signal)
            continue

        if signal.get("category") == "Portfolio Risk":
            eligible_signals.append(signal)
        elif (
            signal.get("category") == "Research Gap"
            and signal.get("signal_type") in holding_research_types
        ):
            eligible_signals.append(signal)

    if eligible_signals:
        return eligible_signals[0]

    return scenario_signals[0] if scenario_signals else None


def _signal_action_verb(signal):

    category = signal.get("category")

    if category == "Research Gap":
        return "Reevaluate"

    if category in {"Macro Risk", "Macro Environment", "Market Event"}:
        return "Monitor"

    if category == "Agent Health":
        return "Investigate"

    if category == "System Infrastructure":
        return "Confirm"

    return "Review"


def build_signal_driven_action_queue(signals):

    actions = []
    seen_titles = set()

    for signal in rank_weighted_signals(signals):
        title = signal.get("title", "").strip().rstrip(".")
        normalized_title = title.casefold()

        if not title or normalized_title in seen_titles:
            continue

        action = _concise(f"{_signal_action_verb(signal)} {title}")

        if action.casefold() not in {item.casefold() for item in actions}:
            actions.append(action)
            seen_titles.add(normalized_title)

        if len(actions) == 3:
            break

    return actions


def _build_signal_executive_notes(signals):

    weighted_signals = rank_weighted_signals(signals)

    if not weighted_signals:
        return "No material agent signals are available."

    dominant_category = _dominant_signal_value(
        weighted_signals,
        "category"
    )
    highest_risk = next(
        (
            signal for signal in weighted_signals
            if signal.get("severity") in {"CRITICAL", "HIGH"}
        ),
        weighted_signals[0]
    )
    sources = {
        signal["source_agent"]
        for signal in weighted_signals
    }
    first_sentence = (
        f"{dominant_category} signals dominate today's signal stack, "
        f"led by {highest_risk['source_agent']}."
    )

    if len(sources) >= 3:
        second_sentence = (
            f"Signals are broad across {len(sources)} source agents."
        )
    elif len(sources) == 2:
        second_sentence = "Signals span two source agents."
    else:
        second_sentence = (
            f"Signals are concentrated in {highest_risk['source_agent']}."
        )

    return f"{first_sentence} {second_sentence}"


def _dominant_theme(theme_report):

    if isinstance(theme_report, dict):
        themes = theme_report.get("themes", [])
    else:
        themes = theme_report or []

    return themes[0] if themes else None


def _dominant_theme_impact(theme_impact_report):

    if isinstance(theme_impact_report, dict):
        impacts = theme_impact_report.get("impacts", [])
    else:
        impacts = theme_impact_report or []

    return impacts[0] if impacts else None


def _key_theme_conflict(theme_conflict_report):

    if isinstance(theme_conflict_report, dict):
        conflicts = theme_conflict_report.get("conflicts", [])
    else:
        conflicts = theme_conflict_report or []

    return conflicts[0] if conflicts else None


def build_signal_driven_executive_summary(registry, signals,
                                          theme_report=None,
                                          theme_impact_report=None,
                                          theme_conflict_report=None):

    weighted_signals = rank_weighted_signals(signals)
    current_signals = _current_weighted_signals(weighted_signals)
    top_priority = _select_current_priority_signal(weighted_signals)
    dominant_theme = _dominant_theme(theme_report)
    dominant_impact = _dominant_theme_impact(theme_impact_report)
    key_conflict = _key_theme_conflict(theme_conflict_report)
    macro_environment = _select_macro_environment_signal(current_signals)
    portfolio_risk = _select_portfolio_risk_signal(current_signals)
    worst_stress = _select_worst_stress_scenario(weighted_signals)
    portfolio_opportunity = select_signal_by_category(
        current_signals,
        ("Portfolio Opportunity",)
    )
    market_development = _select_market_event_signal(current_signals)
    actions = build_signal_driven_action_queue(current_signals)
    notes = _build_signal_executive_notes(current_signals)
    summary = [
        (
            "System Health: "
            f"{determine_signal_driven_system_health(registry, signals)}"
        ),
        "",
        (
            f"Top Priority: {top_priority['title']}"
            if top_priority
            else "Top Priority: None identified."
        ),
        "",
        (
            f"Dominant Cross-Agent Theme: {dominant_theme['theme_title']}"
            if dominant_theme
            else "Dominant Cross-Agent Theme: None"
        ),
        (
            f"Theme Reason: {dominant_theme['theme_reason']}"
            if dominant_theme
            else "Theme Reason: No cross-agent themes detected."
        ),
        (
            f"Theme Impact: {_theme_impact_summary(dominant_impact)}"
            if dominant_impact
            else "Theme Impact: No mapped portfolio impact."
        ),
        (
            f"Key Conflict: {key_conflict['conflict_title']}"
            if key_conflict
            else "Key Conflict: None"
        ),
        (
            f"Conflict Reason: {key_conflict['conflict_reason']}"
            if key_conflict
            else "Conflict Reason: No deterministic conflicts detected."
        ),
        "",
        (
            f"Top Macro Environment: {macro_environment['title']}"
            if macro_environment
            else "Top Macro Environment: Unknown"
        ),
        "",
        (
            f"Top Portfolio Risk: {portfolio_risk['title']}"
            if portfolio_risk
            else "Top Portfolio Risk: No major portfolio risk identified."
        ),
        "",
        f"Worst Stress Scenario: {_stress_scenario_summary(worst_stress)}",
        "",
        (
            f"Top Portfolio Opportunity: {portfolio_opportunity['title']}"
            if portfolio_opportunity
            else (
                "Top Portfolio Opportunity: "
                "No major portfolio opportunity identified."
            )
        ),
        "",
        (
            f"Top Market Development: {market_development['title']}"
            if market_development
            else (
                "Top Market Development: "
                "No major market development identified."
            )
        ),
        "",
        "Priority Action Queue:"
    ]

    if actions:
        summary.extend(
            f"{number}. {action}"
            for number, action in enumerate(actions, start=1)
        )
    else:
        summary.append("No priority actions identified.")

    summary.extend([
        "",
        f"Executive Notes: {notes}",
        "",
        "Stress-test scenarios are separated from current live priorities.",
        "",
        (
            "Echo Executive Summary is generated deterministically from "
            "agent signals and does not constitute investment advice."
        )
    ])

    return summary


def compress_action_queue(actions):

    compressed = []

    for action in actions or []:
        action = _concise(action, limit=120)

        if action and action.casefold() not in {
            item.casefold() for item in compressed
        }:
            compressed.append(action)

        if len(compressed) == 3:
            break

    return compressed


def determine_full_report_trigger(system_health, signals, portfolio_risk):

    if system_health in {"DEGRADED", "CRITICAL"}:
        return "Agent failure detected."

    top_priority = _select_current_priority_signal(signals)

    if (
        top_priority
        and top_priority.get("severity") in {"HIGH", "CRITICAL"}
    ):
        return "High-priority signal requires review."

    if portfolio_risk is not None:
        return "Portfolio risk details need review."

    return "No immediate full-report review required."


def build_echo_executive_brief(registry, signals, theme_report=None,
                               theme_impact_report=None,
                               theme_conflict_report=None):

    weighted_signals = rank_weighted_signals(signals)
    current_signals = _current_weighted_signals(weighted_signals)
    system_health = determine_signal_driven_system_health(
        registry,
        weighted_signals
    )
    top_priority = _select_current_priority_signal(weighted_signals)
    dominant_theme = _dominant_theme(theme_report)
    dominant_impact = _dominant_theme_impact(theme_impact_report)
    key_conflict = _key_theme_conflict(theme_conflict_report)
    portfolio_risk = _select_portfolio_risk_signal(current_signals)
    worst_stress = _select_worst_stress_scenario(weighted_signals)
    macro_backdrop = _select_macro_environment_signal(current_signals)
    market_watch = _select_market_event_signal(current_signals)
    actions = compress_action_queue(
        build_signal_driven_action_queue(current_signals)
    )
    brief = [
        f"System: {system_health}",
        (
            f"Top Priority: {_concise(top_priority['title'], limit=140)}"
            if top_priority
            else "Top Priority: None identified."
        ),
        (
            f"Dominant Theme: {_concise(dominant_theme['theme_title'], limit=140)}"
            if dominant_theme
            else "Dominant Theme: None"
        ),
        (
            f"Theme Impact: {_concise(_theme_impact_summary(dominant_impact), limit=140)}"
            if dominant_impact
            else "Theme Impact: No mapped portfolio impact."
        ),
        (
            f"Key Conflict: {_concise(key_conflict['conflict_title'], limit=140)}"
            if key_conflict
            else "Key Conflict: None"
        ),
        (
            f"Portfolio Risk: {_concise(portfolio_risk['title'], limit=140)}"
            if portfolio_risk
            else "Portfolio Risk: No major portfolio risk identified."
        ),
        (
            "Worst Stress Scenario: "
            f"{_concise(_stress_scenario_summary(worst_stress), limit=140)}"
        ),
        (
            f"Macro Backdrop: {_concise(macro_backdrop['title'], limit=140)}"
            if macro_backdrop
            else "Macro Backdrop: Unknown"
        ),
        (
            f"Market Watch: {_concise(market_watch['title'], limit=140)}"
            if market_watch
            else "Market Watch: No major market development identified."
        ),
        "",
        "Action Queue:"
    ]

    if actions:
        brief.extend(
            f"{number}. {action}"
            for number, action in enumerate(actions, start=1)
        )
    else:
        brief.append("No priority actions identified.")

    brief.extend([
        "",
        (
            "Read Full Report If: "
            f"{determine_full_report_trigger(
                system_health,
                weighted_signals,
                portfolio_risk
            )}"
        ),
        "",
        (
            "Echo Executive Brief is a compressed command brief. "
            "Stress-test scenarios are separated from current live "
            "priorities. Full agent reports remain below."
        )
    ])

    return brief


def create_agent_registry():

    registry = []

    for definition in AGENT_REGISTRY:
        agent = dict(definition)
        capability = AGENT_QUERY_CAPABILITIES.get(
            agent["agent_name"],
            FUTURE_AGENT_QUERY_CAPABILITY
        )
        agent.update({
            key: tuple(value)
            for key, value in capability.items()
        })
        registry.append(agent)

    return registry


def get_agent_registry():

    return create_agent_registry()


def get_registry_agent(registry, agent_name):

    return next(
        agent for agent in registry
        if agent["agent_name"] == agent_name
    )


def normalize_agent_name(agent_name):

    normalized = " ".join(str(agent_name or "").split()).casefold()

    if not normalized:
        return ""

    if normalized in AGENT_NAME_ALIASES:
        return AGENT_NAME_ALIASES[normalized]

    for agent in AGENT_REGISTRY:
        if agent["agent_name"].casefold() == normalized:
            return agent["agent_name"]

    return " ".join(str(agent_name).split())


def get_agent_by_name(agent_name, registry=None):

    normalized_name = normalize_agent_name(agent_name)
    registry = registry if registry is not None else get_agent_registry()

    return next(
        (
            agent for agent in registry
            if agent["agent_name"].casefold() == normalized_name.casefold()
        ),
        None
    )


def get_agent_query_capability(agent_name):

    agent = get_agent_by_name(agent_name)

    if agent is None:
        return None

    return {
        "agent_name": agent["agent_name"],
        "query_mode": agent["query_mode"],
        "supported_query_types": agent["supported_query_types"],
        "planned_query_types": agent["planned_query_types"],
        "example_queries": agent["example_queries"]
    }


def classify_query_intent(query):

    text = " ".join(str(query or "").split()).casefold()

    if not text:
        return "empty"

    intent_terms = (
        ("conflicts", ("conflict", "mismatch", "tension")),
        ("impacts", ("impact", "exposure map", "affected")),
        ("themes", ("theme", "narrative cluster")),
        ("action queue", ("action", "queue", "review list")),
        ("top priority", ("top priority", "highest priority", "priority")),
        ("market watch", ("market watch", "market development")),
        ("macro backdrop", ("macro backdrop", "backdrop")),
        ("portfolio risk", ("portfolio risk",)),
        ("concentration", ("concentration", "too large", "overweight")),
        ("allocation", ("allocation", "target", "underweight")),
        ("opportunity", ("opportunity", "capital deployment", "candidate")),
        ("tax", ("tax", "taxable", "gain", "loss harvest")),
        ("stress test", ("stress", "drawdown", "crisis")),
        ("regime", ("regime",)),
        ("inflation", ("inflation", "cpi", "pce")),
        ("yield curve", ("yield curve", "curve")),
        ("rates", ("rate", "fed", "fomc", "yield")),
        ("labor", ("labor", "jobs", "unemployment", "payroll")),
        ("energy", ("energy", "oil", "crude", "hormuz", "iran")),
        ("market narrative", ("market narrative", "top narrative")),
        ("macro news", ("macro news", "fed news")),
        ("world event", ("world event", "geopolitical")),
        ("portfolio news", ("portfolio news",)),
        ("watchlist news", ("watchlist news",)),
        ("thesis", ("thesis",)),
        ("conviction", ("conviction", "weak holding", "weak holdings")),
        ("research gaps", ("research gap", "research gaps", "coverage")),
        ("watchlist", ("watchlist",))
    )

    for intent, terms in intent_terms:
        if any(term in text for term in terms):
            return intent

    return "general"


def _query_result(agent_name, query, status, answer, confidence="MEDIUM",
                  requires_full_report=False, notes=""):

    return {
        "agent_name": agent_name,
        "query": " ".join(str(query or "").split()),
        "status": status,
        "answer": answer,
        "confidence": confidence,
        "requires_full_report": requires_full_report,
        "notes": notes
    }


def _query_context(context):

    if isinstance(context, dict) and "sections" in context:
        return context

    if isinstance(context, dict) and any(
        key in context
        for key in ("portfolio", "macro", "news", "research")
    ):
        return {"sections": context}

    return build_morning_brief(return_bundle=True)


def _query_sections(context):

    return _query_context(context)["sections"]


def _lines_from_section(sections, key, full_report=False):

    value = sections.get(key, [])

    if full_report and isinstance(value, dict):
        return _report_lines(value) + _full_report_lines(value)

    if full_report:
        return _full_report_lines(value)

    return _report_lines(value)


def _first_field(lines, labels):

    for label in labels:
        value = _field_value(lines, label)

        if value:
            return value

    return ""


def _compact_lines(lines, limit=4):

    useful_lines = [
        line for line in lines
        if line and not set(line) <= {"-"}
    ]

    return " | ".join(useful_lines[:limit]) if useful_lines else "None found."


def _numbered_after(lines, heading, limit=3):

    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []

    items = []

    for line in lines[start:]:
        if not line:
            if items:
                break
            continue

        if re.match(r"^\d+\.\s+", line):
            items.append(line)

        if len(items) == limit:
            break

    return items


def _detect_query_tickers(query, sections):

    portfolio_context = _extract_portfolio_context(sections.get("portfolio"))
    known_tickers = sorted(
        portfolio_context["allocations"],
        key=lambda ticker: (-len(ticker), ticker)
    )
    text = " ".join(str(query or "").split())
    detected = []

    for ticker in known_tickers:
        if re.search(rf"\b{re.escape(ticker)}\b", text, flags=re.IGNORECASE):
            detected.append(ticker)

    uppercase_tokens = re.findall(r"\b[A-Z][A-Z0-9.]{1,5}\b", text)

    for token in uppercase_tokens:
        token = token.upper()

        if token in portfolio_context["allocations"]:
            detected.append(token)

    return _unique_preserve_order(detected)


def classify_echo_multi_agent_intent(query, sections=None):

    text = " ".join(str(query or "").split()).casefold()

    if not text:
        return "empty"

    if sections and _detect_query_tickers(query, sections):
        if any(
            term in text
            for term in (
                "risk",
                "risks",
                "affected",
                "impact",
                "conviction",
                "thesis",
                "catalyst",
                "monitor",
                "exposed",
                "exposure"
            )
        ):
            return "position risk"

    if any(term in text for term in ("conflict", "mismatch", "tension")):
        return "theme/conflict review"

    if any(
        term in text
        for term in ("allocation", "concentration", "overweight",
                     "underweight", "too large", "exposed am i")
    ):
        return "allocation/concentration review"

    if any(
        term in text
        for term in ("inflation", "energy", "rates", "rate risk", "fed",
                     "macro", "regime", "yield")
    ):
        return "macro impact"

    if any(
        term in text
        for term in ("news", "narrative", "market", "headline",
                     "catalyst", "today")
    ):
        return "market/news impact"

    if any(
        term in text
        for term in ("research", "conviction", "thesis", "weak holding",
                     "weak holdings", "quality")
    ):
        return "research quality"

    if any(
        term in text
        for term in ("portfolio risk", "biggest risk", "top risk",
                     "stress", "drawdown", "crisis")
    ):
        return "portfolio risk"

    if any(
        term in text
        for term in ("top priority", "highest priority", "monitor",
                     "review", "what matters", "watch")
    ):
        return "general top-priority review"

    return "general top-priority review"


def _echo_multi_agent_supported_intent(intent):

    return intent in {
        "position risk",
        "portfolio risk",
        "macro impact",
        "market/news impact",
        "research quality",
        "theme/conflict review",
        "allocation/concentration review",
        "general top-priority review"
    }


def _should_route_echo_multi_agent(query, context=None):

    sections = _query_sections(context)
    intent = classify_echo_multi_agent_intent(query, sections)

    if not _echo_multi_agent_supported_intent(intent):
        return False

    simple_intent = classify_query_intent(query)
    text = " ".join(str(query or "").split()).casefold()

    if simple_intent in {
        "top priority",
        "themes",
        "impacts",
        "conflicts",
        "action queue",
        "market watch",
        "macro backdrop",
        "portfolio risk"
    } and not any(
        term in text
        for term in (
            "why",
            "how",
            "biggest",
            "main",
            "monitor",
            "today",
            "affect",
            "impact",
            "exposed",
            "risks to",
            "risk to"
        )
    ):
        return False

    return True


def _answer_from_lines(agent_name, query, answer, confidence="HIGH",
                       requires_full_report=False, notes=""):

    return _query_result(
        agent_name,
        query,
        "ANSWERED",
        _concise(answer, limit=700),
        confidence,
        requires_full_report,
        notes or "Answered deterministically from existing Echo reports."
    )


def answer_portfolio_query(query, context):

    sections = _query_sections(context)
    portfolio_lines = _lines_from_section(sections, "portfolio", True)
    executive_lines = sections.get("executive_summary", [])
    intent = classify_query_intent(query)

    if intent in {"risk", "portfolio risk", "general"}:
        risk = _first_field(executive_lines, ("Top Portfolio Risk",))
        return _answer_from_lines(
            "Portfolio Manager",
            query,
            f"Top portfolio risk: {risk or determine_top_portfolio_risk(sections.get('portfolio'))}",
            requires_full_report=True
        )

    if intent == "concentration":
        summary = _report_section(portfolio_lines, "CONCENTRATION RISK SUMMARY")
        details = _report_section(portfolio_lines, "CONCENTRATION RISK DETAILS")
        return _answer_from_lines(
            "Portfolio Manager",
            query,
            "Concentration risk: "
            f"{_compact_lines(summary + details, limit=5)}",
            requires_full_report=True
        )

    if intent == "allocation":
        allocation = _report_section(portfolio_lines, "TICKER ALLOCATION")
        alerts = _report_section(portfolio_lines, "REBALANCE ALERTS")
        return _answer_from_lines(
            "Portfolio Manager",
            query,
            f"Allocation snapshot: {_compact_lines(allocation + alerts, limit=6)}",
            requires_full_report=True
        )

    if intent == "opportunity":
        opportunity = _first_field(
            executive_lines,
            ("Top Portfolio Opportunity",)
        )
        deployment = _report_section(portfolio_lines, "CAPITAL DEPLOYMENT")
        return _answer_from_lines(
            "Portfolio Manager",
            query,
            f"Portfolio opportunity: {opportunity or _compact_lines(deployment)}",
            requires_full_report=True
        )

    if intent == "tax":
        tax_summary = _report_section(portfolio_lines, "TAX OPTIMIZATION SUMMARY")
        tax_details = _report_section(portfolio_lines, "TAX OPTIMIZATION DETAILS")
        return _answer_from_lines(
            "Portfolio Manager",
            query,
            f"Tax summary: {_compact_lines(tax_summary + tax_details, limit=6)}",
            requires_full_report=True
        )

    if intent == "stress test":
        stress = _report_section(portfolio_lines, "STRESS TEST SUMMARY")
        return _answer_from_lines(
            "Portfolio Manager",
            query,
            f"Stress test summary: {_compact_lines(stress, limit=5)}",
            requires_full_report=True
        )

    return _query_result(
        "Portfolio Manager",
        query,
        "UNSUPPORTED_QUERY",
        "Portfolio Manager supports risk, concentration, allocation, opportunity, tax, and stress test queries.",
        "LOW",
        False,
        "No deterministic portfolio query intent matched."
    )


def answer_macro_query(query, context):

    sections = _query_sections(context)
    macro_lines = _lines_from_section(sections, "macro", True)
    intent = classify_query_intent(query)

    if intent in {"regime", "general"}:
        regime = _first_field(macro_lines, ("Current Macro Regime",))
        priority = _first_field(macro_lines, ("Top Macro Priority",))
        reason = _first_field(macro_lines, ("Top Macro Reason",))
        return _answer_from_lines(
            "Macro Agent",
            query,
            f"Current macro regime: {regime or 'Unknown'}. Top macro priority: {priority or 'Unknown'}. Reason: {reason or 'Not available.'}",
            requires_full_report=True
        )

    field_map = {
        "inflation": "Inflation Trend",
        "rates": "Policy Rate",
        "labor": "Labor Market",
        "yield curve": "Yield Curve",
        "energy": "Energy"
    }

    if intent in field_map:
        label = field_map[intent]
        value = _first_field(macro_lines, (label,))
        ranked = [
            line for line in _report_section(macro_lines, "Ranked Macro Priority Signals:")
            if label.casefold() in line.casefold()
        ]
        return _answer_from_lines(
            "Macro Agent",
            query,
            f"{label}: {value or 'Unknown'}. Detail: {_compact_lines(ranked, limit=3)}",
            requires_full_report=True
        )

    return _query_result(
        "Macro Agent",
        query,
        "UNSUPPORTED_QUERY",
        "Macro Agent supports regime, inflation, rates, labor, yield curve, and energy queries.",
        "LOW",
        False,
        "No deterministic macro query intent matched."
    )


def answer_news_query(query, context):

    sections = _query_sections(context)
    news_lines = _lines_from_section(sections, "news", True)
    intent = classify_query_intent(query)
    label_map = {
        "market narrative": "Top Market Narrative",
        "general": "Top Market Narrative",
        "macro news": "Top Macro Story",
        "world event": "Top World Event Story",
        "portfolio news": "Top Portfolio Story",
        "watchlist news": "Top Watchlist Story"
    }

    if intent in label_map:
        label = label_map[intent]
        value = _first_field(news_lines, (label,))
        reason = _first_field(news_lines, ("Top Narrative Reason",))
        score = _first_field(news_lines, ("Top Narrative Score",))
        return _answer_from_lines(
            "News Agent",
            query,
            f"{label}: {value or 'None'}. Narrative score: {score or 'N/A'}. Reason: {reason or 'Not available.'}",
            requires_full_report=True
        )

    return _query_result(
        "News Agent",
        query,
        "UNSUPPORTED_QUERY",
        "News Agent supports market narrative, macro news, world event, portfolio news, and watchlist news queries.",
        "LOW",
        False,
        "No deterministic news query intent matched."
    )


def answer_research_query(query, context):

    sections = _query_sections(context)
    research_lines = _lines_from_section(sections, "research", True)
    portfolio_lines = _lines_from_section(sections, "portfolio", True)
    intent = classify_query_intent(query)

    if intent in {"conviction", "weak holdings", "general"}:
        health = (
            _report_section(research_lines, "RESEARCH HEALTH")
            + _report_section(portfolio_lines, "RESEARCH HEALTH")
        )
        weak = [
            line for line in health
            if "low conviction" in line.casefold()
        ]

        if not weak:
            weak = [
                line for line in research_lines + portfolio_lines
                if "low conviction" in line.casefold()
            ]

        return _answer_from_lines(
            "Research Agent",
            query,
            f"Weak conviction holdings: {_compact_lines(weak, limit=6)}",
            requires_full_report=True
        )

    if intent in {"research gaps", "thesis"}:
        gaps = (
            _report_section(research_lines, "RESEARCH GAPS")
            + _report_section(portfolio_lines, "RESEARCH GAPS")
        )
        health = _report_section(portfolio_lines, "RESEARCH HEALTH")
        return _answer_from_lines(
            "Research Agent",
            query,
            f"Research review: {_compact_lines(gaps + health, limit=6)}",
            requires_full_report=True
        )

    if intent == "watchlist":
        watchlist = (
            _report_section(research_lines, "WATCHLIST")
            + _report_section(portfolio_lines, "WATCHLIST")
        )
        return _answer_from_lines(
            "Research Agent",
            query,
            f"Watchlist: {_compact_lines(watchlist, limit=6)}",
            requires_full_report=True
        )

    return _query_result(
        "Research Agent",
        query,
        "UNSUPPORTED_QUERY",
        "Research Agent supports thesis, conviction, research gaps, weak holdings, and watchlist queries.",
        "LOW",
        False,
        "No deterministic research query intent matched."
    )


def answer_echo_query(query, context):

    sections = _query_sections(context)
    executive_brief = sections.get("executive_brief", [])
    executive_summary = sections.get("executive_summary", [])
    intent = classify_query_intent(query)

    if intent == "top priority":
        value = _first_field(executive_summary, ("Top Priority",))
        return _answer_from_lines("Echo", query, f"Top priority: {value or 'None identified.'}")

    if intent == "themes":
        return _answer_from_lines(
            "Echo",
            query,
            _compact_lines(sections.get("theme_summary", []) + sections.get("theme_details", []), limit=8),
            requires_full_report=True
        )

    if intent == "impacts":
        return _answer_from_lines(
            "Echo",
            query,
            _compact_lines(sections.get("theme_impact_summary", []) + sections.get("theme_impact_details", []), limit=8),
            requires_full_report=True
        )

    if intent == "conflicts":
        return _answer_from_lines(
            "Echo",
            query,
            _compact_lines(sections.get("theme_conflict_summary", []) + sections.get("theme_conflict_details", []), limit=10),
            requires_full_report=True
        )

    if intent == "action queue":
        actions = _numbered_after(executive_summary, "Priority Action Queue:")
        return _answer_from_lines("Echo", query, f"Action queue: {_compact_lines(actions)}")

    if intent == "market watch":
        value = _first_field(executive_brief, ("Market Watch",))
        return _answer_from_lines("Echo", query, f"Market watch: {value or 'No major market development identified.'}")

    if intent == "macro backdrop":
        value = _first_field(executive_brief, ("Macro Backdrop",))
        return _answer_from_lines("Echo", query, f"Macro backdrop: {value or 'Unknown.'}")

    if intent == "portfolio risk":
        value = _first_field(executive_brief, ("Portfolio Risk",))
        return _answer_from_lines("Echo", query, f"Portfolio risk: {value or 'No major portfolio risk identified.'}")

    return _answer_from_lines(
        "Echo",
        query,
        (
            f"Top priority: {_first_field(executive_summary, ('Top Priority',)) or 'None identified.'} "
            f"Key conflict: {_first_field(executive_summary, ('Key Conflict',)) or 'None.'} "
            f"Market watch: {_first_field(executive_brief, ('Market Watch',)) or 'None.'}"
        ),
        "MEDIUM"
    )


def _multi_agent_route_plan(intent, tickers):

    if intent == "position risk":
        return [
            ("Portfolio Manager", "what is my concentration risk?"),
            ("Research Agent", "which holdings have weak conviction?"),
            ("Macro Agent", "what is the current regime?"),
            ("News Agent", "what is the top market narrative?")
        ]

    if intent == "portfolio risk":
        return [
            ("Portfolio Manager", "what is the top portfolio risk?"),
            ("Macro Agent", "what is the current regime?"),
            ("News Agent", "what is the top market narrative?"),
            ("Research Agent", "which holdings have weak conviction?")
        ]

    if intent == "macro impact":
        return [
            ("Macro Agent", "what is the current regime?"),
            ("Portfolio Manager", "what is my concentration risk?"),
            ("News Agent", "what is the top market narrative?"),
            ("Research Agent", "which holdings have weak conviction?")
        ]

    if intent == "market/news impact":
        return [
            ("News Agent", "what is the top market narrative?"),
            ("Macro Agent", "what is the current regime?"),
            ("Portfolio Manager", "what is the top portfolio risk?"),
            ("Research Agent", "which holdings have weak conviction?")
        ]

    if intent == "research quality":
        return [
            ("Research Agent", "which holdings have weak conviction?"),
            ("Portfolio Manager", "what is my concentration risk?"),
            ("Macro Agent", "what is the current regime?")
        ]

    if intent == "theme/conflict review":
        return [
            ("Portfolio Manager", "what is my concentration risk?"),
            ("Macro Agent", "what is the current regime?"),
            ("News Agent", "what is the top market narrative?"),
            ("Research Agent", "which holdings have weak conviction?")
        ]

    if intent == "allocation/concentration review":
        return [
            ("Portfolio Manager", "what is my concentration risk?"),
            ("Research Agent", "which holdings have weak conviction?"),
            ("Macro Agent", "what is the current regime?")
        ]

    return [
        ("Portfolio Manager", "what is the top portfolio risk?"),
        ("Macro Agent", "what is the current regime?"),
        ("News Agent", "what is the top market narrative?"),
        ("Research Agent", "which holdings have weak conviction?")
    ]


def _source_answer_map(route_plan, context):

    source_answers = {}

    for agent_name, agent_query in route_plan:
        result = answer_agent_query(agent_name, agent_query, context)

        if result.get("status") == "ANSWERED":
            source_answers[result["agent_name"]] = result.get("answer", "")
        else:
            source_answers[result.get("agent_name", agent_name)] = (
                result.get("answer", "No answer returned.")
            )

    return source_answers


def _ticker_allocation_summary(ticker, portfolio_context):

    target = portfolio_context["allocation_targets"].get(ticker, {})
    allocation = target.get("allocation")
    target_weight = target.get("target")
    difference = target.get("difference")
    concentration = next(
        (
            item for item in portfolio_context["concentration"]
            if item["ticker"] == ticker
        ),
        None
    )
    parts = []

    if isinstance(allocation, (int, float)):
        if isinstance(target_weight, (int, float)) and isinstance(
            difference,
            (int, float)
        ):
            parts.append(
                f"{ticker} is {allocation:g}% of the portfolio versus "
                f"a {target_weight:g}% target ({difference:+g}%)."
            )
        else:
            parts.append(f"{ticker} is {allocation:g}% of the portfolio.")

    if concentration:
        parts.append(
            f"Portfolio Manager flags {ticker} as "
            f"{concentration['severity'].lower()} concentration: "
            f"{concentration['detail']}."
        )

    if ticker in portfolio_context["overweight_holdings"]:
        parts.append(f"{ticker} is also marked overweight.")

    return " ".join(parts)


def _ticker_research_summary(ticker, research_lines, portfolio_context):

    ticker_lines = [
        line for line in research_lines
        if re.search(rf"\b{re.escape(ticker)}\b", line)
    ]
    low_conviction = ticker in portfolio_context["low_conviction"] or any(
        "conviction low" in line.casefold()
        or "low conviction" in line.casefold()
        for line in ticker_lines
    )

    if low_conviction:
        return (
            f"Research Agent classifies {ticker} as weak or low conviction."
        )

    if ticker_lines:
        return f"Research Agent has coverage for {ticker}: {ticker_lines[0]}."

    return f"Research Agent has no direct {ticker} issue in the current report."


def _ticker_theme_summary(ticker, echo_lines):

    related = []

    for index, line in enumerate(echo_lines):
        if not re.search(rf"\b{re.escape(ticker)}\b", line):
            continue

        cleaned = re.sub(r"^\d+\.\s+", "", line).strip()

        if "conflict" in cleaned.casefold():
            reason = next(
                (
                    candidate.strip().split(":", 1)[1].strip()
                    for candidate in echo_lines[index + 1:index + 6]
                    if candidate.strip().casefold().startswith(
                        "conflict reason:"
                    )
                    and ":" in candidate
                ),
                ""
            )

            if reason:
                related.append(f"{cleaned}: {reason}")
            else:
                related.append(cleaned)
        else:
            related.append(cleaned)

    conflict = next(
        (line for line in related if "conflict" in line.casefold()),
        ""
    )
    impact = next(
        (line for line in related if "impact reason" in line.casefold()),
        ""
    )

    if conflict:
        return conflict

    if impact:
        return impact

    if related:
        return related[0]

    return ""


def _macro_pressure_summary(ticker, portfolio_context, macro_lines):

    target = portfolio_context["allocation_details"].get(ticker, {})
    factors = set(target.get("factors") or [])
    inflation = _first_field(macro_lines, ("Inflation Trend",))
    rates = _first_field(macro_lines, ("Policy Rate",))
    regime = _first_field(macro_lines, ("Current Macro Regime",))

    if "growth" in factors and (
        "ris" in inflation.casefold()
        or "stress" in regime.casefold()
        or "restrict" in rates.casefold()
    ):
        return (
            "Macro conditions add secondary pressure because inflation/rates "
            "themes can pressure growth assets."
        )

    if "commodity" in factors and "ris" in _first_field(
        macro_lines,
        ("Energy",)
    ).casefold():
        return (
            "Macro conditions are relevant because energy is rising and the "
            "holding maps to commodity exposure."
        )

    return ""


def _news_direct_catalyst_summary(ticker, news_lines):

    direct = [
        line for line in news_lines
        if re.search(rf"\b{re.escape(ticker)}\b", line)
    ]

    if direct:
        return f"News Agent shows a direct {ticker} mention: {direct[0]}."

    return (
        f"News Agent does not show a direct {ticker}-specific catalyst in "
        "the current report."
    )


def _position_risk_answer(tickers, sections):

    portfolio_context = _extract_portfolio_context(sections.get("portfolio"))
    research_lines = _lines_from_section(sections, "research", True)
    macro_lines = _lines_from_section(sections, "macro", True)
    news_lines = _lines_from_section(sections, "news", True)
    echo_lines = (
        sections.get("theme_impact_details", [])
        + sections.get("theme_conflict_details", [])
        + sections.get("theme_details", [])
    )
    sentences = []

    for ticker in tickers:
        reasons = []
        concentration = any(
            item["ticker"] == ticker
            for item in portfolio_context["concentration"]
        )
        low_conviction = ticker in portfolio_context["low_conviction"]
        macro_pressure = _macro_pressure_summary(
            ticker,
            portfolio_context,
            macro_lines
        )

        if concentration:
            reasons.append("position size")

        if low_conviction:
            reasons.append("weak conviction")

        if macro_pressure:
            reasons.append("macro sensitivity")

        if not reasons:
            reasons.append("portfolio exposure")

        sentences.append(
            f"{ticker} risk is mainly " + " plus ".join(reasons) + "."
        )
        sentences.append(_ticker_allocation_summary(ticker, portfolio_context))
        sentences.append(
            _ticker_research_summary(ticker, research_lines, portfolio_context)
        )

        theme_summary = _ticker_theme_summary(ticker, echo_lines)

        if theme_summary:
            sentences.append(theme_summary)

        if macro_pressure:
            sentences.append(macro_pressure)

        sentences.append(_news_direct_catalyst_summary(ticker, news_lines))

    return " ".join(sentence for sentence in sentences if sentence)


def _rates_exposure_summary(sections):

    portfolio_context = _extract_portfolio_context(sections.get("portfolio"))
    growth = next(
        (
            factor for factor in portfolio_context["factor_details"]
            if factor["name"].casefold() == "growth"
        ),
        None
    )
    equity = next(
        (
            exposure for exposure in portfolio_context["exposure_details"]
            if exposure["name"].casefold() == "equity"
        ),
        None
    )
    details = []

    if growth:
        details.append(f"Growth factor exposure is {growth['allocation']:g}%.")

    if equity:
        details.append(f"Equity exposure is {equity['allocation']:g}%.")

    return " ".join(details)


def _echo_multi_agent_conclusion(intent, tickers, sections, source_answers):

    executive_summary = sections.get("executive_summary", [])
    executive_brief = sections.get("executive_brief", [])
    macro_lines = _lines_from_section(sections, "macro", True)
    news_lines = _lines_from_section(sections, "news", True)
    portfolio_lines = _lines_from_section(sections, "portfolio", True)
    answer_parts = []

    if intent == "position risk" and tickers:
        answer_parts.append(_position_risk_answer(tickers, sections))

    elif intent == "macro impact":
        impact = _first_field(executive_summary, ("Theme Impact",))
        macro = source_answers.get("Macro Agent", "")
        answer_parts.append(
            f"Macro impact is led by {macro} {impact or ''}".strip()
        )
        rates_summary = _rates_exposure_summary(sections)

        if rates_summary:
            answer_parts.append(rates_summary)

    elif intent == "market/news impact":
        market = _first_field(executive_brief, ("Market Watch",))
        reason = _first_field(news_lines, ("Top Narrative Reason",))
        impact = _first_field(executive_summary, ("Theme Impact",))
        answer_parts.append(
            f"Market/news impact is led by {market or 'the top market narrative'}."
        )

        if reason:
            answer_parts.append(reason)

        if impact:
            answer_parts.append(impact)

    elif intent == "research quality":
        weakest = _first_field(
            _report_section(
                _lines_from_section(sections, "research", True),
                "RESEARCH AGENT EXECUTIVE BRIEF"
            ),
            ("Lowest Conviction Holding",)
        ) or _field_value(
            _lines_from_section(sections, "research", True),
            "Lowest Conviction Holding"
        )
        answer_parts.append(source_answers.get("Research Agent", ""))

        if weakest:
            answer_parts.append(f"Lowest conviction holding: {weakest}.")

    elif intent == "theme/conflict review":
        conflict = _first_field(executive_summary, ("Key Conflict",))
        reason = _first_field(executive_summary, ("Conflict Reason",))
        conflict_summary = _compact_lines(
            sections.get("theme_conflict_summary", [])
            + sections.get("theme_conflict_details", []),
            limit=8
        )
        answer_parts.append(
            f"Biggest conflict: {conflict or 'None identified.'}"
        )

        if reason:
            answer_parts.append(reason)

        answer_parts.append(conflict_summary)

    elif intent == "allocation/concentration review":
        answer_parts.append(source_answers.get("Portfolio Manager", ""))
        conflict = _first_field(executive_summary, ("Key Conflict",))

        if conflict:
            answer_parts.append(f"Related conflict: {conflict}.")

        answer_parts.append(_rates_exposure_summary(sections))

    elif intent == "portfolio risk":
        answer_parts.append(source_answers.get("Portfolio Manager", ""))
        answer_parts.append(source_answers.get("Macro Agent", ""))
        answer_parts.append(source_answers.get("Research Agent", ""))

    else:
        top_priority = _first_field(executive_summary, ("Top Priority",))
        market = _first_field(executive_brief, ("Market Watch",))
        macro = _first_field(executive_brief, ("Macro Backdrop",))
        risk = _first_field(executive_brief, ("Portfolio Risk",))
        answer_parts.append(
            f"Top priority is {top_priority or 'none identified'}."
        )

        if risk:
            answer_parts.append(f"Portfolio risk: {risk}.")

        if macro:
            answer_parts.append(f"Macro backdrop: {macro}.")

        if market:
            answer_parts.append(f"Market watch: {market}.")

    if intent in {"macro impact", "allocation/concentration review"}:
        text = " ".join(
            " ".join(str(part or "").split())
            for part in answer_parts
        )
        lowered = text.casefold()

        if "rate" in lowered or "fed" in lowered or "inflation" in lowered:
            answer_parts.append(
                "Conclusion: monitor rates, inflation, and growth-sensitive "
                "portfolio exposure."
            )

    if not answer_parts:
        answer_parts.append(
            "Echo found no supported deterministic multi-agent conclusion."
        )

    return _concise(" ".join(part for part in answer_parts if part), limit=1200)


def answer_echo_multi_agent_query(query, context=None):

    query_context = _query_context(context)
    sections = query_context["sections"]
    normalized_query = " ".join(str(query or "").split())
    intent = classify_echo_multi_agent_intent(normalized_query, sections)
    tickers = _detect_query_tickers(normalized_query, sections)

    if not normalized_query:
        return {
            "agent_name": "Echo",
            "query": "",
            "status": "EMPTY_QUERY",
            "routed_agents": [],
            "answer": "Query cannot be empty.",
            "confidence": "LOW",
            "source_answers": {},
            "requires_full_report": False,
            "notes": "Provide a non-empty query for Echo."
        }

    if not _echo_multi_agent_supported_intent(intent):
        return {
            "agent_name": "Echo",
            "query": normalized_query,
            "status": "UNSUPPORTED_QUERY",
            "routed_agents": [],
            "answer": (
                "Echo multi-agent response engine supports position risk, "
                "portfolio risk, macro impact, market/news impact, research "
                "quality, theme/conflict review, allocation/concentration "
                "review, and general top-priority review."
            ),
            "confidence": "LOW",
            "source_answers": {},
            "requires_full_report": False,
            "notes": "No deterministic multi-agent query intent matched."
        }

    route_plan = _multi_agent_route_plan(intent, tickers)
    source_answers = _source_answer_map(route_plan, query_context)
    answer = _echo_multi_agent_conclusion(
        intent,
        tickers,
        sections,
        source_answers
    )
    routed_agents = [agent_name for agent_name, _ in route_plan]
    confidence = "HIGH" if source_answers else "LOW"

    if intent == "position risk" and not tickers:
        confidence = "MEDIUM"

    return {
        "agent_name": "Echo",
        "query": normalized_query,
        "status": "ANSWERED",
        "routed_agents": routed_agents,
        "answer": answer,
        "confidence": confidence,
        "source_answers": source_answers,
        "requires_full_report": True,
        "notes": (
            "Echo multi-agent response engine used deterministic routing; "
            "no AI/LLM commentary or external APIs were used."
        )
    }


def answer_agent_query(agent_name, query, context=None):

    normalized_query = " ".join(str(query or "").split())
    normalized_agent_name = normalize_agent_name(agent_name)

    if normalized_agent_name == "Echo":
        if not normalized_query:
            return _query_result(
                "Echo",
                "",
                "EMPTY_QUERY",
                "Query cannot be empty.",
                "LOW",
                False,
                "Provide a non-empty query for Echo."
            )

        if _should_route_echo_multi_agent(normalized_query, context):
            return answer_echo_multi_agent_query(normalized_query, context)

        return answer_echo_query(normalized_query, context)

    agent = get_agent_by_name(agent_name)

    if agent is None:
        return {
            "agent_name": normalized_agent_name,
            "query": normalized_query,
            "status": "UNKNOWN_AGENT",
            "answer": "Agent not found.",
            "confidence": "LOW",
            "requires_full_report": False,
            "notes": "No registry entry matched the requested agent."
        }

    if not normalized_query:
        return {
            "agent_name": agent["agent_name"],
            "query": "",
            "status": "EMPTY_QUERY",
            "answer": "Query cannot be empty.",
            "confidence": "LOW",
            "requires_full_report": False,
            "notes": "Provide a non-empty query for this agent."
        }

    if agent["query_mode"] == "PLANNED":
        return _query_result(
            agent["agent_name"],
            normalized_query,
            "QUERY_MODE_PLANNED",
            "Query mode is planned for this agent but not yet implemented.",
            "LOW",
            False,
            "Placeholder agents remain planned in Phase 85."
        )

    if agent["query_mode"] == "NOT_SUPPORTED":
        return _query_result(
            agent["agent_name"],
            normalized_query,
            "QUERY_MODE_NOT_SUPPORTED",
            "Query mode is not supported for this agent.",
            "LOW",
            False,
            "This agent has no deterministic query interface."
        )

    answerers = {
        "Portfolio Manager": answer_portfolio_query,
        "Macro Agent": answer_macro_query,
        "News Agent": answer_news_query,
        "Research Agent": answer_research_query
    }
    answerer = answerers.get(agent["agent_name"])

    if answerer is None:
        return _query_result(
            agent["agent_name"],
            normalized_query,
            "QUERY_MODE_NOT_SUPPORTED",
            "No deterministic query handler is available for this agent.",
            "LOW",
            False,
            "Supported handlers exist for active report agents only."
        )

    return answerer(normalized_query, context)


def _echo_tool_context(context=None):

    return _query_context(context)


def _echo_tool_response(tool, data, summary, confidence="HIGH", notes=""):

    return {
        "tool": tool,
        "status": "OK",
        "data": data,
        "summary": _concise(summary, limit=900),
        "confidence": confidence,
        "notes": notes or (
            "Returned from Echo deterministic reports and query functions."
        )
    }


def _echo_tool_lines(context, key, full_report=False):

    return _lines_from_section(_echo_tool_context(context)["sections"], key,
                               full_report)


def _echo_tool_field(lines, *labels):

    return _first_field(lines, labels)


def echo_get_daily_brief(context=None):

    sections = _echo_tool_context(context)["sections"]
    executive_brief = sections.get("executive_brief", [])
    executive_summary = sections.get("executive_summary", [])
    action_queue = _numbered_after(executive_summary, "Priority Action Queue:")
    top_priority = _echo_tool_field(executive_summary, "Top Priority")
    dominant_theme = _echo_tool_field(
        executive_summary,
        "Dominant Cross-Agent Theme"
    )
    market_watch = _echo_tool_field(executive_brief, "Market Watch")
    macro_backdrop = _echo_tool_field(executive_brief, "Macro Backdrop")
    portfolio_risk = _echo_tool_field(executive_brief, "Portfolio Risk")
    worst_stress = (
        _echo_tool_field(executive_brief, "Worst Stress Scenario")
        or _echo_tool_field(executive_summary, "Worst Stress Scenario")
    )
    data = {
        "top_priority": top_priority,
        "dominant_theme": dominant_theme,
        "portfolio_risk": portfolio_risk,
        "worst_stress_scenario": worst_stress,
        "macro_backdrop": macro_backdrop,
        "market_watch": market_watch,
        "action_queue": action_queue,
        "executive_brief": executive_brief,
        "executive_summary": executive_summary
    }
    summary = (
        f"Top priority: {top_priority or 'None identified.'} "
        f"Dominant theme: {dominant_theme or 'None identified.'} "
        f"Worst stress scenario: {worst_stress or 'None identified.'} "
        f"Market watch: {market_watch or 'None identified.'}"
    )
    return _echo_tool_response(
        "echo_get_daily_brief",
        data,
        summary,
        "HIGH",
        "Latest/generated Echo briefing summary."
    )


def echo_get_state(context=None):

    state = build_echo_state(_echo_tool_context(context))
    data = {
        "state": state
    }
    summary = (
        "Top priority: "
        f"{(state.get('top_priority') or {}).get('title') or 'None identified.'} "
        "Dominant theme: "
        f"{(state.get('dominant_theme') or {}).get('theme_title') or 'None identified.'}"
    )

    return _echo_tool_response(
        "echo_get_state",
        data,
        summary,
        "HIGH",
        "Compressed Echo state generated from deterministic reports."
    )


def echo_get_state_delta(context=None):

    delta = read_state_delta()
    summary_data = delta.get("summary") or {}
    material_count = summary_data.get("material_change_count") or 0
    top_change = summary_data.get("top_change") or {}
    summary = (
        f"Material changes: {material_count}. "
        "Top change: "
        f"{top_change.get('field') or 'None'}."
    )

    return _echo_tool_response(
        "echo_get_state_delta",
        {"delta": delta},
        summary,
        "HIGH",
        "Latest compressed Echo state delta from generated state files."
    )


def echo_get_state_history(context=None):

    history = read_state_history()
    summary_data = history.get("summary") or {}
    stability = history.get("state_stability") or {}
    summary = (
        f"State samples: {history.get('sample_count') or 0}. "
        "Most common priority: "
        f"{summary_data.get('most_common_priority') or 'None'}. "
        "Priority changes: "
        f"{stability.get('priority_changed_count') or 0}."
    )

    return _echo_tool_response(
        "echo_get_state_history",
        {"history": history},
        summary,
        "HIGH",
        "Latest Echo historical state summary from generated history files."
    )


def echo_get_change_detection(context=None):

    detection = read_change_detection()
    summary_data = detection.get("summary") or {}
    top_signal = summary_data.get("top_signal") or {}
    summary = (
        f"Change level: {summary_data.get('change_level') or 'none'}. "
        "Top signal: "
        f"{top_signal.get('name') or 'None'}."
    )

    return _echo_tool_response(
        "echo_get_change_detection",
        {"change_detection": detection},
        summary,
        "HIGH",
        "Latest Echo ranked state-change signal from generated state files."
    )


def echo_get_knowledge_graph(context=None):

    graph = read_knowledge_graph()
    summary_data = graph.get("summary") or {}
    top_nodes = summary_data.get("top_connected_nodes") or []
    top_node = top_nodes[0] if top_nodes else {}
    summary = (
        f"Nodes: {summary_data.get('node_count') or 0}. "
        f"Edges: {summary_data.get('edge_count') or 0}. "
        "Most connected: "
        f"{top_node.get('label') or 'None'}."
    )

    return _echo_tool_response(
        "echo_get_knowledge_graph",
        {"knowledge_graph": graph},
        summary,
        "HIGH",
        "Latest deterministic Echo relationship memory graph."
    )


def _apply_memory_context_budget(memory_context, context_budget):

    if not isinstance(memory_context, dict):
        return {}

    if not isinstance(context_budget, dict):
        return memory_context

    try:
        max_items = int(context_budget.get("max_context_items") or 0)
    except (TypeError, ValueError):
        max_items = 0

    if max_items <= 0:
        return memory_context

    capped = json.loads(json.dumps(memory_context, default=str))
    operating = capped.get("operating_context")

    if not isinstance(operating, dict):
        return capped

    included = 0
    current_state = operating.get("current_state")
    if isinstance(current_state, dict):
        current_items = list(current_state.items())
        operating["current_state"] = dict(current_items[:max_items])
        included += len(operating["current_state"])

    for key in (
        "important_changes",
        "persistent_patterns",
        "top_signals",
        "connected_entities",
        "recommended_attention"
    ):
        values = operating.get(key)

        if not isinstance(values, list):
            continue

        remaining = max(max_items - included, 0)
        operating[key] = values[:remaining]
        included += len(operating[key])

    capped["context_budget"] = {
        "max_items": max_items,
        "included_items": min(included, max_items),
        "excluded_items": max(
            (
                (memory_context.get("context_budget") or {}).get(
                    "included_items",
                    0
                )
                - min(included, max_items)
            ),
            0
        )
    }

    return capped


def echo_get_memory_context(context=None):

    memory_context = read_memory_context()
    context_budget = (
        context.get("context_budget")
        if isinstance(context, dict)
        else None
    )

    if isinstance(context_budget, dict):
        memory_context = _apply_memory_context_budget(
            memory_context,
            context_budget
        )

    summary_data = memory_context.get("summary") or {}
    summary = (
        f"Top priority: {summary_data.get('top_priority') or 'None'}. "
        f"Change level: {summary_data.get('change_level') or 'none'}. "
        f"Top signal: {summary_data.get('top_signal') or 'None'}. "
        f"Dominant cluster: {summary_data.get('dominant_cluster') or 'None'}."
    )

    return _echo_tool_response(
        "echo_get_memory_context",
        {"memory_context": memory_context},
        summary,
        "HIGH",
        "Primary compact Echo memory context loaded before full reports."
    )


def echo_get_context_budget(context=None):

    context_budget = (
        context.get("context_budget")
        if isinstance(context, dict)
        else None
    )

    if not isinstance(context_budget, dict):
        context_budget = read_context_budget()

    summary = (
        f"Query class: {context_budget.get('query_class') or 'unknown'}. "
        f"Budget level: {context_budget.get('budget_level') or 'standard'}. "
        f"Max context items: {context_budget.get('max_context_items') or 0}."
    )

    return _echo_tool_response(
        "echo_get_context_budget",
        {"context_budget": context_budget},
        summary,
        "HIGH",
        "Deterministic pre-LLM context budget for this query."
    )


def echo_get_agent_routing(context=None):

    agent_routing = (
        context.get("agent_routing")
        if isinstance(context, dict)
        else None
    )

    if not isinstance(agent_routing, dict):
        agent_routing = read_agent_routing()

    primary_agents = agent_routing.get("primary_agents") or []
    summary = (
        f"Routing mode: {agent_routing.get('routing_mode') or 'none'}. "
        f"Primary agents: {', '.join(primary_agents) or 'None'}. "
        f"Confidence: {agent_routing.get('confidence') or 'low'}."
    )

    return _echo_tool_response(
        "echo_get_agent_routing",
        {"agent_routing": agent_routing},
        summary,
        "HIGH",
        "Deterministic active-agent routing for this query."
    )


def echo_get_context_assembly(context=None):

    context_assembly = (
        context.get("context_assembly")
        if isinstance(context, dict)
        else None
    )

    if not isinstance(context_assembly, dict):
        context_assembly = read_context_assembly()

    summary_data = context_assembly.get("context_summary") or {}
    summary = (
        f"Assembly mode: {context_assembly.get('assembly_mode') or 'unknown'}. "
        f"Blocks: {summary_data.get('block_count') or 0}. "
        "Full reports included: "
        f"{bool(summary_data.get('full_reports_included'))}."
    )

    return _echo_tool_response(
        "echo_get_context_assembly",
        {"context_assembly": context_assembly},
        summary,
        "HIGH",
        "Deterministic final answer context assembled from memory, budget, and routing."
    )


def echo_get_response_composer(context=None):

    response_composer = (
        context.get("response_composer")
        if isinstance(context, dict)
        else None
    )

    if not isinstance(response_composer, dict):
        response_composer = read_response_composer()

    summary = (
        f"Response mode: {response_composer.get('response_mode') or 'fallback'}. "
        f"Used sources: {len(response_composer.get('used_sources') or [])}. "
        "Clean user-facing answer is available."
    )

    return _echo_tool_response(
        "echo_get_response_composer",
        {"response_composer": response_composer},
        summary,
        "HIGH",
        "Deterministic user-facing answer composed from assembled context."
    )


def echo_get_intent_reasoning(context=None):

    intent_reasoning = (
        context.get("intent_reasoning")
        if isinstance(context, dict)
        else None
    )

    if not isinstance(intent_reasoning, dict):
        intent_reasoning = read_intent_reasoning()

    summary = (
        "Reasoning intent: "
        f"{intent_reasoning.get('reasoning_intent') or 'unknown'}. "
        f"Depth: {intent_reasoning.get('reasoning_depth') or 'none'}. "
        f"Style: {intent_reasoning.get('answer_style') or 'brief'}."
    )

    return _echo_tool_response(
        "echo_get_intent_reasoning",
        {"intent_reasoning": intent_reasoning},
        summary,
        intent_reasoning.get("confidence", "MEDIUM").upper(),
        "Deterministic reasoning intent classification."
    )


def echo_ask(question, context=None):

    result = answer_echo_multi_agent_query(question, _echo_tool_context(context))
    status = "OK" if result.get("status") == "ANSWERED" else result.get(
        "status",
        "ERROR"
    )

    return {
        "tool": "echo_ask",
        "status": status,
        "data": {
            "question": " ".join(str(question or "").split()),
            "response": result,
            "routed_agents": result.get("routed_agents", []),
            "source_answers": result.get("source_answers", {})
        },
        "summary": _concise(result.get("answer", ""), limit=900),
        "confidence": result.get("confidence", "MEDIUM"),
        "notes": (
            "Called answer_echo_multi_agent_query using deterministic "
            "Echo routing."
        )
    }


def echo_ask_agent(agent, question, context=None):

    result = answer_agent_query(agent, question, _echo_tool_context(context))
    status = "OK" if result.get("status") == "ANSWERED" else result.get(
        "status",
        "ERROR"
    )

    return {
        "tool": "echo_ask_agent",
        "status": status,
        "data": {
            "agent": normalize_agent_name(agent),
            "question": " ".join(str(question or "").split()),
            "response": result
        },
        "summary": _concise(result.get("answer", ""), limit=900),
        "confidence": result.get("confidence", "MEDIUM"),
        "notes": "Called answer_agent_query for the requested agent."
    }


def echo_get_top_priority(context=None):

    sections = _echo_tool_context(context)["sections"]
    executive_summary = sections.get("executive_summary", [])
    top_priority = _echo_tool_field(executive_summary, "Top Priority")
    priority_source = _echo_tool_field(
        sections.get("priority_summary", []),
        "Priority Source"
    )
    action_queue = _numbered_after(executive_summary, "Priority Action Queue:")
    data = {
        "top_priority": top_priority,
        "priority_source": priority_source,
        "action_queue": action_queue,
        "priority_summary": sections.get("priority_summary", []),
        "priority_details": sections.get("priority_details", [])
    }
    summary = f"Top priority: {top_priority or 'None identified.'}"
    return _echo_tool_response(
        "echo_get_top_priority",
        data,
        summary,
        "HIGH"
    )


def echo_get_themes(context=None):

    sections = _echo_tool_context(context)["sections"]
    theme_summary = sections.get("theme_summary", [])
    theme_details = sections.get("theme_details", [])
    dominant_theme = _echo_tool_field(theme_summary, "Dominant Theme")
    dominant_score = _echo_tool_field(theme_summary, "Dominant Theme Score")
    theme_count = _echo_tool_field(theme_summary, "Theme Count")
    data = {
        "dominant_theme": dominant_theme,
        "dominant_theme_score": dominant_score,
        "theme_count": theme_count,
        "theme_summary": theme_summary,
        "theme_details": theme_details
    }
    summary = (
        f"Dominant theme: {dominant_theme or 'None identified.'} "
        f"Theme count: {theme_count or '0'}."
    )
    return _echo_tool_response("echo_get_themes", data, summary, "HIGH")


def echo_get_theme_impacts(context=None):

    sections = _echo_tool_context(context)["sections"]
    impact_summary = sections.get("theme_impact_summary", [])
    impact_details = sections.get("theme_impact_details", [])
    dominant_impact = _echo_tool_field(
        impact_summary,
        "Dominant Theme Impact"
    )
    dominant_tier = _echo_tool_field(impact_summary, "Dominant Impact Tier")
    mapped_themes = _echo_tool_field(impact_summary, "Mapped Themes")
    data = {
        "dominant_theme_impact": dominant_impact,
        "dominant_impact_tier": dominant_tier,
        "mapped_themes": mapped_themes,
        "theme_impact_summary": impact_summary,
        "theme_impact_details": impact_details
    }
    summary = dominant_impact or "No theme impact mappings detected."
    return _echo_tool_response(
        "echo_get_theme_impacts",
        data,
        summary,
        "HIGH"
    )


def echo_get_conflicts(context=None):

    sections = _echo_tool_context(context)["sections"]
    conflict_summary = sections.get("theme_conflict_summary", [])
    conflict_details = sections.get("theme_conflict_details", [])
    key_conflict = _echo_tool_field(conflict_summary, "Key Conflict")
    key_reason = _echo_tool_field(conflict_summary, "Key Conflict Reason")
    detected = _echo_tool_field(conflict_summary, "Detected Conflicts")
    high_conflicts = _echo_tool_field(conflict_summary, "High Conflicts")
    data = {
        "key_conflict": key_conflict,
        "key_conflict_reason": key_reason,
        "detected_conflicts": detected,
        "high_conflicts": high_conflicts,
        "theme_conflict_summary": conflict_summary,
        "theme_conflict_details": conflict_details
    }
    summary = (
        f"Key conflict: {key_conflict or 'None identified.'} "
        f"Detected conflicts: {detected or '0'}."
    )
    return _echo_tool_response("echo_get_conflicts", data, summary, "HIGH")


def echo_get_portfolio_snapshot(context=None):

    sections = _echo_tool_context(context)["sections"]
    portfolio = sections.get("portfolio")
    portfolio_lines = _lines_from_section(sections, "portfolio", True)
    executive_summary = sections.get("executive_summary", [])
    top_risk = (
        _echo_tool_field(executive_summary, "Top Portfolio Risk")
        or determine_top_portfolio_risk(portfolio)
    )
    worst_stress = _echo_tool_field(
        executive_summary,
        "Worst Stress Scenario"
    )
    opportunity = _echo_tool_field(
        executive_summary,
        "Top Portfolio Opportunity"
    )
    data = {
        "portfolio_risk": top_risk,
        "worst_stress_scenario": worst_stress,
        "allocation": _report_section(portfolio_lines, "TICKER ALLOCATION"),
        "rebalance_alerts": _report_section(portfolio_lines,
                                            "REBALANCE ALERTS"),
        "concentration_summary": _report_section(
            portfolio_lines,
            "CONCENTRATION RISK SUMMARY"
        ),
        "concentration_details": _report_section(
            portfolio_lines,
            "CONCENTRATION RISK DETAILS"
        ),
        "stress_test_summary": _report_section(
            portfolio_lines,
            "STRESS TEST SUMMARY"
        ),
        "opportunity": opportunity,
        "capital_deployment": _report_section(
            portfolio_lines,
            "CAPITAL DEPLOYMENT"
        )
    }
    summary = (
        f"Portfolio risk: {top_risk or 'None identified.'} "
        f"Opportunity: {opportunity or 'None identified.'}"
    )
    return _echo_tool_response(
        "echo_get_portfolio_snapshot",
        data,
        summary,
        "HIGH",
        "Snapshot uses Portfolio Manager report sections."
    )


def echo_get_macro_snapshot(context=None):

    macro_lines = _echo_tool_lines(context, "macro", True)
    data = {
        "current_macro_regime": _echo_tool_field(
            macro_lines,
            "Current Macro Regime"
        ),
        "top_macro_priority": _echo_tool_field(
            macro_lines,
            "Top Macro Priority"
        ),
        "top_macro_reason": _echo_tool_field(macro_lines,
                                             "Top Macro Reason"),
        "inflation_trend": _echo_tool_field(macro_lines, "Inflation Trend"),
        "policy_rate": _echo_tool_field(macro_lines, "Policy Rate"),
        "labor_market": _echo_tool_field(macro_lines, "Labor Market"),
        "yield_curve": _echo_tool_field(macro_lines, "Yield Curve"),
        "energy": _echo_tool_field(macro_lines, "Energy"),
        "ranked_macro_priority_signals": _report_section(
            macro_lines,
            "Ranked Macro Priority Signals:"
        ),
        "macro_indicators": _report_section(macro_lines, "Macro Indicators")
    }
    summary = (
        f"Macro regime: {data['current_macro_regime'] or 'Unknown'}. "
        f"Inflation: {data['inflation_trend'] or 'Unknown'}. "
        f"Rates: {data['policy_rate'] or 'Unknown'}."
    )
    return _echo_tool_response(
        "echo_get_macro_snapshot",
        data,
        summary,
        "HIGH"
    )


def echo_get_news_snapshot(context=None):

    news_lines = _echo_tool_lines(context, "news", True)
    data = {
        "top_market_narrative": _echo_tool_field(
            news_lines,
            "Top Market Narrative"
        ),
        "supporting_articles": _echo_tool_field(news_lines,
                                                "Supporting Articles"),
        "top_narrative_score": _echo_tool_field(news_lines,
                                                "Top Narrative Score"),
        "representative_headline": _echo_tool_field(
            news_lines,
            "Representative Headline"
        ),
        "top_narrative_reason": _echo_tool_field(
            news_lines,
            "Top Narrative Reason"
        ),
        "top_macro_story": _echo_tool_field(news_lines, "Top Macro Story"),
        "top_world_event_story": _echo_tool_field(
            news_lines,
            "Top World Event Story"
        ),
        "top_portfolio_story": _echo_tool_field(news_lines,
                                                "Top Portfolio Story"),
        "top_watchlist_story": _echo_tool_field(news_lines,
                                                "Top Watchlist Story")
    }
    summary = (
        f"Top market narrative: "
        f"{data['top_market_narrative'] or 'None identified.'}"
    )
    return _echo_tool_response(
        "echo_get_news_snapshot",
        data,
        summary,
        "HIGH"
    )


def echo_get_research_snapshot(context=None):

    research_lines = _echo_tool_lines(context, "research", True)
    portfolio_lines = _echo_tool_lines(context, "portfolio", True)
    research_health = (
        _report_section(research_lines, "RESEARCH HEALTH")
        + _report_section(portfolio_lines, "RESEARCH HEALTH")
    )
    weak_holdings = [
        line for line in research_health
        if "low conviction" in line.casefold()
    ]

    if not weak_holdings:
        weak_holdings = [
            line for line in research_lines + portfolio_lines
            if "low conviction" in line.casefold()
        ]

    data = {
        "weak_holdings": weak_holdings,
        "lowest_conviction_holding": _echo_tool_field(
            research_lines,
            "Lowest Conviction Holding"
        ),
        "top_research_priority": _echo_tool_field(
            research_lines,
            "Top Research Priority"
        ),
        "research_health": research_health,
        "research_gaps": (
            _report_section(research_lines, "RESEARCH GAPS")
            + _report_section(portfolio_lines, "RESEARCH GAPS")
        ),
        "watchlist_issues": [
            line for line in research_health
            if "watch" in line.casefold()
        ],
        "watchlist": (
            _report_section(research_lines, "WATCHLIST")
            + _report_section(portfolio_lines, "WATCHLIST")
        )
    }
    summary = (
        "Weak holdings: "
        f"{_compact_lines(weak_holdings, limit=4)}"
    )
    return _echo_tool_response(
        "echo_get_research_snapshot",
        data,
        summary,
        "HIGH"
    )


ECHO_TOOL_REGISTRY = {
    "echo_get_daily_brief": {
        "function_name": "echo_get_daily_brief",
        "description": "Return the latest/generated Echo briefing summary.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with top priority, dominant theme, market watch, "
            "macro backdrop, portfolio risk, and action queue."
        )
    },
    "echo_get_state": {
        "function_name": "echo_get_state",
        "description": "Return compressed Echo operating state.",
        "expected_input_fields": {},
        "output_description": (
            "JSON-serializable dictionary with top priority, dominant theme, "
            "portfolio, research, news, macro, conflicts, action queue, and "
            "risk register."
        )
    },
    "echo_get_state_delta": {
        "function_name": "echo_get_state_delta",
        "description": "Return latest compressed Echo state delta.",
        "expected_input_fields": {},
        "output_description": (
            "JSON-serializable dictionary with material changes, new risks, "
            "resolved risks, and major state field changes."
        )
    },
    "echo_get_state_history": {
        "function_name": "echo_get_state_history",
        "description": "Return historical Echo state movement summary.",
        "expected_input_fields": {},
        "output_description": (
            "JSON-serializable dictionary with priority, theme, macro, "
            "portfolio risk, risk frequency, action frequency, persistence, "
            "and stability history."
        )
    },
    "echo_get_change_detection": {
        "function_name": "echo_get_change_detection",
        "description": "Return ranked Echo state-change detection signals.",
        "expected_input_fields": {},
        "output_description": (
            "JSON-serializable dictionary with prioritized state-change "
            "signals, escalations, deescalations, and recommended attention."
        )
    },
    "echo_get_knowledge_graph": {
        "function_name": "echo_get_knowledge_graph",
        "description": "Return Echo deterministic knowledge graph.",
        "expected_input_fields": {},
        "output_description": (
            "JSON-serializable dictionary with relationship nodes, edges, "
            "clusters, entity index, and relationship index."
        )
    },
    "echo_get_memory_context": {
        "function_name": "echo_get_memory_context",
        "description": "Return Echo memory-first operating context.",
        "expected_input_fields": {},
        "output_description": (
            "Compact JSON-serializable context built from state, delta, "
            "history, change detection, and knowledge graph artifacts."
        )
    },
    "echo_get_context_budget": {
        "function_name": "echo_get_context_budget",
        "description": "Return deterministic query context budget.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with query class, budget level, max context items, "
            "preferred context sources, excluded sources, and tool hints."
        )
    },
    "echo_get_agent_routing": {
        "function_name": "echo_get_agent_routing",
        "description": "Return deterministic active-agent routing for a query.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with primary agents, secondary agents, excluded "
            "agents, routing mode, confidence, and agent context plan."
        )
    },
    "echo_get_context_assembly": {
        "function_name": "echo_get_context_assembly",
        "description": "Return deterministic final answer context assembly.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with assembly mode, included/excluded sources, "
            "context blocks, context summary, and assembly reason."
        )
    },
    "echo_get_response_composer": {
        "function_name": "echo_get_response_composer",
        "description": "Return deterministic clean user-facing response.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with response mode, answer, supporting points, "
            "caveats, used sources, and compact debug summary."
        )
    },
    "echo_get_intent_reasoning": {
        "function_name": "echo_get_intent_reasoning",
        "description": "Return deterministic reasoning intent classification.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with reasoning intent, depth, answer style, "
            "required context, detected entities, horizon, and instructions."
        )
    },
    "echo_ask": {
        "function_name": "echo_ask",
        "description": "Ask Echo one multi-agent deterministic question.",
        "expected_input_fields": {"question": "string"},
        "output_description": (
            "Dictionary containing the synthesized Echo answer, routed "
            "agents, and source answers."
        )
    },
    "echo_ask_agent": {
        "function_name": "echo_ask_agent",
        "description": "Ask one existing deterministic Echo agent.",
        "expected_input_fields": {
            "agent": "string",
            "question": "string"
        },
        "output_description": (
            "Dictionary containing the selected agent answer and metadata."
        )
    },
    "echo_get_top_priority": {
        "function_name": "echo_get_top_priority",
        "description": "Return Echo's current top priority.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with top priority, priority source, and action queue."
        )
    },
    "echo_get_themes": {
        "function_name": "echo_get_themes",
        "description": "Return dominant cross-agent themes.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with theme summary and theme detail report lines."
        )
    },
    "echo_get_theme_impacts": {
        "function_name": "echo_get_theme_impacts",
        "description": "Return theme-to-portfolio impact mappings.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with dominant theme impact, tier, and impact details."
        )
    },
    "echo_get_conflicts": {
        "function_name": "echo_get_conflicts",
        "description": "Return detected deterministic cross-agent conflicts.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with key conflict, conflict counts, and details."
        )
    },
    "echo_get_portfolio_snapshot": {
        "function_name": "echo_get_portfolio_snapshot",
        "description": "Return portfolio risk and allocation snapshot.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with risk, allocation, concentration, stress test, "
            "and opportunity data."
        )
    },
    "echo_get_macro_snapshot": {
        "function_name": "echo_get_macro_snapshot",
        "description": "Return macro regime and indicator snapshot.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with macro regime, inflation, rates, labor, yield "
            "curve, and energy."
        )
    },
    "echo_get_news_snapshot": {
        "function_name": "echo_get_news_snapshot",
        "description": "Return market narrative and news story snapshot.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with top narrative, supporting articles, and top "
            "macro/world/portfolio stories."
        )
    },
    "echo_get_research_snapshot": {
        "function_name": "echo_get_research_snapshot",
        "description": "Return research quality and watchlist snapshot.",
        "expected_input_fields": {},
        "output_description": (
            "Dictionary with weak holdings, conviction issues, research "
            "gaps, and watchlist issues."
        )
    }
}


def get_echo_tool_registry():

    return {
        name: dict(metadata)
        for name, metadata in ECHO_TOOL_REGISTRY.items()
    }


class BaseLLMProvider:

    provider_name = "base"

    def model_name(self):

        return ""

    def live_calls_enabled(self):

        return False

    def is_configured(self):

        return False

    def generate_response(self, messages, tools=None, context=None):

        raise NotImplementedError


class OpenAIProvider(BaseLLMProvider):

    provider_name = "openai"

    def model_name(self):

        return (
            os.getenv("ECHO_OPENAI_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        )

    def live_calls_enabled(self):

        return (
            _env_flag_enabled_any(("ECHO_LLM_LIVE", "LLM_LIVE_MODE"))
            and self.is_configured()
        )

    def is_configured(self):

        return bool(os.getenv("OPENAI_API_KEY"))

    def generate_response(self, messages, tools=None, context=None):

        model = self.model_name()
        tool_context = format_tool_context_for_llm(tools)

        if not self.is_configured():
            return {
                "status": "NOT_CONFIGURED",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": False,
                "confidence": "LOW",
                "notes": (
                    "OPENAI_API_KEY is not configured. No OpenAI API call "
                    "was made."
                )
            }

        if not self.live_calls_enabled():
            return {
                "status": "STUB",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": False,
                "confidence": "LOW",
                "notes": (
                    "OpenAI provider is configured but LLM live mode is not "
                    "enabled. No OpenAI API call was made."
                )
            }

        try:
            from openai import OpenAI
        except ImportError:
            return {
                "status": "DEPENDENCY_MISSING",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": False,
                "confidence": "LOW",
                "notes": "OpenAI package not installed. Run: pip install openai"
            }

        prompt_messages = _build_openai_prompt_messages(messages, tool_context)

        try:
            client = OpenAI()

            if hasattr(client, "responses"):
                response = client.responses.create(
                    model=model,
                    input=prompt_messages
                )
                answer = getattr(response, "output_text", "")
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=prompt_messages
                )
                answer = response.choices[0].message.content

            return {
                "status": "ANSWERED",
                "provider": self.provider_name,
                "model": model,
                "answer": " ".join(str(answer or "").split()),
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": True,
                "confidence": "HIGH" if tool_context else "MEDIUM",
                "notes": (
                    "OpenAI live response generated from Echo deterministic "
                    "tool context. No function-calling was used."
                )
            }
        except Exception as error:
            return {
                "status": "ERROR",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": True,
                "confidence": "LOW",
                "notes": (
                    "OpenAI provider call failed without exposing secrets: "
                    f"{_concise(error, limit=180)}"
                )
            }

class AnthropicProvider(BaseLLMProvider):

    provider_name = "anthropic"

    def model_name(self):

        return os.getenv("ANTHROPIC_MODEL") or "claude-3-5-haiku-latest"

    def live_calls_enabled(self):

        return (
            _env_flag_enabled_any(("LLM_LIVE_MODE", "ECHO_LLM_LIVE"))
            and self.is_configured()
        )

    def is_configured(self):

        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def generate_response(self, messages, tools=None, context=None):

        model = self.model_name()
        tool_context = format_tool_context_for_llm(tools)

        if not self.is_configured():
            return {
                "status": "NOT_CONFIGURED",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": False,
                "confidence": "LOW",
                "notes": (
                    "ANTHROPIC_API_KEY is not configured. No Anthropic API "
                    "call was made."
                )
            }

        if not self.live_calls_enabled():
            return {
                "status": "STUB",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": False,
                "confidence": "LOW",
                "notes": (
                    "Anthropic provider is configured but LLM live mode is "
                    "not enabled. No Anthropic API call was made."
                )
            }

        try:
            from anthropic import Anthropic, RateLimitError
        except ImportError:
            return {
                "status": "DEPENDENCY_MISSING",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": False,
                "confidence": "LOW",
                "notes": (
                    "Anthropic package not installed. Run: pip install "
                    "anthropic"
                )
            }

        prompt_message = _build_anthropic_prompt_message(messages, tool_context)

        try:
            client = Anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=800,
                system=build_echo_llm_system_prompt(),
                messages=[{"role": "user", "content": prompt_message}]
            )
            answer_parts = []

            for block in getattr(response, "content", []) or []:
                text = getattr(block, "text", "")

                if text:
                    answer_parts.append(text)

            answer = " ".join(" ".join(answer_parts).split())

            return {
                "status": "ANSWERED",
                "provider": self.provider_name,
                "model": model,
                "answer": answer,
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": True,
                "confidence": "HIGH" if tool_context else "MEDIUM",
                "notes": (
                    "Anthropic live response generated from Echo assembled "
                    "context and deterministic response composer output. "
                    "Claude did not bypass Echo orchestration."
                )
            }
        except RateLimitError as error:
            return {
                "status": "RATE_LIMITED",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": True,
                "confidence": "LOW",
                "notes": (
                    "Anthropic provider rate limited the request without "
                    "exposing secrets: "
                    f"{_concise(_redact_secret_text(error), limit=180)}"
                )
            }
        except Exception as error:
            return {
                "status": "ERROR",
                "provider": self.provider_name,
                "model": model,
                "answer": "",
                "tool_context_used": bool(tool_context),
                "tool_context_char_count": len(tool_context),
                "live_call_attempted": True,
                "confidence": "LOW",
                "notes": (
                    "Anthropic provider call failed without exposing "
                    "secrets: "
                    f"{_concise(_redact_secret_text(error), limit=180)}"
                )
            }


class UnknownLLMProvider(BaseLLMProvider):

    def __init__(self, provider_name):

        self.provider_name = provider_name or "unknown"

    def is_configured(self):

        return False

    def generate_response(self, messages, tools=None, context=None):

        return {
            "status": "UNKNOWN_PROVIDER",
            "provider": self.provider_name,
            "configured": False,
            "live_calls_enabled": False,
            "message_count": len(messages or []),
            "tool_count": len(tools or []),
            "response": "Unsupported LLM provider.",
            "notes": "No external API call was made."
        }


def _env_flag_enabled(name):

    return str(os.getenv(name) or "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "on"
    }


def _env_flag_enabled_any(names):

    return any(_env_flag_enabled(name) for name in names or ())


def _build_llm_tool_context(tools):

    if not isinstance(tools, dict):
        return {}

    tool_context = {}

    for tool_name, result in tools.items():
        if not isinstance(result, dict):
            continue

        tool_context[tool_name] = {
            "status": result.get("status"),
            "summary": result.get("summary"),
            "confidence": result.get("confidence"),
            "data": result.get("data", {})
        }

    return tool_context


def build_echo_llm_system_prompt():

    return "\n".join([
        "You are Echo, a personal chief-of-staff interface over deterministic tools.",
        "Ground operating, portfolio, macro, news, and research answers in the provided Echo tool context.",
        "For casual conversation, greetings, thanks, or harmless creative prompts, respond naturally and do not force an agent report.",
        "Use reasoning intent to decide whether to retrieve, explain, analyze a scenario, critique, prioritize, recommend, or converse.",
        "Treat the deterministic response composer answer as a reference draft, not the final answer.",
        "Clearly separate known tool facts from inference or judgment.",
        "Do not invent portfolio holdings, news, macro data, prices, or research conclusions.",
        "If the tool context is insufficient, say what is missing.",
        "Do not provide personalized financial advice as a directive.",
        "You may frame risks, tradeoffs, exposures, and review areas.",
        "Avoid unsupported buy/sell instructions.",
        "Be concise, direct, and decision-useful."
    ])


_SECRET_KEY_TERMS = ("api", "key", "secret", "token", "password")


def _looks_like_secret_key_name(key_name):

    normalized = re.sub(r"[^a-z0-9]+", "_", str(key_name or "").casefold())
    parts = {part for part in normalized.split("_") if part}
    return bool(parts & set(_SECRET_KEY_TERMS)) or normalized.endswith("_key")


def _redact_secret_text(text):

    redacted = str(text or "")
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]{12,}", "[REDACTED]", redacted)
    redacted = re.sub(
        r"(?i)(OPENAI_API_KEY|ANTHROPIC_API_KEY|API_KEY)\s*=\s*\S+",
        r"\1=[REDACTED]",
        redacted
    )
    return redacted


def _redact_secret_values(value, key_name=""):

    if _looks_like_secret_key_name(key_name):
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            key: _redact_secret_values(item, key)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_redact_secret_values(item, key_name) for item in value]

    if isinstance(value, tuple):
        return tuple(_redact_secret_values(item, key_name) for item in value)

    if isinstance(value, str):
        return _redact_secret_text(value)

    return value


def _compact_llm_context_value(value, depth=0):

    if depth >= 4:
        return _concise(value, limit=240)

    if isinstance(value, dict):
        compact = {}

        for key, item in value.items():
            key_text = str(key or "").casefold()

            if any(
                term in key_text
                for term in ("raw", "full_report", "report_text", "transcript")
            ):
                continue

            compact[key] = _compact_llm_context_value(item, depth + 1)

        return compact

    if isinstance(value, list):
        compact_items = [
            _compact_llm_context_value(item, depth + 1)
            for item in value[:12]
        ]

        if len(value) > 12:
            compact_items.append(f"... truncated {len(value) - 12} items")

        return compact_items

    if isinstance(value, tuple):
        return _compact_llm_context_value(list(value), depth)

    if isinstance(value, str):
        return _concise(_redact_secret_text(value), limit=700)

    return value


def format_tool_context_for_llm(orchestrator_result, max_chars=12000):

    if not isinstance(orchestrator_result, dict):
        return ""

    if "tool_results" in orchestrator_result:
        selected_tools = orchestrator_result.get("selected_tools", [])
        tool_results = orchestrator_result.get("tool_results", {})
    else:
        selected_tools = list(orchestrator_result)
        tool_results = orchestrator_result

    formatted = {
        "selected_tools": selected_tools,
        "context_budget": orchestrator_result.get("context_budget", {}),
        "agent_routing": orchestrator_result.get("agent_routing", {}),
        "context_assembly": orchestrator_result.get("context_assembly", {}),
        "intent_reasoning": orchestrator_result.get("intent_reasoning", {}),
        "response_composer": orchestrator_result.get("response_composer", {}),
        "tool_summaries": {},
        "tool_data": {}
    }

    if isinstance(tool_results, dict):
        for tool_name, result in tool_results.items():
            if not isinstance(result, dict):
                continue

            formatted["tool_summaries"][tool_name] = {
                "status": result.get("status"),
                "summary": _concise(result.get("summary", ""), limit=700),
                "confidence": result.get("confidence"),
                "notes": _concise(result.get("notes", ""), limit=350)
            }
            formatted["tool_data"][tool_name] = _compact_llm_context_value(
                result.get("data", {})
            )

    formatted = _redact_secret_values(formatted)
    text = json.dumps(formatted, ensure_ascii=True, sort_keys=True, default=str)
    text = _redact_secret_text(text)

    if len(text) > max_chars:
        suffix = "\n... Echo tool context truncated to fit LLM budget."
        return text[:max_chars - len(suffix)] + suffix

    return text


def _llm_provider_payload(orchestrator_result):

    if not isinstance(orchestrator_result, dict):
        return {}

    return {
        "selected_tools": orchestrator_result.get("selected_tools", []),
        "context_budget": orchestrator_result.get("context_budget", {}),
        "agent_routing": orchestrator_result.get("agent_routing", {}),
        "context_assembly": orchestrator_result.get(
            "context_assembly",
            {}
        ),
        "intent_reasoning": orchestrator_result.get("intent_reasoning", {}),
        "response_composer": orchestrator_result.get(
            "response_composer",
            {}
        ),
        "tool_results": orchestrator_result.get("tool_results", {})
    }


_UNSUPPORTED_LLM_PHRASES = (
    "guaranteed",
    "risk-free",
    "you should buy",
    "you should sell",
    "definitely"
)


_NON_TICKER_TOKENS = {
    "AI",
    "API",
    "CPI",
    "ETF",
    "ECHO",
    "FED",
    "FRED",
    "GDP",
    "HIGH",
    "LLM",
    "LOW",
    "MEDIUM",
    "N/A",
    "OK",
    "PM",
    "US",
    "USA",
    "WTI"
}


def _ticker_tokens(text):

    tokens = re.findall(r"\b[A-Z][A-Z0-9.]{1,5}\b", str(text or ""))
    return {
        token
        for token in tokens
        if token not in _NON_TICKER_TOKENS
        and not token.isdigit()
    }


def validate_llm_response(answer, tool_context):

    warnings = []
    normalized_answer = " ".join(str(answer or "").split())
    lower_answer = normalized_answer.casefold()

    if not normalized_answer:
        warnings.append("LLM answer is empty.")

    for phrase in _UNSUPPORTED_LLM_PHRASES:
        if phrase in lower_answer:
            warnings.append(
                f"LLM answer contains unsupported phrase: {phrase}."
            )

    if len(normalized_answer) > 4000:
        warnings.append("LLM answer exceeds the response length budget.")

    context_tickers = _ticker_tokens(tool_context)
    answer_tickers = _ticker_tokens(normalized_answer)
    unknown_tickers = sorted(answer_tickers - context_tickers)
    outside_context_terms = (
        "outside context",
        "outside the context",
        "not in the tool context",
        "not found in the tool context",
        "unknown",
        "insufficient context",
        "not enough context",
        "do not own",
        "not shown"
    )

    if unknown_tickers and not any(term in lower_answer for term in outside_context_terms):
        warnings.append(
            "LLM answer mentions tickers not present in Echo tool context: "
            + ", ".join(unknown_tickers)
            + "."
        )

    fallback_required = bool(warnings)

    return {
        "valid": not fallback_required,
        "warnings": warnings,
        "fallback_required": fallback_required
    }


def _message_content(messages):

    if isinstance(messages, str):
        return messages

    if isinstance(messages, (list, tuple)):
        parts = []

        for message in messages:
            if isinstance(message, dict):
                content = message.get("content")
            else:
                content = message

            if content:
                parts.append(str(content))

        return "\n".join(parts)

    return str(messages or "")


def _build_openai_prompt_messages(messages, tool_context):

    system_message = build_echo_llm_system_prompt()
    tool_context_text = str(tool_context or "")
    user_message = (
        f"User question:\n{_message_content(messages)}\n\n"
        f"Echo reasoning/context package:\n{tool_context_text}\n\n"
        "Answer the user's actual question using reasoning_intent, "
        "reasoning_depth, answer_style, reasoning_instructions, assembled "
        "context, and tool summaries. The response_composer answer is a "
        "grounding reference only, not the final answer. Use risk, exposure, "
        "monitor, review, and tradeoff framing. Do not issue unsupported buy "
        "or sell directives."
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]


def _build_anthropic_prompt_message(messages, tool_context):

    return (
        f"User question:\n{_message_content(messages)}\n\n"
        "Echo reasoning intent, assembled context, and deterministic "
        "response composer reference:\n"
        f"{str(tool_context or '')}\n\n"
        "Answer the user's actual question using reasoning_intent, "
        "reasoning_depth, answer_style, and reasoning_instructions. Treat "
        "response_composer.answer as a grounding aid only, not the final "
        "answer. Do not introduce facts, holdings, prices, recommendations, "
        "or conclusions outside the provided Echo context. Preserve caveats "
        "where context is incomplete."
    )


def _response_metadata(provider_name, provider_model, live_call_attempted,
                       fallback_used, response_source, provider_status,
                       context_budget, agent_routing, context_assembly,
                       intent_reasoning=None):

    intent_reasoning = (
        intent_reasoning
        if isinstance(intent_reasoning, dict)
        else {}
    )

    return {
        "llm_provider": provider_name,
        "model": provider_model,
        "live_call_attempted": bool(live_call_attempted),
        "fallback_used": bool(fallback_used),
        "response_source": response_source,
        "provider_status": provider_status,
        "query_class": (
            context_budget.get("query_class")
            if isinstance(context_budget, dict)
            else None
        ),
        "routing_mode": (
            agent_routing.get("routing_mode")
            if isinstance(agent_routing, dict)
            else None
        ),
        "assembly_mode": (
            context_assembly.get("assembly_mode")
            if isinstance(context_assembly, dict)
            else None
        ),
        "reasoning_intent": intent_reasoning.get("reasoning_intent"),
        "reasoning_depth": intent_reasoning.get("reasoning_depth"),
        "answer_style": intent_reasoning.get("answer_style")
    }


def _reasoning_fallback_answer(fallback_answer, intent_reasoning,
                               context_assembly):

    intent = (
        intent_reasoning.get("reasoning_intent")
        if isinstance(intent_reasoning, dict)
        else ""
    )

    if intent not in {"scenario_analysis", "explanation", "critique"}:
        return fallback_answer

    blocks = (
        context_assembly.get("context_blocks")
        if isinstance(context_assembly, dict)
        else []
    )
    relevant = []

    for block in blocks or []:
        if not isinstance(block, dict):
            continue

        title = " ".join(str(block.get("title") or "").split())
        content = _concise(block.get("content", ""), limit=180)

        if title or content:
            relevant.append(
                f"{title}: {content}".strip(": ")
            )

        if len(relevant) == 2:
            break

    context_text = (
        " | ".join(relevant)
        if relevant
        else _concise(fallback_answer, limit=220)
    )

    return (
        "This requires reasoning beyond deterministic fallback. "
        f"Relevant context: {context_text}"
    )


def _normalize_llm_provider_name(provider_name=None):

    configured_provider = (
        os.getenv("LLM_PROVIDER")
        or os.getenv("ECHO_LLM_PROVIDER")
    )
    provider = provider_name or configured_provider or "openai"
    return " ".join(str(provider or "").split()).casefold() or "openai"


def get_llm_provider(provider_name=None):

    provider = _normalize_llm_provider_name(provider_name)

    if provider == "openai":
        return OpenAIProvider()

    if provider == "anthropic":
        return AnthropicProvider()

    return UnknownLLMProvider(provider)


def get_llm_provider_status(provider_name=None):

    provider = get_llm_provider(provider_name)
    live_enabled = provider.live_calls_enabled()

    return {
        "status": "OK",
        "active_provider": provider.provider_name,
        "configured": provider.is_configured(),
        "live_calls_enabled": live_enabled,
        "model": provider.model_name(),
        "available_providers": ["openai", "anthropic"],
        "notes": (
            "LLM provider layer is active. Live calls require provider "
            "configuration plus LLM_LIVE_MODE=1/true/yes or "
            "ECHO_LLM_LIVE=1/true/yes."
        )
    }


AGENT_ROUTING_TOOL_MAP = {
    "portfolio": "echo_get_portfolio_snapshot",
    "research": "echo_get_research_snapshot",
    "news": "echo_get_news_snapshot",
    "macro": "echo_get_macro_snapshot"
}


def _context_assembly_reports(context):

    sections = _echo_tool_context(context)["sections"]

    return {
        "portfolio": sections.get("portfolio"),
        "research": sections.get("research"),
        "news": sections.get("news"),
        "macro": sections.get("macro"),
        "executive": {
            "executive_brief": sections.get("executive_brief", []),
            "summary": sections.get("executive_summary", [])
        }
    }


def _agent_routing_tools(agent_routing, include_secondary=True):

    if not isinstance(agent_routing, dict):
        return []

    agents = list(agent_routing.get("primary_agents") or [])

    if include_secondary:
        agents.extend(agent_routing.get("secondary_agents") or [])

    tools = []

    for agent in agents:
        tool_name = AGENT_ROUTING_TOOL_MAP.get(agent)

        if tool_name and tool_name not in tools:
            tools.append(tool_name)

    return tools


def _echo_orchestrator_select_tools(message, context, context_budget=None,
                                    agent_routing=None):

    sections = _echo_tool_context(context)["sections"]
    text = " ".join(str(message or "").split()).casefold()
    tickers = _detect_query_tickers(message, sections)
    selected_tools = []
    budget_level = (
        (context_budget or {}).get("budget_level")
        if isinstance(context_budget, dict)
        else None
    )
    query_class = (
        (context_budget or {}).get("query_class")
        if isinstance(context_budget, dict)
        else None
    )

    def add_tools(*tool_names):
        for tool_name in tool_names:
            if tool_name not in selected_tools:
                selected_tools.append(tool_name)

    add_tools(
        "echo_get_context_budget",
        "echo_get_agent_routing",
        "echo_get_memory_context",
        "echo_get_context_assembly",
        "echo_get_response_composer",
        "echo_get_intent_reasoning"
    )

    if query_class in {"simple", "conversational"}:
        return selected_tools

    if isinstance(context_budget, dict):
        for tool_name in context_budget.get("tool_hints") or []:
            add_tools(tool_name)

    if isinstance(agent_routing, dict):
        include_secondary = budget_level in {"expanded", "full"}
        add_tools(*_agent_routing_tools(agent_routing, include_secondary))

        if agent_routing.get("routing_mode") in {"multi_agent", "all_agents"}:
            add_tools("echo_get_themes", "echo_get_conflicts")

        if query_class in {"multi_agent", "deep_dive"}:
            add_tools("echo_get_change_detection", "echo_get_knowledge_graph")

    if tickers:
        add_tools(
            "echo_ask",
            "echo_get_themes",
            "echo_get_conflicts"
        )

    if any(
        term in text
        for term in (
            "connect",
            "connected",
            "connection",
            "connections",
            "graph",
            "knowledge graph",
            "relationship",
            "relationships",
            "linked",
            "links",
            "relates",
            "related",
            "cluster",
            "clusters"
        )
    ):
        add_tools(
            "echo_get_knowledge_graph",
            "echo_get_change_detection"
        )

    if not isinstance(agent_routing, dict) and any(
        term in text
        for term in (
            "risk",
            "exposure",
            "allocation",
            "concentration",
            "overweight",
            "underweight"
        )
    ):
        add_tools(
            "echo_get_portfolio_snapshot",
            "echo_get_conflicts",
            "echo_get_theme_impacts"
        )

    if not isinstance(agent_routing, dict) and any(
        term in text
        for term in (
            "macro",
            "inflation",
            "rates",
            "rate",
            "yield",
            "energy",
            "fed"
        )
    ):
        add_tools(
            "echo_get_macro_snapshot",
            "echo_get_themes",
            "echo_get_theme_impacts"
        )

    if not isinstance(agent_routing, dict) and any(
        term in text
        for term in ("news", "market", "world", "iran", "china")
    ):
        add_tools("echo_get_news_snapshot", "echo_get_themes")

    if not isinstance(agent_routing, dict) and any(
        term in text
        for term in ("research", "conviction", "thesis", "weak holding")
    ):
        add_tools("echo_get_research_snapshot", "echo_get_conflicts")

    if selected_tools == [
        "echo_get_context_budget",
        "echo_get_agent_routing",
        "echo_get_memory_context",
        "echo_get_context_assembly",
        "echo_get_response_composer",
        "echo_get_intent_reasoning"
    ]:
        add_tools(
            "echo_get_top_priority",
            "echo_get_themes"
        )

    if budget_level == "minimal":
        selected_tools = [
            tool_name for tool_name in selected_tools
            if tool_name in {
                "echo_get_context_budget",
                "echo_get_agent_routing",
                "echo_get_memory_context",
                "echo_get_context_assembly",
                "echo_get_response_composer",
                "echo_get_intent_reasoning"
            }
        ]
    elif budget_level == "standard":
        selected_tools = [
            tool_name for tool_name in selected_tools
            if tool_name not in {
                "echo_get_daily_brief"
            }
        ]

    return selected_tools


def _run_echo_orchestrator_tool(tool_name, message, context):

    if tool_name == "echo_ask":
        return echo_ask(message, context)

    tool_functions = {
        "echo_get_daily_brief": echo_get_daily_brief,
        "echo_get_state": echo_get_state,
        "echo_get_state_delta": echo_get_state_delta,
        "echo_get_state_history": echo_get_state_history,
        "echo_get_change_detection": echo_get_change_detection,
        "echo_get_knowledge_graph": echo_get_knowledge_graph,
        "echo_get_memory_context": echo_get_memory_context,
        "echo_get_context_budget": echo_get_context_budget,
        "echo_get_agent_routing": echo_get_agent_routing,
        "echo_get_context_assembly": echo_get_context_assembly,
        "echo_get_response_composer": echo_get_response_composer,
        "echo_get_intent_reasoning": echo_get_intent_reasoning,
        "echo_get_top_priority": echo_get_top_priority,
        "echo_get_themes": echo_get_themes,
        "echo_get_theme_impacts": echo_get_theme_impacts,
        "echo_get_conflicts": echo_get_conflicts,
        "echo_get_portfolio_snapshot": echo_get_portfolio_snapshot,
        "echo_get_macro_snapshot": echo_get_macro_snapshot,
        "echo_get_news_snapshot": echo_get_news_snapshot,
        "echo_get_research_snapshot": echo_get_research_snapshot
    }
    tool_function = tool_functions.get(tool_name)

    if tool_function is None:
        return {
            "tool": tool_name,
            "status": "UNKNOWN_TOOL",
            "data": {},
            "summary": "Tool not found.",
            "confidence": "LOW",
            "notes": "No registered deterministic tool matched."
        }

    return tool_function(context)


def _echo_orchestrator_answer(tool_results):

    summaries = []

    for tool_name, result in tool_results.items():
        summary = " ".join(str(result.get("summary") or "").split())

        if summary:
            summaries.append(f"{tool_name}: {summary}")

    if not summaries:
        return "No deterministic tool summaries were available."

    return _concise(" ".join(summaries), limit=1200)


def _echo_orchestrator_confidence(tool_results):

    confidences = {
        str(result.get("confidence") or "MEDIUM").upper()
        for result in tool_results.values()
    }

    if not tool_results or "LOW" in confidences:
        return "LOW"

    if "MEDIUM" in confidences:
        return "MEDIUM"

    return "HIGH"


def echo_orchestrate_user_message(message, context=None):

    normalized_message = " ".join(str(message or "").split())
    query_context = _echo_tool_context(context)

    if not normalized_message:
        return {
            "status": "EMPTY_MESSAGE",
            "mode": "DETERMINISTIC_ORCHESTRATOR_STUB",
            "message": "",
            "selected_tools": [],
            "tool_results": {},
            "answer": "Message cannot be empty.",
            "confidence": "LOW",
            "notes": (
                "Echo LLM orchestrator stub did not run because no message "
                "was provided."
            )
        }

    memory_context = read_memory_context()
    context_budget = build_context_budget(
        normalized_message,
        memory_context,
        sorted(ECHO_TOOL_REGISTRY)
    )
    agent_routing = route_query_to_agents(
        normalized_message,
        context_budget,
        memory_context,
        list(AGENT_ROUTING_TOOL_MAP)
    )
    context_assembly = assemble_echo_context(
        normalized_message,
        memory_context,
        context_budget,
        agent_routing,
        _context_assembly_reports(query_context)
    )
    response_composer = compose_echo_response(
        normalized_message,
        context_budget,
        agent_routing,
        context_assembly,
        memory_context
    )
    intent_reasoning = classify_reasoning_intent(
        normalized_message,
        context_budget,
        agent_routing,
        context_assembly,
        memory_context
    )
    write_context_budget_json(context_budget)
    write_context_budget_text(context_budget)
    write_agent_routing_json(agent_routing)
    write_agent_routing_text(agent_routing)
    write_context_assembly_json(context_assembly)
    write_context_assembly_text(context_assembly)
    write_response_composer_json(response_composer)
    write_response_composer_text(response_composer)
    write_intent_reasoning_json(intent_reasoning)
    write_intent_reasoning_text(intent_reasoning)
    query_context = dict(query_context)
    query_context["context_budget"] = context_budget
    query_context["agent_routing"] = agent_routing
    query_context["context_assembly"] = context_assembly
    query_context["response_composer"] = response_composer
    query_context["intent_reasoning"] = intent_reasoning

    selected_tools = _echo_orchestrator_select_tools(
        normalized_message,
        query_context,
        context_budget,
        agent_routing
    )
    tool_results = {
        tool_name: _run_echo_orchestrator_tool(
            tool_name,
            normalized_message,
            query_context
        )
        for tool_name in selected_tools
    }

    return {
        "status": "ANSWERED",
        "mode": "DETERMINISTIC_ORCHESTRATOR_STUB",
        "message": normalized_message,
        "selected_tools": selected_tools,
        "context_budget": context_budget,
        "agent_routing": agent_routing,
        "context_assembly": context_assembly,
        "response_composer": response_composer,
        "intent_reasoning": intent_reasoning,
        "tool_results": tool_results,
        "answer": response_composer.get("answer") or _echo_orchestrator_answer(
            tool_results
        ),
        "confidence": _echo_orchestrator_confidence(tool_results),
        "notes": (
            "LLM orchestrator stub used deterministic tool selection and "
            "tool-summary fallback synthesis. LLM Enabled: No. No external "
            "API call was made."
        )
    }


def echo_generate_llm_answer(message, context=None):

    normalized_message = " ".join(str(message or "").split())
    query_context = _echo_tool_context(context)
    orchestrator_result = echo_orchestrate_user_message(
        normalized_message,
        query_context
    )
    provider = get_llm_provider()
    provider_payload = _llm_provider_payload(orchestrator_result)
    tool_context = format_tool_context_for_llm(provider_payload)
    provider_result = provider.generate_response(
        [{"role": "user", "content": normalized_message}],
        tools=provider_payload,
        context=query_context
    )
    selected_tools = orchestrator_result.get("selected_tools", [])
    context_budget = orchestrator_result.get("context_budget", {})
    agent_routing = orchestrator_result.get("agent_routing", {})
    context_assembly = orchestrator_result.get("context_assembly", {})
    response_composer = orchestrator_result.get("response_composer", {})
    intent_reasoning = orchestrator_result.get("intent_reasoning", {})
    tool_results = orchestrator_result.get("tool_results", {})
    fallback_answer = _reasoning_fallback_answer(
        orchestrator_result.get("answer", ""),
        intent_reasoning,
        context_assembly
    )
    fallback_validation = validate_llm_response(
        fallback_answer,
        tool_context
    )
    provider_status = provider_result.get("status", "UNKNOWN")
    provider_model = provider_result.get("model", provider.model_name())
    live_call_attempted = bool(provider_result.get("live_call_attempted"))
    tool_context_char_count = provider_result.get(
        "tool_context_char_count",
        len(tool_context)
    )

    if provider_status == "ANSWERED":
        validation = validate_llm_response(
            provider_result.get("answer", ""),
            tool_context
        )
        provider_name = provider_result.get("provider", provider.provider_name)
        llm_metadata = _response_metadata(
            provider_name,
            provider_model,
            live_call_attempted,
            validation["fallback_required"],
            (
                "deterministic"
                if validation["fallback_required"]
                else "llm"
            ),
            provider_status,
            context_budget,
            agent_routing,
            context_assembly,
            intent_reasoning
        )

        if validation["fallback_required"]:
            return {
                "status": "DETERMINISTIC_FALLBACK",
                "mode": "DETERMINISTIC_FALLBACK",
                "provider": provider_name,
                "model": provider_model,
                **llm_metadata,
                "message": normalized_message,
                "answer": fallback_answer,
                "selected_tools": selected_tools,
                "context_budget": context_budget,
                "agent_routing": agent_routing,
                "context_assembly": context_assembly,
                "response_composer": response_composer,
                "intent_reasoning": intent_reasoning,
                "tool_results": tool_results,
                "confidence": orchestrator_result.get(
                    "confidence",
                    "MEDIUM"
                ),
                "validation": validation,
                "tool_context_char_count": tool_context_char_count,
                "live_call_attempted": live_call_attempted,
                "fallback_used": True,
                "response_source": "deterministic",
                "notes": (
                    "Deterministic fallback used because LLM response "
                    "validation failed: "
                    f"{'; '.join(validation['warnings'])}"
                )
            }

        return {
            "status": "ANSWERED",
            "mode": "LLM_PROVIDER",
            "provider": provider_name,
            "model": provider_model,
            **llm_metadata,
            "message": normalized_message,
            "answer": provider_result.get("answer", ""),
            "selected_tools": selected_tools,
            "context_budget": context_budget,
            "agent_routing": agent_routing,
            "context_assembly": context_assembly,
            "response_composer": response_composer,
            "intent_reasoning": intent_reasoning,
            "tool_results": tool_results,
            "confidence": provider_result.get("confidence", "MEDIUM"),
            "validation": validation,
            "tool_context_char_count": tool_context_char_count,
            "live_call_attempted": live_call_attempted,
            "fallback_used": False,
            "response_source": "llm",
            "notes": _redact_secret_text(provider_result.get("notes", ""))
        }

    if provider_status == "NOT_CONFIGURED":
        fallback_reason = "LLM provider is not configured."
    elif provider_status == "STUB":
        fallback_reason = "LLM live mode is disabled."
    elif provider_status == "DEPENDENCY_MISSING":
        fallback_reason = "LLM provider dependency is missing."
    else:
        fallback_reason = f"Provider status was {provider_status}."

    llm_metadata = _response_metadata(
        provider.provider_name,
        provider_model,
        live_call_attempted,
        True,
        "deterministic",
        provider_status,
        context_budget,
        agent_routing,
        context_assembly,
        intent_reasoning
    )

    return {
        "status": "DETERMINISTIC_FALLBACK",
        "mode": "DETERMINISTIC_FALLBACK",
        "provider": provider.provider_name,
        "model": provider_model,
        **llm_metadata,
        "message": normalized_message,
        "answer": fallback_answer,
        "selected_tools": selected_tools,
        "context_budget": context_budget,
        "agent_routing": agent_routing,
        "context_assembly": context_assembly,
        "response_composer": response_composer,
        "intent_reasoning": intent_reasoning,
        "tool_results": tool_results,
        "confidence": orchestrator_result.get("confidence", "MEDIUM"),
        "validation": fallback_validation,
        "tool_context_char_count": tool_context_char_count,
        "live_call_attempted": live_call_attempted,
        "fallback_used": True,
        "response_source": "deterministic",
        "notes": (
            f"Deterministic fallback used. {fallback_reason} "
            f"{_redact_secret_text(provider_result.get('notes', ''))}"
        )
    }


def get_echo_orchestrator_status():

    provider_status = get_llm_provider_status()

    return {
        "status": "ACTIVE",
        "mode": "DETERMINISTIC_STUB",
        "llm_enabled": provider_status["live_calls_enabled"],
        "llm_provider_status": provider_status,
        "active_provider": provider_status["active_provider"],
        "llm_configured": provider_status["configured"],
        "live_calls_enabled": provider_status["live_calls_enabled"],
        "model": provider_status["model"],
        "fallback_mode_available": True,
        "available_tools": sorted(ECHO_TOOL_REGISTRY)
    }


def run_report_agent(registry, agent_name, report_function, fallback):

    agent = get_registry_agent(registry, agent_name)
    start_time = perf_counter()

    try:
        report = report_function()
        agent["last_run_status"] = "SUCCESS"
        agent["health"] = "HEALTHY"
    except Exception as error:
        report = fallback(str(error))
        agent["status"] = "ERROR"
        agent["health"] = "DEGRADED"
        agent["last_run_status"] = "FAILED"
        agent["failure_message"] = " ".join(str(error).split())[:180]
    finally:
        agent["execution_time_seconds"] = perf_counter() - start_time

    return report


def get_registry_report(registry):

    summary = [
        (
            "Active Agents: "
            f"{sum(agent['status'] == 'ACTIVE' for agent in registry)}"
        ),
        (
            "Partial Active Agents: "
            f"{sum(agent['status'] == 'PARTIAL_ACTIVE' for agent in registry)}"
        ),
        (
            "Placeholder Agents: "
            f"{sum(agent['status'] == 'PLACEHOLDER' for agent in registry)}"
        ),
        (
            "Failed Agents: "
            f"{sum(
                agent['status'] == 'ERROR'
                or agent['last_run_status'] == 'FAILED'
                for agent in registry
            )}"
        ),
        (
            "Healthy Agents: "
            f"{sum(agent['health'] == 'HEALTHY' for agent in registry)}"
        ),
        (
            "Report Mode Supported: "
            f"{sum(
                agent['report_mode'] == 'SUPPORTED'
                for agent in registry
            )}"
        ),
        (
            "Report Mode Partial: "
            f"{sum(agent['report_mode'] == 'PARTIAL' for agent in registry)}"
        ),
        (
            "Query Mode Supported: "
            f"{sum(
                agent['query_mode'] == 'SUPPORTED'
                for agent in registry
            )}"
        ),
        (
            "Query Mode Planned: "
            f"{sum(agent['query_mode'] == 'PLANNED' for agent in registry)}"
        ),
        "",
        (
            "Echo operates in report mode and supports deterministic "
            "backend queries for active report agents."
        )
    ]
    details = []

    for agent in registry:
        execution_time = (
            f"{agent['execution_time_seconds']:.2f}s"
            if agent["execution_time_seconds"] is not None
            else "N/A"
        )
        line = (
            f"{agent['agent_name']} | Role {agent['role']} | "
            f"Status {agent['status']} | Health {agent['health']} | "
            f"Report {agent['report_mode']} | Query {agent['query_mode']} | "
            f"Last Run {agent['last_run_status']} | Time {execution_time}"
        )

        if agent["failure_message"]:
            line += f" | Error {agent['failure_message']}"

        if agent["notes"]:
            line += f" | Notes {agent['notes']}"

        details.append(line)

    return {
        "summary": summary,
        "details": details
    }


def get_query_interface_report(registry):

    summary = [
        "Query Interface Status: ACTIVE",
        (
            "Query Mode Supported Agents: "
            f"{sum(
                agent['query_mode'] == 'SUPPORTED'
                for agent in registry
            ) + 1}"
        ),
        (
            "Query Mode Planned Agents: "
            f"{sum(agent['query_mode'] == 'PLANNED' for agent in registry)}"
        ),
        (
            "Query Mode Not Supported Agents: "
            f"{sum(
                agent['query_mode'] == 'NOT_SUPPORTED'
                for agent in registry
            )}"
        ),
        "Unknown Agent Handling: ENABLED",
        "Empty Query Handling: ENABLED",
        "Echo Multi-Agent Response Engine: ACTIVE",
        "Echo Multi-Agent Routing: DETERMINISTIC",
        "LLM Orchestrator Stub: ACTIVE | LLM Enabled: No",
        (
            "LLM Provider Layer: ACTIVE | Provider: "
            f"{get_llm_provider_status()['active_provider']} | "
            "Live Calls: "
            f"{'Enabled' if get_llm_provider_status()['live_calls_enabled'] else 'Disabled'}"
        ),
        "LLM Response Safety Contract: ACTIVE",
        "Deterministic Only: YES",
        "AI Integration: NONE",
        "",
        (
            "Query answers use existing generated reports, signals, themes, "
            "theme impacts, and conflicts."
        ),
        (
            "Echo can route one user question across active report agents "
            "and synthesize a deterministic response."
        )
    ]
    details = [
        (
            "Echo | Query Mode SUPPORTED | Supported Types top priority, "
            "themes, impacts, conflicts, action queue, market watch, "
            "macro backdrop, portfolio risk, multi-agent position risk, "
            "multi-agent macro impact, multi-agent market/news impact, "
            "multi-agent research quality, multi-agent allocation/"
            "concentration review, multi-agent top-priority review | "
            "Routing deterministic | AI/LLM commentary NONE | Example "
            "What are the biggest risks to SMCI?"
        )
    ]

    agents_by_name = {
        agent["agent_name"]: agent
        for agent in registry
    }

    for agent_name in QUERY_INTERFACE_AGENT_ORDER:
        agent = agents_by_name[agent_name]
        supported_types = ", ".join(agent["supported_query_types"]) or "None"
        planned_types = ", ".join(agent["planned_query_types"]) or "None"
        example = (
            agent["example_queries"][0]
            if agent["example_queries"]
            else "None"
        )
        details.append(
            f"{agent['agent_name']} | Query Mode {agent['query_mode']} | "
            f"Supported Types {supported_types} | "
            f"Planned Types {planned_types} | Example {example}"
        )

    return {
        "summary": summary,
        "details": details
    }


def _briefing_title():

    return (
        "=================================\n"
        "         ECHO BRIEFING\n"
        "=================================\n\n"
    )


def build_report_outputs_section(failures=None):

    outputs = [
        "Executive Brief: 04_Reports/echo_executive_brief.txt",
        "Full Echo Brief: 04_Reports/echo_full_brief.txt",
        "News Report: 04_Reports/agents/news_full_report.txt",
        "Macro Report: 04_Reports/agents/macro_full_report.txt",
        "Research Report: 04_Reports/agents/research_full_report.txt",
        "Portfolio Report: 04_Reports/agents/portfolio_full_report.txt",
        "",
        (
            "Full report separation is active. daily_brief.txt remains "
            "backward compatible."
        )
    ]

    if failures:
        outputs.extend([
            "",
            "Report Write Failures: " + "; ".join(failures)
        ])

    return outputs


def get_report_archive_timestamp():

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _default_retention_status():

    return {
        "archive_enabled": REPORT_ARCHIVE_ENABLED,
        "archive_folder": "N/A",
        "keep_count": REPORT_ARCHIVE_KEEP_COUNT,
        "runs_retained": 0,
        "cleanup_deleted": 0,
        "status": "OK",
        "notes": (
            "Archive retention is configured. Archive output is generated "
            "when reports are written."
            if REPORT_ARCHIVE_ENABLED
            else "Report archiving is disabled."
        )
    }


def build_report_retention_summary(retention_status=None):

    retention_status = retention_status or _default_retention_status()

    return [
        (
            "Archive Enabled: "
            f"{'Yes' if retention_status['archive_enabled'] else 'No'}"
        ),
        f"Archive Folder: {retention_status['archive_folder']}",
        f"Archive Keep Count: {retention_status['keep_count']}",
        f"Archive Runs Retained: {retention_status['runs_retained']}",
        f"Archive Cleanup Deleted: {retention_status['cleanup_deleted']}",
        f"Retention Status: {retention_status['status']}",
        f"Notes: {retention_status['notes']}"
    ]


def _is_timestamped_archive_folder(path):

    try:
        datetime.strptime(path.name, "%Y%m%d_%H%M%S")
    except ValueError:
        return False

    return path.is_dir()


def cleanup_old_report_archives(archive_dir, keep_count):

    archive_dir = Path(archive_dir)
    deleted = 0
    failures = []

    try:
        archive_root = archive_dir.resolve()
        archive_root.mkdir(parents=True, exist_ok=True)
        archive_folders = sorted(
            (
                path for path in archive_root.iterdir()
                if _is_timestamped_archive_folder(path)
            ),
            key=lambda path: path.name,
            reverse=True
        )
    except (OSError, ValueError) as error:
        return {
            "deleted": 0,
            "retained": 0,
            "failures": [" ".join(str(error).split())[:180]]
        }

    for folder in archive_folders[max(int(keep_count or 0), 0):]:
        try:
            resolved_folder = folder.resolve()

            if resolved_folder.parent != archive_root:
                raise ValueError(
                    f"Unsafe archive cleanup path: {resolved_folder}"
                )

            shutil.rmtree(resolved_folder)
            deleted += 1
        except (OSError, ValueError) as error:
            failures.append(
                f"{folder}: {' '.join(str(error).split())[:180]}"
            )

    retained = sum(
        _is_timestamped_archive_folder(path)
        for path in archive_root.iterdir()
    )

    return {
        "deleted": deleted,
        "retained": retained,
        "failures": failures
    }


def _assemble_report_bundle(
    sections,
    report_output_failures=None,
    retention_status=None
):

    title = _briefing_title()
    report_outputs = add_section(
        "REPORT OUTPUTS",
        build_report_outputs_section(report_output_failures)
    )
    retention_summary = add_section(
        "REPORT RETENTION SUMMARY",
        build_report_retention_summary(retention_status)
    )
    executive_brief_report = (
        title
        + add_section(
            "ECHO EXECUTIVE BRIEF",
            sections["executive_brief"]
        )
    )
    full_echo_report = executive_brief_report

    for title_key, content_key in (
        ("ECHO EXECUTIVE SUMMARY", "executive_summary"),
        ("CROSS-AGENT THEME SUMMARY", "theme_summary"),
        ("CROSS-AGENT THEME DETAILS", "theme_details"),
        ("THEME IMPACT SUMMARY", "theme_impact_summary"),
        ("THEME IMPACT DETAILS", "theme_impact_details"),
        ("THEME CONFLICT SUMMARY", "theme_conflict_summary"),
        ("THEME CONFLICT DETAILS", "theme_conflict_details"),
        ("CROSS-AGENT PRIORITY SUMMARY", "priority_summary"),
        ("CROSS-AGENT PRIORITY DETAILS", "priority_details"),
        ("AGENT SIGNAL BUS SUMMARY", "signal_bus_summary"),
        ("AGENT SIGNAL BUS DETAILS", "signal_bus_details"),
        ("SIGNAL WEIGHTING SUMMARY", "signal_weighting_summary"),
        ("SIGNAL WEIGHTING DETAILS", "signal_weighting_details"),
        ("SIGNAL MAGNITUDE SUMMARY", "signal_magnitude_summary"),
        ("SIGNAL MAGNITUDE DETAILS", "signal_magnitude_details"),
        ("AGENT REGISTRY SUMMARY", "registry_summary"),
        ("AGENT REGISTRY DETAILS", "registry_details"),
        ("AGENT QUERY INTERFACE SUMMARY", "query_summary"),
        ("AGENT QUERY INTERFACE DETAILS", "query_details")
    ):
        full_echo_report += add_section(title_key, sections[content_key])

    daily_brief = (
        executive_brief_report
        + report_outputs
        + retention_summary
    )
    daily_brief += full_echo_report[len(executive_brief_report):]
    daily_brief += add_section(
        "NEWS AGENT EXECUTIVE BRIEF",
        sections["news"]["executive_brief"]
    )
    daily_brief += add_section(
        "NEWS AGENT FULL REPORT",
        sections["news"]["full_report"]
    )
    daily_brief += add_section(
        "MACRO AGENT EXECUTIVE BRIEF",
        sections["macro"]["executive_brief"]
    )
    daily_brief += add_section(
        "MACRO AGENT FULL REPORT",
        sections["macro"]["full_report"]
    )
    daily_brief += add_section(
        "RESEARCH AGENT EXECUTIVE BRIEF",
        sections["research"]["executive_brief"]
    )
    daily_brief += add_section(
        "RESEARCH AGENT FULL REPORT",
        sections["research"]["full_report"]
    )
    daily_brief += add_section(
        "PORTFOLIO MANAGER REPORT",
        sections["portfolio"]
    )

    return {
        "daily_brief": daily_brief,
        "echo_executive_brief": executive_brief_report,
        "echo_full_brief": full_echo_report,
        "news_full_report": (
            add_section(
                "NEWS AGENT EXECUTIVE BRIEF",
                sections["news"]["executive_brief"]
            )
            + add_section(
                "NEWS AGENT FULL REPORT",
                sections["news"]["full_report"]
            )
        ),
        "macro_full_report": (
            add_section(
                "MACRO AGENT EXECUTIVE BRIEF",
                sections["macro"]["executive_brief"]
            )
            + add_section(
                "MACRO AGENT FULL REPORT",
                sections["macro"]["full_report"]
            )
        ),
        "research_full_report": (
            add_section(
                "RESEARCH AGENT EXECUTIVE BRIEF",
                sections["research"]["executive_brief"]
            )
            + add_section(
                "RESEARCH AGENT FULL REPORT",
                sections["research"]["full_report"]
            )
        ),
        "portfolio_full_report": add_section(
            "PORTFOLIO MANAGER REPORT",
            sections["portfolio"]
        ),
        "sections": sections
    }


def build_morning_brief(
    return_bundle=False,
    report_output_failures=None,
    retention_status=None
):

    registry = create_agent_registry()
    news = run_report_agent(
        registry,
        "News Agent",
        get_news_report,
        lambda error: {
            "executive_brief": [f"News Agent unavailable: {error}"],
            "full_report": ["No news articles available."]
        }
    )
    macro = run_report_agent(
        registry,
        "Macro Agent",
        get_macro_report,
        lambda error: {
            "executive_brief": [f"Macro Agent unavailable: {error}"],
            "full_report": ["No macro data available."]
        }
    )
    research = run_report_agent(
        registry,
        "Research Agent",
        get_research_agent_report,
        lambda error: {
            "executive_brief": [
                f"Research Agent Status: OFFLINE",
                f"Research Agent unavailable: {error}"
            ],
            "full_report": ["No research data available."]
        }
    )
    portfolio = run_report_agent(
        registry,
        "Portfolio Manager",
        get_portfolio_report,
        lambda error: [f"Portfolio Manager unavailable: {error}"]
    )
    policy = get_policy()
    registry_report = get_registry_report(registry)
    query_interface_report = get_query_interface_report(registry)
    signals = build_agent_signals(
        portfolio,
        research,
        macro,
        news,
        registry
    )
    signal_bus_report = build_agent_signal_bus_report(signals)
    signal_weighting_report = build_signal_weighting_report(signals)
    signal_magnitude_report = build_signal_magnitude_report(signals)
    priority_report = build_cross_agent_priority_report(signals)
    theme_report = build_cross_agent_theme_report(signals)
    theme_impact_report = build_theme_impact_report(
        theme_report["themes"],
        signals,
        portfolio
    )
    theme_conflict_report = build_theme_conflict_report(
        theme_report["themes"],
        theme_impact_report["impacts"],
        signals,
        portfolio,
        macro,
        news
    )
    executive_summary = build_signal_driven_executive_summary(
        registry,
        signals,
        theme_report,
        theme_impact_report,
        theme_conflict_report
    )
    executive_brief = build_echo_executive_brief(
        registry,
        signals,
        theme_report,
        theme_impact_report,
        theme_conflict_report
    )

    sections = {
        "executive_brief": executive_brief,
        "executive_summary": executive_summary,
        "theme_summary": theme_report["summary"],
        "theme_details": theme_report["details"],
        "theme_impact_summary": theme_impact_report["summary"],
        "theme_impact_details": theme_impact_report["details"],
        "theme_conflict_summary": theme_conflict_report["summary"],
        "theme_conflict_details": theme_conflict_report["details"],
        "priority_summary": priority_report["summary"],
        "priority_details": priority_report["details"],
        "signal_bus_summary": signal_bus_report["summary"],
        "signal_bus_details": signal_bus_report["details"],
        "signal_weighting_summary": signal_weighting_report["summary"],
        "signal_weighting_details": signal_weighting_report["details"],
        "signal_magnitude_summary": signal_magnitude_report["summary"],
        "signal_magnitude_details": signal_magnitude_report["details"],
        "registry_summary": registry_report["summary"],
        "registry_details": registry_report["details"],
        "query_summary": query_interface_report["summary"],
        "query_details": query_interface_report["details"],
        "news": news,
        "macro": macro,
        "research": research,
        "portfolio": portfolio
    }
    bundle = _assemble_report_bundle(
        sections,
        report_output_failures,
        retention_status
    )

    return bundle if return_bundle else bundle["daily_brief"]


def write_report_file(path, content):

    path = Path(path)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
    except (OSError, ValueError) as error:
        return {
            "success": False,
            "path": str(path),
            "error": " ".join(str(error).split())[:180]
        }

    return {
        "success": True,
        "path": str(path),
        "error": ""
    }


def _report_file_map(root_dir):

    root_dir = Path(root_dir)

    return {
        "daily_brief": root_dir / "daily_brief.txt",
        "echo_executive_brief": root_dir / "echo_executive_brief.txt",
        "echo_full_brief": root_dir / "echo_full_brief.txt",
        "news_full_report": root_dir / "agents" / "news_full_report.txt",
        "macro_full_report": root_dir / "agents" / "macro_full_report.txt",
        "research_full_report": (
            root_dir / "agents" / "research_full_report.txt"
        ),
        "portfolio_full_report": (
            root_dir / "agents" / "portfolio_full_report.txt"
        )
    }


def write_latest_reports(bundle):

    report_paths = _report_file_map(REPORTS_DIR)

    return {
        name: write_report_file(path, bundle[name])
        for name, path in report_paths.items()
    }


def write_separated_reports(bundle):

    return {
        name: result
        for name, result in write_latest_reports(bundle).items()
        if name != "daily_brief"
    }


def write_archive_reports(bundle, timestamp):

    archive_folder = REPORT_ARCHIVE_DIR / timestamp
    report_paths = _report_file_map(archive_folder)

    return {
        name: write_report_file(path, bundle[name])
        for name, path in report_paths.items()
    }


def _write_failures(results):

    return [
        f"{result['path']}: {result['error']}"
        for result in results.values()
        if not result["success"]
    ]


def apply_report_retention(report_bundle, timestamp=None):

    timestamp = timestamp or get_report_archive_timestamp()
    retention_status = _default_retention_status()
    retention_notes = []
    archive_results = {}

    if REPORT_ARCHIVE_ENABLED:
        archive_folder = REPORT_ARCHIVE_DIR / timestamp
        retention_status["archive_folder"] = (
            f"04_Reports/archive/{timestamp}"
        )
        archive_results = write_archive_reports(report_bundle, timestamp)
        archive_failures = _write_failures(archive_results)

        if archive_failures:
            retention_notes.extend(archive_failures)

        cleanup = cleanup_old_report_archives(
            REPORT_ARCHIVE_DIR,
            REPORT_ARCHIVE_KEEP_COUNT
        )
        retention_status["cleanup_deleted"] = cleanup["deleted"]
        retention_status["runs_retained"] = cleanup["retained"]
        retention_notes.extend(cleanup["failures"])
    else:
        retention_status["notes"] = "Report archiving is disabled."

    if retention_notes:
        retention_status["status"] = "DEGRADED"
        retention_status["notes"] = "; ".join(retention_notes)
    elif REPORT_ARCHIVE_ENABLED:
        retention_status["notes"] = (
            "Archive write and cleanup completed. Archive directory may "
            "need a future git ignore policy."
        )

    return {
        "status": retention_status,
        "archive_results": archive_results
    }


def save_report(brief):

    return write_report_file(REPORTS_DIR / "daily_brief.txt", brief)



if __name__ == "__main__":
    report_bundle = build_morning_brief(return_bundle=True)
    retention = apply_report_retention(report_bundle)
    report_bundle = _assemble_report_bundle(
        report_bundle["sections"],
        retention_status=retention["status"]
    )
    latest_results = write_latest_reports(report_bundle)
    latest_failures = _write_failures(latest_results)

    if latest_failures:
        report_bundle = _assemble_report_bundle(
            report_bundle["sections"],
            latest_failures,
            retention["status"]
        )
        write_latest_reports(report_bundle)

    if REPORT_ARCHIVE_ENABLED:
        timestamp = Path(
            retention["status"]["archive_folder"]
        ).name
        write_archive_reports(report_bundle, timestamp)

    previous_state = load_previous_state()
    state = build_echo_state(report_bundle)
    state_delta = build_echo_state_delta(previous_state, state)

    if previous_state is not None:
        snapshot_result = save_state_snapshot(previous_state)

        if not snapshot_result["success"]:
            print(f"Echo state snapshot failed: {snapshot_result['error']}")

    state_result = write_echo_state(state)
    delta_json_result = write_state_delta_json(state_delta)
    delta_text_result = write_state_delta_text(state_delta)
    state_history = build_echo_state_history(state, STATE_ARCHIVE_DIR)
    history_json_result = write_state_history_json(state_history)
    history_text_result = write_state_history_text(state_history)
    change_detection = build_echo_change_detection(
        state,
        state_delta,
        state_history
    )
    change_detection_json_result = write_change_detection_json(
        change_detection
    )
    change_detection_text_result = write_change_detection_text(
        change_detection
    )
    knowledge_graph = build_echo_knowledge_graph(
        state,
        state_delta,
        state_history,
        change_detection
    )
    knowledge_graph_json_result = write_knowledge_graph_json(knowledge_graph)
    knowledge_graph_text_result = write_knowledge_graph_text(knowledge_graph)
    memory_context = build_echo_memory_context(
        state,
        state_delta,
        state_history,
        change_detection,
        knowledge_graph
    )
    memory_context_json_result = write_memory_context_json(memory_context)
    memory_context_text_result = write_memory_context_text(memory_context)
    daily_orchestration_query = "Echo daily run overall executive summary"
    context_budget = build_context_budget(
        daily_orchestration_query,
        memory_context,
        sorted(ECHO_TOOL_REGISTRY)
    )
    context_budget_json_result = write_context_budget_json(context_budget)
    context_budget_text_result = write_context_budget_text(context_budget)
    agent_routing = route_query_to_agents(
        daily_orchestration_query,
        context_budget,
        memory_context,
        list(AGENT_ROUTING_TOOL_MAP)
    )
    agent_routing_json_result = write_agent_routing_json(agent_routing)
    agent_routing_text_result = write_agent_routing_text(agent_routing)
    context_assembly = assemble_echo_context(
        daily_orchestration_query,
        memory_context,
        context_budget,
        agent_routing,
        _context_assembly_reports(report_bundle)
    )
    context_assembly_json_result = write_context_assembly_json(
        context_assembly
    )
    context_assembly_text_result = write_context_assembly_text(
        context_assembly
    )
    response_composer = compose_echo_response(
        daily_orchestration_query,
        context_budget,
        agent_routing,
        context_assembly,
        memory_context
    )
    response_composer_json_result = write_response_composer_json(
        response_composer
    )
    response_composer_text_result = write_response_composer_text(
        response_composer
    )
    intent_reasoning = classify_reasoning_intent(
        daily_orchestration_query,
        context_budget,
        agent_routing,
        context_assembly,
        memory_context
    )
    intent_reasoning_json_result = write_intent_reasoning_json(
        intent_reasoning
    )
    intent_reasoning_text_result = write_intent_reasoning_text(
        intent_reasoning
    )

    if not state_result["success"]:
        print(f"Echo state write failed: {state_result['error']}")

    if not delta_json_result["success"]:
        print(f"Echo state delta JSON write failed: {delta_json_result['error']}")

    if not delta_text_result["success"]:
        print(f"Echo state delta text write failed: {delta_text_result['error']}")

    if not history_json_result["success"]:
        print(
            "Echo state history JSON write failed: "
            f"{history_json_result['error']}"
        )

    if not history_text_result["success"]:
        print(
            "Echo state history text write failed: "
            f"{history_text_result['error']}"
        )

    if not change_detection_json_result["success"]:
        print(
            "Echo change detection JSON write failed: "
            f"{change_detection_json_result['error']}"
        )

    if not change_detection_text_result["success"]:
        print(
            "Echo change detection text write failed: "
            f"{change_detection_text_result['error']}"
        )

    if not knowledge_graph_json_result["success"]:
        print(
            "Echo knowledge graph JSON write failed: "
            f"{knowledge_graph_json_result['error']}"
        )

    if not knowledge_graph_text_result["success"]:
        print(
            "Echo knowledge graph text write failed: "
            f"{knowledge_graph_text_result['error']}"
        )

    if not memory_context_json_result["success"]:
        print(
            "Echo memory context JSON write failed: "
            f"{memory_context_json_result['error']}"
        )

    if not memory_context_text_result["success"]:
        print(
            "Echo memory context text write failed: "
            f"{memory_context_text_result['error']}"
        )

    if not context_budget_json_result["success"]:
        print(
            "Echo context budget JSON write failed: "
            f"{context_budget_json_result['error']}"
        )

    if not context_budget_text_result["success"]:
        print(
            "Echo context budget text write failed: "
            f"{context_budget_text_result['error']}"
        )

    if not agent_routing_json_result["success"]:
        print(
            "Echo agent routing JSON write failed: "
            f"{agent_routing_json_result['error']}"
        )

    if not agent_routing_text_result["success"]:
        print(
            "Echo agent routing text write failed: "
            f"{agent_routing_text_result['error']}"
        )

    if not context_assembly_json_result["success"]:
        print(
            "Echo context assembly JSON write failed: "
            f"{context_assembly_json_result['error']}"
        )

    if not context_assembly_text_result["success"]:
        print(
            "Echo context assembly text write failed: "
            f"{context_assembly_text_result['error']}"
        )

    if not response_composer_json_result["success"]:
        print(
            "Echo response composer JSON write failed: "
            f"{response_composer_json_result['error']}"
        )

    if not response_composer_text_result["success"]:
        print(
            "Echo response composer text write failed: "
            f"{response_composer_text_result['error']}"
        )

    if not intent_reasoning_json_result["success"]:
        print(
            "Echo intent reasoning JSON write failed: "
            f"{intent_reasoning_json_result['error']}"
        )

    if not intent_reasoning_text_result["success"]:
        print(
            "Echo intent reasoning text write failed: "
            f"{intent_reasoning_text_result['error']}"
        )

    print(report_bundle["daily_brief"])
