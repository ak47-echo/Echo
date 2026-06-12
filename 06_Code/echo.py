from agents.news_agent import get_news_report
from agents.macro_agent import get_macro_report
from agents.portfolio_manager import get_portfolio_report
from agents.research_agent import get_research_agent_report
from agents.policy_agent import get_policy
from datetime import datetime
from pathlib import Path
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
    metadata=None
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

    return {
        "source_agent": source_agent,
        "signal_type": signal_type,
        "severity": severity,
        "title": _concise(title),
        "description": _concise(description or title, limit=240),
        "confidence": confidence,
        "category": category or "System Infrastructure",
        "score": score_priority(severity),
        "metadata": dict(metadata) if isinstance(metadata, dict) else {}
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
    regime_key = regime.casefold().replace("_", " ").replace("-", " ")

    if regime:
        high_risk_regime = any(
            risk in regime_key
            for risk in ("recession", "stagflation", "inflation shock")
        )
        _append_signal(
            signals,
            "Macro Agent",
            "MACRO_REGIME",
            "HIGH" if high_risk_regime else "INFO",
            f"Macro regime: {regime}",
            (
                "Macro Agent identified a high-risk macro regime."
                if high_risk_regime
                else "Macro Agent reported the current macro regime."
            ),
            "MEDIUM",
            "Macro Risk" if high_risk_regime else "Macro Environment",
            {"regime": regime}
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
    high_relevance = _field_value(lines, "High Relevance Stories")

    try:
        high_relevance_count = int(high_relevance)
    except ValueError:
        high_relevance_count = 0

    if high_relevance_count > 0:
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
            signal.get("metadata")
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

    return rank_signals(
        build_portfolio_signals(portfolio)
        + build_research_signals(research)
        + build_macro_signals(macro)
        + build_news_signals(news)
        + build_registry_signals(registry)
    )


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
        weighted_signal = dict(signal)
        weighted_signal["weighted_score"] = get_signal_weight(signal)
        weighted_signals.append(weighted_signal)

    return sorted(
        weighted_signals,
        key=lambda signal: (
            -signal["weighted_score"],
            PRIORITY_AGENT_RANKS.get(signal["source_agent"], 99),
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


def build_priority_candidates(signals):

    candidates = []

    for signal in rank_signals(signals):
        if signal["severity"] == "INFO":
            continue

        candidates.append({
            "source_agent": signal["source_agent"],
            "category": signal["category"],
            "title": signal["title"],
            "description": signal["description"],
            "severity": signal["severity"],
            "score": signal["score"],
            "signal_type": signal["signal_type"]
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
            -candidate.get("score", 0),
            PRIORITY_AGENT_RANKS.get(candidate.get("source_agent"), 99)
        )
        current_key = (
            -current.get("score", 0),
            PRIORITY_AGENT_RANKS.get(current.get("source_agent"), 99)
        )

        if candidate_key < current_key:
            unique_priorities[normalized_title] = candidate

    return sorted(
        unique_priorities.values(),
        key=lambda priority: (
            -priority.get("score", 0),
            PRIORITY_AGENT_RANKS.get(
                priority.get("source_agent"),
                99
            ),
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
        if risk["weighted_score"] - environment["weighted_score"] <= 10:
            return environment

        return risk

    return environment or risk


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


def build_signal_driven_executive_summary(registry, signals):

    weighted_signals = rank_weighted_signals(signals)
    top_priority = weighted_signals[0] if weighted_signals else None
    macro_environment = _select_macro_environment_signal(weighted_signals)
    portfolio_risk = _select_portfolio_risk_signal(weighted_signals)
    portfolio_opportunity = select_signal_by_category(
        weighted_signals,
        ("Portfolio Opportunity",)
    )
    market_development = select_signal_by_category(
        weighted_signals,
        ("Market Event",)
    )
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


def build_echo_executive_brief(registry, signals):

    weighted_signals = rank_weighted_signals(signals)
    system_health = determine_signal_driven_system_health(
        registry,
        weighted_signals
    )
    top_priority = weighted_signals[0] if weighted_signals else None
    portfolio_risk = _select_portfolio_risk_signal(weighted_signals)
    macro_backdrop = _select_macro_environment_signal(weighted_signals)
    market_watch = select_signal_by_category(
        weighted_signals,
        ("Market Event",)
    )
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
        ("CROSS-AGENT PRIORITY SUMMARY", "priority_summary"),
        ("CROSS-AGENT PRIORITY DETAILS", "priority_details"),
        ("AGENT SIGNAL BUS SUMMARY", "signal_bus_summary"),
        ("AGENT SIGNAL BUS DETAILS", "signal_bus_details"),
        ("SIGNAL WEIGHTING SUMMARY", "signal_weighting_summary"),
        ("SIGNAL WEIGHTING DETAILS", "signal_weighting_details"),
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
    priority_report = build_cross_agent_priority_report(signals)
    executive_summary = build_signal_driven_executive_summary(
        registry,
        signals
    )
    executive_brief = build_echo_executive_brief(
        registry,
        signals
    )

    sections = {
        "executive_brief": executive_brief,
        "executive_summary": executive_summary,
        "priority_summary": priority_report["summary"],
        "priority_details": priority_report["details"],
        "signal_bus_summary": signal_bus_report["summary"],
        "signal_bus_details": signal_bus_report["details"],
        "signal_weighting_summary": signal_weighting_report["summary"],
        "signal_weighting_details": signal_weighting_report["details"],
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
