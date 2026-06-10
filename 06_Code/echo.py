from agents.news_agent import get_news
from agents.macro_agent import get_macro_report
from agents.portfolio_manager import get_portfolio_report
from agents.policy_agent import get_policy


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


def build_morning_brief():

    news = get_news()
    macro = get_macro_report()
    portfolio = get_portfolio_report()
    policy = get_policy()

    brief = ""

    brief += "=================================\n"
    brief += "         ECHO BRIEFING\n"
    brief += "=================================\n\n"

    brief += add_section("NEWS AGENT REPORT", news)
    brief += add_section("MACRO AGENT REPORT", macro)
    brief += add_section("PORTFOLIO MANAGER REPORT", portfolio)

    return brief


def save_report(brief):

    with open("../04_Reports/daily_brief.txt", "w") as file:
        file.write(brief)



briefing = build_morning_brief()
print(briefing)
save_report(briefing)