from agents.news_agent import get_news_report
from agents.macro_agent import get_macro_report
from agents.portfolio_manager import get_portfolio_report
from agents.research_agent import get_research_agent_report
from agents.policy_agent import get_policy
from datetime import datetime
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
        "query_mode": "PLANNED",
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
        "query_mode": "PLANNED",
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
        "query_mode": "PLANNED",
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
        "query_mode": "PLANNED",
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
        "supported_query_types": (),
        "planned_query_types": (
            "portfolio impact",
            "position review",
            "allocation question",
            "rebalancing question",
            "candidate comparison"
        ),
        "example_queries": (
            "What happens if I sell SMCI?",
            "How does buying AVUV affect concentration?",
            "Is UNH too large?"
        )
    },
    "News Agent": {
        "supported_query_types": (),
        "planned_query_types": (
            "ticker news lookup",
            "portfolio news relevance",
            "world event lookup",
            "market headline review"
        ),
        "example_queries": (
            "What happened with UNH today?",
            "Any news affecting semiconductors?",
            "What world events matter for markets?"
        )
    },
    "Macro Agent": {
        "supported_query_types": (),
        "planned_query_types": (
            "macro regime question",
            "inflation question",
            "rates question",
            "labor market question",
            "yield curve question"
        ),
        "example_queries": (
            "What is the current macro regime?",
            "Are rates restrictive?",
            "Is inflation rising or falling?"
        )
    },
    "Research Agent": {
        "supported_query_types": (),
        "planned_query_types": (
            "thesis review",
            "evidence check",
            "watchlist analysis",
            "conviction review"
        ),
        "example_queries": (
            "What research is missing for ECO?",
            "What is the thesis for SMCI?",
            "Which holdings have weak conviction?"
        )
    }
}

FUTURE_AGENT_QUERY_CAPABILITY = {
    "supported_query_types": (),
    "planned_query_types": ("basic future capability description",),
    "example_queries": ("What capabilities are planned for this agent?",)
}

AGENT_NAME_ALIASES = {
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
            "Portfolio Risk",
            {"worst_scenario": worst_scenario}
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
        _report_lines(portfolio),
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

    lines = _report_lines(portfolio)
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
        )
    ]
    details = []

    for number, priority in enumerate(priorities[:10], start=1):
        details.extend([
            f"{number}. {priority['title']}",
            f"   Source: {priority['source_agent']}",
            f"   Severity: {priority['severity']}",
            f"   Category: {priority['category']}",
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

    lines = _report_lines(portfolio)
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


def _select_portfolio_risk_signal(signals):

    eligible_signals = []
    holding_research_types = {
        "MISSING_THESIS",
        "LOW_CONVICTION",
        "UNCOVERED_HOLDING"
    }

    for signal in rank_weighted_signals(signals):
        if signal.get("category") == "Portfolio Risk":
            eligible_signals.append(signal)
        elif (
            signal.get("category") == "Research Gap"
            and signal.get("signal_type") in holding_research_types
        ):
            eligible_signals.append(signal)

    return eligible_signals[0] if eligible_signals else None


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
    top_priority = weighted_signals[0] if weighted_signals else None
    dominant_theme = _dominant_theme(theme_report)
    dominant_impact = _dominant_theme_impact(theme_impact_report)
    key_conflict = _key_theme_conflict(theme_conflict_report)
    macro_environment = _select_macro_environment_signal(weighted_signals)
    portfolio_risk = _select_portfolio_risk_signal(weighted_signals)
    portfolio_opportunity = select_signal_by_category(
        weighted_signals,
        ("Portfolio Opportunity",)
    )
    market_development = _select_market_event_signal(weighted_signals)
    actions = build_signal_driven_action_queue(weighted_signals)
    notes = _build_signal_executive_notes(weighted_signals)
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

    weighted_signals = rank_weighted_signals(signals)
    top_priority = weighted_signals[0] if weighted_signals else None

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
    system_health = determine_signal_driven_system_health(
        registry,
        weighted_signals
    )
    top_priority = weighted_signals[0] if weighted_signals else None
    dominant_theme = _dominant_theme(theme_report)
    dominant_impact = _dominant_theme_impact(theme_impact_report)
    key_conflict = _key_theme_conflict(theme_conflict_report)
    portfolio_risk = _select_portfolio_risk_signal(weighted_signals)
    macro_backdrop = _select_macro_environment_signal(weighted_signals)
    market_watch = _select_market_event_signal(weighted_signals)
    actions = compress_action_queue(
        build_signal_driven_action_queue(weighted_signals)
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
            "Full agent reports remain below."
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


def answer_agent_query(agent_name, query, context=None):

    normalized_query = " ".join(str(query or "").split())
    agent = get_agent_by_name(agent_name)

    if agent is None:
        return {
            "agent_name": normalize_agent_name(agent_name),
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
        status = "QUERY_MODE_PLANNED"
        answer = (
            "Query mode is planned for this agent but not yet implemented."
        )
    elif agent["query_mode"] == "NOT_SUPPORTED":
        status = "QUERY_MODE_NOT_SUPPORTED"
        answer = "Query mode is not supported for this agent."
    else:
        status = "ERROR"
        answer = "Query execution is not active in this phase."

    return {
        "agent_name": agent["agent_name"],
        "query": normalized_query,
        "status": status,
        "answer": answer,
        "confidence": "LOW",
        "requires_full_report": False,
        "notes": (
            "Phase 69 provides the deterministic query contract only; "
            "no agent reasoning was executed."
        )
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
            "Echo currently operates in report mode. "
            "Conversational query mode is planned."
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
        "Query Interface Status: PLANNED",
        (
            "Query Mode Supported Agents: "
            f"{sum(
                agent['query_mode'] == 'SUPPORTED'
                for agent in registry
            )}"
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
        "",
        "Echo conversational query mode is planned but not active yet."
    ]
    details = []

    agents_by_name = {
        agent["agent_name"]: agent
        for agent in registry
    }

    for agent_name in QUERY_INTERFACE_AGENT_ORDER:
        agent = agents_by_name[agent_name]
        planned_types = ", ".join(agent["planned_query_types"]) or "None"
        example = (
            agent["example_queries"][0]
            if agent["example_queries"]
            else "None"
        )
        details.append(
            f"{agent['agent_name']} | Query Mode {agent['query_mode']} | "
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

    print(report_bundle["daily_brief"])
