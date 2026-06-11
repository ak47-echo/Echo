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


def create_agent_registry():

    return [dict(agent) for agent in AGENT_REGISTRY]


def get_registry_agent(registry, agent_name):

    return next(
        agent for agent in registry
        if agent["agent_name"] == agent_name
    )


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

    brief = ""

    brief += "=================================\n"
    brief += "         ECHO BRIEFING\n"
    brief += "=================================\n\n"

    brief += add_section(
        "AGENT REGISTRY SUMMARY",
        registry_report["summary"]
    )
    brief += add_section(
        "AGENT REGISTRY DETAILS",
        registry_report["details"]
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



briefing = build_morning_brief()
print(briefing)
save_report(briefing)
