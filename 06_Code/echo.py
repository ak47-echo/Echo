from agents.news_agent import get_news_report
from agents.macro_agent import get_macro_report
from agents.portfolio_manager import get_portfolio_report
from agents.policy_agent import get_policy
from time import perf_counter


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
        "status": "PARTIAL_ACTIVE",
        "health": "HEALTHY",
        "report_mode": "PARTIAL",
        "query_mode": "PLANNED",
        "last_run_status": "NOT_RUN",
        "execution_time_seconds": None,
        "output_section_name": "Portfolio Manager analytical support",
        "failure_message": "",
        "notes": "Analytical support layer used by Portfolio Manager"
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
    "Portfolio Manager"
)


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


def build_echo_executive_summary(registry, news, macro, portfolio):

    macro_environment = determine_top_macro_environment(macro)
    portfolio_risk = determine_top_portfolio_risk(portfolio)
    portfolio_opportunity = determine_top_portfolio_opportunity(portfolio)
    market_development = determine_top_market_development(news)
    actions = build_priority_action_queue(portfolio, macro, news)
    high_relevance = _field_value(
        _report_lines(news),
        "High Relevance Stories"
    )
    news_note = (
        f"News flow includes {high_relevance} high-relevance stories"
        if high_relevance
        else "News relevance is unavailable"
    )
    notes = _concise(
        f"Macro environment: {macro_environment.rstrip('.')}; "
        f"portfolio risk: {portfolio_risk.rstrip('.')}.",
        limit=260
    )
    notes += f" {news_note}."
    summary = [
        f"System Health: {determine_system_health(registry)}",
        "",
        f"Top Macro Environment: {macro_environment}",
        "",
        f"Top Portfolio Risk: {portfolio_risk}",
        "",
        f"Top Portfolio Opportunity: {portfolio_opportunity}",
        "",
        f"Top Market Development: {market_development}",
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
            "agent outputs and does not constitute investment advice."
        )
    ])

    return summary


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


def build_morning_brief():

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
    portfolio = run_report_agent(
        registry,
        "Portfolio Manager",
        get_portfolio_report,
        lambda error: [f"Portfolio Manager unavailable: {error}"]
    )
    policy = get_policy()
    registry_report = get_registry_report(registry)
    query_interface_report = get_query_interface_report(registry)
    executive_summary = build_echo_executive_summary(
        registry,
        news,
        macro,
        portfolio
    )

    brief = ""

    brief += "=================================\n"
    brief += "         ECHO BRIEFING\n"
    brief += "=================================\n\n"

    brief += add_section(
        "ECHO EXECUTIVE SUMMARY",
        executive_summary
    )
    brief += add_section(
        "AGENT REGISTRY SUMMARY",
        registry_report["summary"]
    )
    brief += add_section(
        "AGENT REGISTRY DETAILS",
        registry_report["details"]
    )
    brief += add_section(
        "AGENT QUERY INTERFACE SUMMARY",
        query_interface_report["summary"]
    )
    brief += add_section(
        "AGENT QUERY INTERFACE DETAILS",
        query_interface_report["details"]
    )
    brief += add_section(
        "NEWS AGENT EXECUTIVE BRIEF",
        news["executive_brief"]
    )
    brief += add_section("NEWS AGENT FULL REPORT", news["full_report"])
    brief += add_section(
        "MACRO AGENT EXECUTIVE BRIEF",
        macro["executive_brief"]
    )
    brief += add_section("MACRO AGENT FULL REPORT", macro["full_report"])
    brief += add_section("PORTFOLIO MANAGER REPORT", portfolio)

    return brief


def save_report(brief):

    with open("../04_Reports/daily_brief.txt", "w") as file:
        file.write(brief)



if __name__ == "__main__":
    briefing = build_morning_brief()
    print(briefing)
    save_report(briefing)
