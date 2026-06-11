import csv
import yfinance as yf
from agents.policy_agent import get_policy
from agents.research_agent import (
    are_asset_classes_compatible,
    get_buy_list,
    get_concentration_risk,
    get_correlation_proxy,
    get_decision_guardrails,
    get_default_regime,
    get_factor_exposure,
    get_historical_market_data_report,
    get_historical_return_report,
    get_holding_comparable_score,
    get_investment_committee_summary,
    get_macro_regime_report,
    get_monte_carlo_report,
    get_portfolio_exposure,
    get_regime_analysis,
    get_ranked_watchlist,
    get_research_coverage,
    get_research_health_checks,
    get_replacement_plan,
    get_security_classification,
    get_security_info,
    get_sell_candidates,
    get_statistical_correlation_report,
    get_stress_test_report,
    get_tax_optimization_report,
    get_thesis,
    get_uncovered_holdings,
    get_uncovered_watchlist,
    get_volatility_report,
    get_watchlist
)


DEPLOYMENT_AMOUNTS = (100, 500, 1000)

PORTFOLIO_REPORT_SECTION_ORDER = (
    "INVESTMENT COMMITTEE SUMMARY",
    "DECISION GUARDRAILS",
    "EXPOSURE SUMMARY",
    "EXPOSURE DETAILS",
    "CONCENTRATION RISK SUMMARY",
    "CONCENTRATION RISK DETAILS",
    "FACTOR EXPOSURE SUMMARY",
    "FACTOR EXPOSURE DETAILS",
    "REGIME ALIGNMENT SUMMARY",
    "REGIME ALIGNMENT DETAILS",
    "CORRELATION PROXY SUMMARY",
    "CORRELATION PROXY DETAILS",
    "STRESS TEST SUMMARY",
    "STRESS TEST DETAILS",
    "MACRO REGIME SUMMARY",
    "MACRO REGIME DETAILS",
    "TAX OPTIMIZATION SUMMARY",
    "TAX OPTIMIZATION DETAILS",
    "HISTORICAL RETURN SUMMARY",
    "HISTORICAL RETURN DETAILS",
    "STATISTICAL CORRELATION SUMMARY",
    "STATISTICAL CORRELATION DETAILS",
    "VOLATILITY SUMMARY",
    "VOLATILITY DETAILS",
    "MONTE CARLO SUMMARY",
    "MONTE CARLO DETAILS",
    "HISTORICAL MARKET DATA SUMMARY",
    "HISTORICAL MARKET DATA DETAILS",
    "BUY LIST",
    "CAPITAL DEPLOYMENT",
    "SELL CANDIDATES",
    "REPLACEMENT PLAN",
    "RESEARCH HEALTH SUMMARY",
    "RESEARCH HEALTH",
    "RESEARCH COVERAGE",
    "RESEARCH GAPS",
    "POSITIONS",
    "TICKER ALLOCATION",
    "REBALANCE ALERTS",
    "TAX IMPACT NOTES",
    "RECOMMENDATIONS",
    "WATCHLIST",
    "CANDIDATE RANKINGS",
    "CANDIDATE VS HOLDINGS",
    "SECURITY CLASSIFICATION",
    "ACCOUNT TOTALS"
)


def order_portfolio_report_sections(report):

    section_indexes = {
        line: index
        for index, line in enumerate(report)
        if line in PORTFOLIO_REPORT_SECTION_ORDER
    }

    if not section_indexes:
        return report

    ordered_indexes = sorted(section_indexes.values())
    prefix = report[:ordered_indexes[0]]
    sections = {}

    for position, start_index in enumerate(ordered_indexes):
        if position + 1 < len(ordered_indexes):
            end_index = ordered_indexes[position + 1]
        else:
            end_index = len(report)

        sections[report[start_index]] = report[start_index:end_index]

    ordered_report = prefix[:]

    for section_name in PORTFOLIO_REPORT_SECTION_ORDER:
        ordered_report.extend(sections.get(section_name, []))

    return ordered_report


def get_capital_deployment(buy_list, amount):

    deployment_candidates = [
        candidate
        for candidate in buy_list
        if (
            str(candidate.get("asset_class", "unknown")).strip().lower() != "cash"
            or str(candidate.get("priority", "")).strip().lower() == "high"
        )
    ]

    if not deployment_candidates or amount <= 0:
        return []

    scores = [
        max(float(candidate.get("total_score", 0) or 0), 0)
        for candidate in deployment_candidates
    ]
    total_score = sum(scores)

    if total_score <= 0:
        return []

    exact_allocations = [
        amount * score / total_score
        for score in scores
    ]
    allocations = [
        int(allocation)
        for allocation in exact_allocations
    ]
    dollars_remaining = amount - sum(allocations)

    remainder_order = sorted(
        range(len(deployment_candidates)),
        key=lambda index: (
            -(exact_allocations[index] - allocations[index]),
            index
        )
    )

    for index in remainder_order[:dollars_remaining]:
        allocations[index] += 1

    return [
        {
            "ticker": candidate["ticker"],
            "allocation": allocation
        }
        for candidate, allocation in zip(deployment_candidates, allocations)
    ]


def get_candidate_holding_action(candidate, position):

    candidate_score = candidate.get("total_score", 0) or 0
    thesis_status = position.get("thesis_status", "missing")
    conviction = position.get("conviction", "unrated")
    holding_score = get_holding_comparable_score(position)

    if not are_asset_classes_compatible(candidate, position):
        return "Not comparable asset objective"

    if thesis_status == "inactive":
        return "Review holding immediately before adding candidate"

    if candidate_score > holding_score and conviction == "low":
        return "Candidate may be superior to low-conviction holding"

    return "No replacement signal"


def get_account_type(account_name):

    account_name = account_name.lower()

    if "roth" in account_name:
        return "Roth"

    elif "ira" in account_name:
        return "Traditional IRA"

    elif "brokerage" in account_name:
        return "Taxable"

    else:
        return "Unknown"


def load_targets(report):

    targets = {}

    with open("../02_Data/targets.csv", "r") as file:

        reader = csv.DictReader(file)
        required_columns = {"ticker", "target_percent"}
        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:
            report.append(
                f"WARNING: targets.csv missing required columns: {', '.join(sorted(missing_columns))}"
            )
            return targets

        for line_number, row in enumerate(reader, start=2):
            try:
                target_percent = float(row["target_percent"])
            except (TypeError, ValueError):
                report.append(
                    f"WARNING: targets.csv line {line_number}: target_percent must be numeric."
                )
                continue

            if target_percent < 0:
                report.append(
                    f"WARNING: targets.csv line {line_number}: target_percent must be >= 0."
                )
                continue

            targets[row["ticker"]] = target_percent

    target_total = sum(targets.values())

    if abs(target_total - 100) > 0.000001:
        report.append(
            f"WARNING: targets.csv target_percent values sum to {target_total:.2f}, expected 100.00."
        )

    return targets


def get_portfolio_report():

    report = []
    holdings = []
    positions = []

    total_value = 0
    account_totals = {}
    ticker_totals = {}
    allocation_differences = {}

    report.append("Portfolio Manager operational.")
    report.append("")

    targets = load_targets(report)
    policy = get_policy()

    with open("../02_Data/holdings.csv", "r") as file:

        reader = csv.DictReader(file)
        required_columns = {"account", "ticker", "shares", "cost_basis"}
        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:
            report.append(
                f"WARNING: holdings.csv missing required columns: {', '.join(sorted(missing_columns))}"
            )
        else:
            for line_number, row in enumerate(reader, start=2):
                try:
                    shares = float(row["shares"])
                except (TypeError, ValueError):
                    report.append(
                        f"WARNING: holdings.csv line {line_number}: shares must be numeric."
                    )
                    continue

                if shares < 0:
                    report.append(
                        f"WARNING: holdings.csv line {line_number}: shares must be >= 0."
                    )
                    continue

                try:
                    cost_basis = float(row["cost_basis"])
                except (TypeError, ValueError):
                    report.append(
                        f"WARNING: holdings.csv line {line_number}: cost_basis must be numeric."
                    )
                    continue

                if cost_basis < 0:
                    report.append(
                        f"WARNING: holdings.csv line {line_number}: cost_basis must be >= 0."
                    )
                    continue

                ticker = row["ticker"]
                security_info = None
                thesis_info = get_thesis(ticker)

                if ticker != "CASH0":
                    security_info = get_security_info(ticker)

                    if not security_info:
                        report.append(
                            f"WARNING: {ticker}: Security metadata missing."
                        )

                holdings.append({
                    "account": row["account"],
                    "ticker": ticker,
                    "shares": shares,
                    "cost_basis": cost_basis,
                    "security_info": security_info,
                    "thesis_info": thesis_info
                })

    for holding in holdings:

        account = holding["account"]
        account_type = get_account_type(account)
        ticker = holding["ticker"]
        shares = holding["shares"]
        cost_basis = holding["cost_basis"]

        try:

            if ticker == "CASH0":
                price = 1
            else:
                stock = yf.Ticker(ticker)
                price = stock.fast_info["last_price"]

            position_value = shares * price

            if ticker == "CASH0":
                gain_loss = 0
                gain_loss_percent = 0
                cost_basis = position_value
            else:
                gain_loss = position_value - cost_basis

                if cost_basis > 0:
                    gain_loss_percent = (gain_loss / cost_basis) * 100
                else:
                    gain_loss_percent = 0

            total_value += position_value

            if account not in account_totals:
                account_totals[account] = 0

            account_totals[account] += position_value

            if ticker not in ticker_totals:
                ticker_totals[ticker] = 0

            ticker_totals[ticker] += position_value

            if ticker == "CASH0":
                security_name = "Cash"
                category = "Cash"
                expense_ratio = 0
            else:
                security_info = holding["security_info"]

                if security_info:
                    security_name = security_info["name"]
                    category = security_info["category"]
                    expense_ratio = float(security_info["expense_ratio"])
                else:
                    security_name = "Unknown"
                    category = "Unknown"
                    expense_ratio = 0

            thesis_info = holding["thesis_info"]

            if thesis_info:
                thesis = thesis_info["thesis"]
                thesis_status = thesis_info["thesis_status"]
                conviction = thesis_info["conviction"]
            else:
                thesis = "No thesis on file."
                thesis_status = "missing"
                conviction = "unrated"

            positions.append({
                "account": account,
                "account_type": account_type,
                "ticker": ticker,
                "name": security_name,
                "category": category,
                "expense_ratio": expense_ratio,
                "shares": shares,
                "price": price,
                "value": position_value,
                "cost_basis": cost_basis,
                "gain_loss": gain_loss,
                "gain_loss_percent": gain_loss_percent,
                "thesis": thesis,
                "thesis_status": thesis_status,
                "conviction": conviction
            })

        except:
            report.append(
                f"WARNING: {account} | {ticker}: Price lookup failed; position excluded from calculations."
            )

    for ticker, value in ticker_totals.items():
        if total_value > 0:
            allocation = (value / total_value) * 100
        else:
            allocation = 0

        allocation_differences[ticker] = allocation - targets.get(ticker, 0)

    report.append("POSITIONS")
    report.append("")

    for position in positions:
        report.append(
            f"{position['account']} ({position['account_type']}) | {position['ticker']}: "
            f"{position['name']} | "
            f"{position['category']} | "
            f"{position['shares']} shares | "
            f"Price ${position['price']:.2f} | "
            f"Value ${position['value']:.2f} | "
            f"Cost Basis ${position['cost_basis']:.2f} | "
            f"Gain/Loss ${position['gain_loss']:.2f} | "
            f"Gain/Loss {position['gain_loss_percent']:.2f}% | "
            f"Thesis Status {position['thesis_status']} | "
            f"Conviction {position['conviction']}"
        )

    report.append("")
    report.append("TICKER ALLOCATION")
    report.append("")

    for ticker, value in ticker_totals.items():

        if total_value > 0:
            allocation = (value / total_value) * 100
        else:
            allocation = 0

        target = targets.get(ticker, 0)
        difference = allocation - target

        report.append(
            f"{ticker}: Value ${value:.2f} | "
            f"Allocation {allocation:.2f}% | "
            f"Target {target:.2f}% | "
            f"Difference {difference:.2f}%"
        )

    report.append("")
    report.append("REBALANCE ALERTS")
    report.append("")

    rebalance_alert_count = 0

    for ticker, value in ticker_totals.items():

        if total_value > 0:
            allocation = (value / total_value) * 100
        else:
            allocation = 0

        target = targets.get(ticker, 0)
        difference = allocation - target

        if difference >= 5:
            report.append(
                f"{ticker}: OVERWEIGHT by {difference:.2f}%"
            )
            rebalance_alert_count += 1

        elif difference <= -5:
            report.append(
                f"{ticker}: UNDERWEIGHT by {abs(difference):.2f}%"
            )
            rebalance_alert_count += 1

    if rebalance_alert_count == 0:
        report.append("No rebalance alerts.")

    report.append("")
    report.append("TAX IMPACT NOTES")
    report.append("")

    tax_note_count = 0

    for position in positions:

        ticker = position["ticker"]
        account_type = position["account_type"]
        gain_loss = position["gain_loss"]
        value = position["value"]

        if ticker == "CASH0":
            continue

        if account_type == "Roth":
            report.append(
                f"{ticker}: Roth position. No current tax impact from selling."
            )
            tax_note_count += 1
        
        elif account_type == "Taxable":

            if gain_loss >= 1000:

                report.append(
                    f"{ticker}: LARGE taxable gain (${gain_loss:.2f}). Significant tax impact if sold."
                )
                tax_note_count += 1

            elif gain_loss >= 500:

                report.append(
                    f"{ticker}: Moderate taxable gain (${gain_loss:.2f}). Review tax consequences before selling."
                )
                tax_note_count += 1

        elif gain_loss <= -500:

            report.append(
                f"{ticker}: Large unrealized loss (${abs(gain_loss):.2f}). Strong tax-loss harvesting candidate."
            )
            tax_note_count += 1

        elif gain_loss <= -100:

            report.append(
                f"{ticker}: Moderate unrealized loss (${abs(gain_loss):.2f}). Possible tax-loss harvesting candidate."
            )
            tax_note_count += 1

    if tax_note_count == 0:
        report.append("No material tax impact notes.")

    report.append("")
    report.append("RECOMMENDATIONS")
    report.append("")

    recommendation_count = 0

    for ticker, value in ticker_totals.items():

        if ticker == "CASH0":
            continue

        if total_value > 0:
            allocation = (value / total_value) * 100
        else:
            allocation = 0

        target = targets.get(ticker, 0)
        difference = allocation - target

        related_positions = []

        for position in positions:
            if position["ticker"] == ticker:
                related_positions.append(position)

        taxable_gain = 0
        taxable_loss = 0
        roth_value = 0
        thesis_status = "missing"
        conviction = "unrated"

        for position in related_positions:

            thesis_status = position["thesis_status"]
            conviction = position["conviction"]

            if position["account_type"] == "Taxable":

                if position["gain_loss"] > 0:
                    taxable_gain += position["gain_loss"]

                elif position["gain_loss"] < 0:
                    taxable_loss += abs(position["gain_loss"])

            elif position["account_type"] == "Roth":
                roth_value += position["value"]

        if thesis_status == "inactive":

            report.append(
                f"{ticker}: Thesis is inactive. Recommendation: Review immediately."
            )
            recommendation_count += 1

        elif difference >= 5 and conviction == "high" and taxable_gain > 0:

            report.append(
                f"{ticker}: Overweight with high conviction and a taxable gain. Recommendation: Hold and monitor."
            )
            recommendation_count += 1

        elif difference >= 5 and conviction == "low":

            report.append(
                f"{ticker}: Overweight with low conviction. Recommendation: Consider reducing."
            )
            recommendation_count += 1

        elif difference >= 10:

            if taxable_gain >= 1000:
                report.append(
                    f"{ticker}: Severely overweight, but selling may trigger large taxable gain. Recommendation: Hold, monitor, and reduce only with deliberate tax planning."
                )
                recommendation_count += 1

            elif taxable_loss >= 500:
                report.append(
                    f"{ticker}: Severely overweight and has material taxable loss. Recommendation: Consider trimming or tax-loss harvesting review."
                )
                recommendation_count += 1

            else:
                report.append(
                    f"{ticker}: Severely overweight. Recommendation: Consider trimming position."
                )
                recommendation_count += 1

        elif difference >= 5:

            if taxable_gain >= 1000:
                report.append(
                    f"{ticker}: Moderately overweight, but taxable gain is significant. Recommendation: Avoid impulsive sale."
                )
                recommendation_count += 1

            else:
                report.append(
                    f"{ticker}: Moderately overweight. Recommendation: Do not add more capital."
                )
                recommendation_count += 1

        elif difference <= -10:

            report.append(
                f"{ticker}: Severely underweight. Recommendation: Prioritize future contributions here."
            )
            recommendation_count += 1

        elif difference <= -5:

            report.append(
                f"{ticker}: Moderately underweight. Recommendation: Consider adding with new cash."
            )
            recommendation_count += 1

    if recommendation_count == 0:
        report.append("No actionable recommendations.")

    report.append("")
    report.append("WATCHLIST")
    report.append("")

    watchlist = get_watchlist()

    for candidate in watchlist:
        report.append(
            f"{candidate['ticker']} | "
            f"Category {candidate['category']} | "
            f"Asset Class {candidate['asset_class']} | "
            f"Priority {candidate['priority']} | "
            f"Conviction {candidate['conviction']} | "
            f"Total Score {candidate['total_score']:g} | "
            f"Notes {candidate['notes']}"
        )

    report.append("")
    report.append("RESEARCH COVERAGE")
    report.append("")

    research_coverage = get_research_coverage(holdings, watchlist)

    report.append(
        f"Total Holdings: {research_coverage['total_holdings']}"
    )
    report.append(
        f"Covered Holdings: {research_coverage['covered_holdings']}"
    )
    report.append(
        f"Uncovered Holdings: {research_coverage['uncovered_holdings']}"
    )
    report.append(
        "Total Watchlist Candidates: "
        f"{research_coverage['total_watchlist_candidates']}"
    )
    report.append(
        "Covered Watchlist Candidates: "
        f"{research_coverage['covered_watchlist_candidates']}"
    )
    report.append(
        "Uncovered Watchlist Candidates: "
        f"{research_coverage['uncovered_watchlist_candidates']}"
    )

    report.append("")
    report.append("RESEARCH GAPS")
    report.append("")

    uncovered_holdings = get_uncovered_holdings(holdings)
    uncovered_watchlist = get_uncovered_watchlist(watchlist)

    if uncovered_holdings or uncovered_watchlist:
        for ticker in uncovered_holdings:
            report.append(f"Holding without thesis coverage: {ticker}")

        for ticker in uncovered_watchlist:
            report.append(f"Watchlist candidate without thesis coverage: {ticker}")
    else:
        report.append("No research coverage gaps detected.")

    report.append("")
    report.append("RESEARCH HEALTH")
    report.append("")

    research_health_checks = get_research_health_checks(
        positions,
        watchlist,
        allocation_differences
    )

    if research_health_checks:
        for health_check in research_health_checks:
            report.append(
                f"{health_check['severity']} | "
                f"{health_check['ticker']} | "
                f"{health_check['issue']} | "
                f"{health_check['recommendation']}"
            )
    else:
        report.append("No research health issues detected.")

    report.append("")
    report.append("RESEARCH HEALTH SUMMARY")
    report.append("")

    severity_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    for health_check in research_health_checks:
        severity = health_check.get("severity")

        if severity in severity_counts:
            severity_counts[severity] += 1

    report.append(
        f"High Severity Issues: {severity_counts['HIGH']}"
    )
    report.append(
        f"Medium Severity Issues: {severity_counts['MEDIUM']}"
    )
    report.append(
        f"Low Severity Issues: {severity_counts['LOW']}"
    )

    buy_list = get_buy_list()
    capital_deployment_plans = {
        amount: get_capital_deployment(buy_list, amount)
        for amount in DEPLOYMENT_AMOUNTS
    }
    sell_candidates = get_sell_candidates(
        positions,
        buy_list,
        allocation_differences
    )
    replacement_plan = get_replacement_plan(sell_candidates, buy_list)
    committee_summary = get_investment_committee_summary(
        buy_list,
        sell_candidates,
        replacement_plan,
        research_health_checks,
        capital_deployment_plans.get(1000, [])
    )

    report.append("")
    report.append("INVESTMENT COMMITTEE SUMMARY")
    report.append("")

    report.append(
        "Top Buy Candidate: "
        f"{committee_summary['top_buy_candidate'] or 'None'}"
    )
    report.append(
        "Top Sell Candidate: "
        f"{committee_summary['top_sell_candidate'] or 'None'}"
    )
    report.append(
        "Top Replacement Plan: "
        f"{committee_summary['top_replacement_plan'] or 'None'}"
    )
    report.append(
        "Top Research Issue: "
        f"{committee_summary['top_research_issue'] or 'None'}"
    )
    report.append(
        "Top Capital Deployment: "
        f"{committee_summary['top_capital_deployment'] or 'None'}"
    )

    decision_guardrails = get_decision_guardrails(
        buy_list,
        sell_candidates,
        replacement_plan,
        watchlist,
        positions,
        total_value
    )

    report.append("")
    report.append("DECISION GUARDRAILS")
    report.append("")

    if decision_guardrails:
        for guardrail in decision_guardrails:
            report.append(
                f"{guardrail['severity']} | "
                f"{guardrail['ticker']} | "
                f"{guardrail['issue']} | "
                f"{guardrail['recommendation']}"
            )
    else:
        report.append("No decision guardrail issues detected.")

    portfolio_exposure = get_portfolio_exposure(positions)

    report.append("")
    report.append("EXPOSURE SUMMARY")
    report.append("")

    report.append(
        "Largest Asset Class: "
        f"{portfolio_exposure['largest_asset_class'].title()} "
        f"{portfolio_exposure['largest_percentage']:.1f}%"
    )
    report.append("")
    report.append(
        "Diversification Score: "
        f"{portfolio_exposure['diversification_score']}"
    )

    report.append("")
    report.append("EXPOSURE DETAILS")
    report.append("")

    for category, percentage in portfolio_exposure["percentages"].items():
        report.append(f"{category.title()}: {percentage:.1f}%")

    report.append("")
    report.append("Top Asset Classes")
    report.append("")

    if portfolio_exposure["top_asset_classes"]:
        for rank, exposure in enumerate(
            portfolio_exposure["top_asset_classes"],
            start=1
        ):
            report.append(
                f"{rank}. {exposure['asset_class'].title()} "
                f"{exposure['percentage']:.1f}%"
            )
    else:
        report.append("No portfolio exposure.")

    concentration_risk = get_concentration_risk(positions)
    largest_position = concentration_risk["largest_position"]

    report.append("")
    report.append("CONCENTRATION RISK SUMMARY")
    report.append("")

    report.append(
        f"Largest Position: {largest_position['ticker']} | "
        f"{largest_position['percentage']:.1f}%"
    )
    report.append(
        "Top 3 Concentration: "
        f"{concentration_risk['top_3_concentration']:.1f}%"
    )
    report.append(
        "Top 5 Concentration: "
        f"{concentration_risk['top_5_concentration']:.1f}%"
    )
    report.append(
        "Portfolio Concentration Risk: "
        f"{concentration_risk['portfolio_risk']}"
    )

    report.append("")
    report.append("CONCENTRATION RISK DETAILS")
    report.append("")

    if concentration_risk["detail_rows"]:
        for issue in concentration_risk["detail_rows"]:
            report.append(
                f"{issue['severity']} | "
                f"{issue['ticker']} | "
                f"Position concentration {issue['percentage']:.1f}%"
            )
    else:
        report.append("No concentration risk issues detected.")

    factor_exposure = get_factor_exposure(positions)

    report.append("")
    report.append("FACTOR EXPOSURE SUMMARY")
    report.append("")

    report.append(
        "Dominant Factor: "
        f"{factor_exposure['dominant_factor'].replace('_', ' ').title()} "
        f"{factor_exposure['dominant_percentage']:.1f}%"
    )
    report.append(
        "Factor Concentration Risk: "
        f"{factor_exposure['concentration_risk']}"
    )

    report.append("")
    report.append("FACTOR EXPOSURE DETAILS")
    report.append("")

    if factor_exposure["ranked_factors"]:
        for exposure in factor_exposure["ranked_factors"]:
            factor_name = exposure["factor"].replace("_", " ").title()
            report.append(
                f"{factor_name}: {exposure['percentage']:.1f}%"
            )
    else:
        report.append("No factor exposure detected.")

    regime_analysis = get_regime_analysis(
        factor_exposure,
        get_default_regime()
    )
    alignment_score = regime_analysis["alignment_score"]

    if alignment_score >= 70:
        portfolio_alignment = "HIGH"
    elif alignment_score >= 40:
        portfolio_alignment = "MEDIUM"
    else:
        portfolio_alignment = "LOW"

    report.append("")
    report.append("REGIME ALIGNMENT SUMMARY")
    report.append("")

    report.append(
        "Current Regime: "
        f"{regime_analysis['regime'].replace('_', ' ').title()}"
    )
    report.append("")
    report.append(
        f"Confidence: {regime_analysis['confidence'].title()}"
    )
    report.append("")
    report.append(f"Alignment Score: {alignment_score:.0f}")
    report.append("")
    report.append(f"Portfolio Alignment: {portfolio_alignment}")

    report.append("")
    report.append("REGIME ALIGNMENT DETAILS")
    report.append("")

    has_regime_details = (
        regime_analysis["strengths"]
        or regime_analysis["gaps"]
        or regime_analysis["disfavored_exposures"]
    )

    if has_regime_details:
        if regime_analysis["strengths"]:
            report.append("Strengths")
            report.append("")

            for strength in regime_analysis["strengths"]:
                factor_name = strength["factor"].replace("_", " ").title()
                report.append(
                    f"Preferred Factor: {factor_name} | "
                    f"{strength['percentage']:.1f}%"
                )

        if regime_analysis["gaps"]:
            report.append("")
            report.append("Gaps")
            report.append("")

            for factor in regime_analysis["gaps"]:
                factor_name = factor.replace("_", " ").title()
                report.append(
                    f"Preferred Factor Missing: {factor_name}"
                )

        if regime_analysis["disfavored_exposures"]:
            report.append("")
            report.append("Disfavored Exposure")
            report.append("")

            for exposure in regime_analysis["disfavored_exposures"]:
                factor_name = exposure["factor"].replace("_", " ").title()
                report.append(
                    f"{factor_name} | {exposure['percentage']:.1f}%"
                )
    else:
        report.append("No regime alignment issues detected.")

    correlation_proxy = get_correlation_proxy(positions)
    highest_cluster = correlation_proxy["highest_cluster"]

    report.append("")
    report.append("CORRELATION PROXY SUMMARY")
    report.append("")

    if highest_cluster:
        report.append(
            "Highest Correlation Cluster: "
            f"{highest_cluster['group_name']} | "
            f"{highest_cluster['exposure']:.1f}%"
        )
    else:
        report.append("Highest Correlation Cluster: None | 0.0%")

    report.append(
        "Portfolio Correlation Proxy Risk: "
        f"{correlation_proxy['portfolio_risk']}"
    )
    report.append("")
    report.append(
        "Correlation proxy is based on classification overlap, "
        "not historical return correlation."
    )

    report.append("")
    report.append("CORRELATION PROXY DETAILS")
    report.append("")

    if correlation_proxy["clusters"]:
        for cluster in correlation_proxy["clusters"]:
            report.append(
                f"{cluster['severity']} | "
                f"{cluster['group_name']} | "
                f"Exposure {cluster['exposure']:.1f}% | "
                f"Members {', '.join(cluster['members'])}"
            )
    else:
        report.append(
            "No material correlation proxy clusters detected."
        )

    stress_test_report = get_stress_test_report(positions)
    worst_scenario = stress_test_report["worst_scenario"]

    report.append("")
    report.append("STRESS TEST SUMMARY")
    report.append("")

    if worst_scenario:
        estimated_dollar_loss = max(
            -worst_scenario["estimated_dollar_impact"],
            0
        )
        report.append(
            f"Worst Scenario: {worst_scenario['scenario']} | "
            f"Impact {worst_scenario['portfolio_impact']:.2f}%"
        )
        report.append(
            f"Estimated Dollar Loss: ${estimated_dollar_loss:,.2f}"
        )
    else:
        report.append("No stress test data available.")

    report.append("")
    report.append("STRESS TEST DETAILS")
    report.append("")

    if stress_test_report["scenarios"]:
        for scenario in stress_test_report["scenarios"]:
            loss_contributor = (
                scenario["largest_loss_contributor"] or "None"
            )
            gain_contributor = (
                scenario["largest_gain_contributor"] or "None"
            )
            report.append(
                f"{scenario['scenario']} | "
                f"Portfolio Impact {scenario['portfolio_impact']:.2f}% | "
                "Estimated Dollar Impact "
                f"${scenario['estimated_dollar_impact']:,.2f} | "
                f"Largest Loss Contributor {loss_contributor} | "
                f"Largest Gain Contributor {gain_contributor}"
            )
    else:
        report.append("No stress test data available.")

    macro_regime_report = get_macro_regime_report(positions)

    report.append("")
    report.append("MACRO REGIME SUMMARY")
    report.append("")

    if macro_regime_report["total_value"] > 0:
        report.append(
            "Current Regime: "
            f"{macro_regime_report['current_regime']} | "
            f"Confidence {macro_regime_report['confidence']:.2f}%"
        )
        report.append(
            f"Alignment Level: {macro_regime_report['alignment_level']}"
        )
        report.append(
            f"Top Signal: {macro_regime_report['top_signal']}"
        )
        report.append("")
        report.append(
            "Macro regime is inferred from portfolio classifications, "
            "not external macroeconomic data."
        )
    else:
        report.append("No macro regime data available.")

    report.append("")
    report.append("MACRO REGIME DETAILS")
    report.append("")

    if macro_regime_report["regime_ranking"]:
        for regime in macro_regime_report["regime_ranking"]:
            report.append(
                f"{regime['regime']} | "
                f"Score {regime['score']:.2f} | "
                f"Confidence {regime['confidence']:.2f}% | "
                f"Alignment {regime['alignment_level']} | "
                f"Top Signal {regime['top_signal']}"
            )
    else:
        report.append("No macro regime data available.")

    tax_optimization_report = get_tax_optimization_report(positions)

    report.append("")
    report.append("TAX OPTIMIZATION SUMMARY")
    report.append("")

    if tax_optimization_report["positions"]:
        report.append(
            "Taxable Assets: "
            f"{tax_optimization_report['taxable_percentage']:.1f}%"
        )
        report.append(
            "Tax Advantaged Assets: "
            f"{tax_optimization_report['tax_advantaged_percentage']:.1f}%"
        )
        report.append("")

        largest_taxable_gain = tax_optimization_report[
            "largest_taxable_gain"
        ]
        largest_taxable_loss = tax_optimization_report[
            "largest_taxable_loss"
        ]

        if largest_taxable_gain:
            report.append(
                "Largest Taxable Gain: "
                f"{largest_taxable_gain['ticker']} | "
                f"+${largest_taxable_gain['gain_loss']:,.2f}"
            )
        else:
            report.append("Largest Taxable Gain: None")

        if largest_taxable_loss:
            report.append(
                "Largest Taxable Loss: "
                f"{largest_taxable_loss['ticker']} | "
                f"-${abs(largest_taxable_loss['gain_loss']):,.2f}"
            )
        else:
            report.append("Largest Taxable Loss: None")

        report.append("")
        report.append(
            "Tax Loss Harvest Candidates: "
            f"{tax_optimization_report['tax_loss_harvest_candidates_count']}"
        )
        report.append(
            "Large Taxable Gain Positions: "
            f"{tax_optimization_report['large_taxable_gain_positions_count']}"
        )
        report.append("")
        report.append(
            "Tax analysis is informational only and not tax advice."
        )
    else:
        report.append("No tax optimization data available.")

    report.append("")
    report.append("TAX OPTIMIZATION DETAILS")
    report.append("")

    if tax_optimization_report["positions"]:
        for position in tax_optimization_report["positions"]:
            if position["gain_loss"] > 0:
                gain_loss_text = f"+${position['gain_loss']:,.2f}"
            elif position["gain_loss"] < 0:
                gain_loss_text = f"-${abs(position['gain_loss']):,.2f}"
            else:
                gain_loss_text = "$0.00"

            report.append(
                f"{position['ticker']} | "
                f"{position['tax_status']} | "
                f"{position['gain_status']} | "
                f"{gain_loss_text} | "
                f"{position['tax_flag']}"
            )
    else:
        report.append("No tax optimization data available.")

    historical_return_report = get_historical_return_report(positions)

    report.append("")
    report.append("HISTORICAL RETURN SUMMARY")
    report.append("")

    if historical_return_report["positions"]:
        largest_contributor = historical_return_report[
            "largest_return_contributor"
        ]
        highest_assumption = historical_return_report[
            "highest_return_assumption"
        ]
        lowest_assumption = historical_return_report[
            "lowest_return_assumption"
        ]

        report.append(
            "Portfolio Implied Long Run Return: "
            f"{historical_return_report['portfolio_implied_return']:.2f}%"
        )
        report.append(
            "Largest Return Contributor: "
            f"{largest_contributor['ticker']} | "
            f"{largest_contributor['weighted_contribution']:.2f}%"
        )
        report.append(
            "Highest Return Assumption: "
            f"{highest_assumption['ticker']} | "
            f"{highest_assumption['blended_return']:.2f}%"
        )
        report.append(
            "Lowest Return Assumption: "
            f"{lowest_assumption['ticker']} | "
            f"{lowest_assumption['blended_return']:.2f}%"
        )
        report.append("")
        report.append(
            "Historical return assumptions are static long-run estimates, "
            "not forecasts."
        )
    else:
        report.append("No historical return data available.")

    report.append("")
    report.append("HISTORICAL RETURN DETAILS")
    report.append("")

    if historical_return_report["positions"]:
        for position in historical_return_report["positions"]:
            factor_name = position["factor"].replace("_", " ").title()
            report.append(
                f"{position['ticker']} | "
                f"Allocation {position['allocation']:.2f}% | "
                f"Asset Class {position['asset_class']} "
                f"{position['asset_class_return']:.2f}% | "
                f"Factor {factor_name} "
                f"{position['factor_return']:.2f}% | "
                f"Blended {position['blended_return']:.2f}% | "
                f"Contribution {position['weighted_contribution']:.2f}%"
            )
    else:
        report.append("No historical return data available.")

    statistical_correlation_report = get_statistical_correlation_report(
        positions
    )

    report.append("")
    report.append("STATISTICAL CORRELATION SUMMARY")
    report.append("")

    if statistical_correlation_report["pairs"]:
        highest_pair = statistical_correlation_report[
            "highest_correlation_pair"
        ]
        lowest_pair = statistical_correlation_report[
            "lowest_correlation_pair"
        ]
        report.append(
            "Weighted Average Correlation: "
            f"{statistical_correlation_report['weighted_average_correlation']:.2f}"
        )
        report.append(
            "Correlation Risk Level: "
            f"{statistical_correlation_report['correlation_risk_level']}"
        )
        report.append(
            "Highest Correlation Pair: "
            f"{highest_pair['ticker_1']} / {highest_pair['ticker_2']} | "
            f"{highest_pair['correlation']:.2f}"
        )
        report.append(
            "Lowest Correlation Pair: "
            f"{lowest_pair['ticker_1']} / {lowest_pair['ticker_2']} | "
            f"{lowest_pair['correlation']:.2f}"
        )
        report.append("")
        report.append(
            "Correlation assumptions are static estimates, "
            "not historical return correlations."
        )
    else:
        report.append("No statistical correlation data available.")

    report.append("")
    report.append("STATISTICAL CORRELATION DETAILS")
    report.append("")

    if statistical_correlation_report["pairs"]:
        for pair in statistical_correlation_report["pairs"]:
            report.append(
                f"{pair['ticker_1']} / {pair['ticker_2']} | "
                f"Correlation {pair['correlation']:.2f} | "
                f"Basis {pair['basis']} | "
                f"Weight Impact {pair['weight_impact']:.2f}%"
            )
    else:
        report.append("No statistical correlation data available.")

    volatility_report = get_volatility_report(positions)

    report.append("")
    report.append("VOLATILITY SUMMARY")
    report.append("")

    if volatility_report["positions"]:
        largest_contributor = volatility_report[
            "largest_volatility_contributor"
        ]
        highest_volatility = volatility_report[
            "highest_volatility_position"
        ]
        report.append(
            "Portfolio Weighted Volatility: "
            f"{volatility_report['portfolio_weighted_volatility']:.2f}%"
        )
        report.append(
            "Volatility Risk Level: "
            f"{volatility_report['volatility_risk_level']}"
        )
        report.append(
            "Largest Volatility Contributor: "
            f"{largest_contributor['ticker']} | "
            f"{largest_contributor['weighted_contribution']:.2f}%"
        )
        report.append(
            "Highest Volatility Position: "
            f"{highest_volatility['ticker']} | "
            f"{highest_volatility['position_volatility']:.2f}%"
        )
        report.append(
            "High Volatility Positions: "
            f"{volatility_report['high_volatility_positions_count']}"
        )
        report.append("")
        report.append(
            "Volatility assumptions are static estimates, "
            "not historical realized volatility."
        )
    else:
        report.append("No volatility data available.")

    report.append("")
    report.append("VOLATILITY DETAILS")
    report.append("")

    if volatility_report["positions"]:
        for position in volatility_report["positions"]:
            factor_name = position["factor"].replace("_", " ").title()
            report.append(
                f"{position['ticker']} | "
                f"Allocation {position['allocation']:.2f}% | "
                f"Asset Class {position['asset_class']} Vol "
                f"{position['asset_class_volatility']:.2f}% | "
                f"Factor {factor_name} Adj "
                f"{position['factor_adjustment']:+.2f}% | "
                f"Position Vol {position['position_volatility']:.2f}% | "
                f"Contribution {position['weighted_contribution']:.2f}%"
            )
    else:
        report.append("No volatility data available.")

    monte_carlo_report = get_monte_carlo_report(positions)

    report.append("")
    report.append("MONTE CARLO SUMMARY")
    report.append("")

    if monte_carlo_report["simulation_count"]:
        report.append(
            f"Simulation Count: {monte_carlo_report['simulation_count']}"
        )
        report.append("")
        report.append(
            f"Expected Return: {monte_carlo_report['expected_return']:.2f}%"
        )
        report.append("")
        report.append(
            f"Median Return: {monte_carlo_report['median_return']:.2f}%"
        )
        report.append("")
        report.append(
            "Probability Positive: "
            f"{monte_carlo_report['probability_positive']:.1f}%"
        )
        report.append("")
        report.append(
            "Probability Negative: "
            f"{monte_carlo_report['probability_negative']:.1f}%"
        )
        report.append("")
        report.append(
            "Monte Carlo results are based on static assumptions "
            "and are not forecasts."
        )
        report.append(
            "Assumptions are derived from Phase 52 historical return "
            "and Phase 54 volatility estimates."
        )
        report.append(
            "This analysis is informational only and does not include "
            "investment advice, taxes, inflation, or withdrawals."
        )
    else:
        report.append("No Monte Carlo data available.")

    report.append("")
    report.append("MONTE CARLO DETAILS")
    report.append("")

    if monte_carlo_report["simulation_count"]:
        report.append(
            f"Best Outcome: {monte_carlo_report['best_outcome']:.2f}%"
        )
        report.append("")
        report.append(
            f"Worst Outcome: {monte_carlo_report['worst_outcome']:.2f}%"
        )
        report.append("")
        report.append(
            "Probability Return > 10%: "
            f"{monte_carlo_report['probability_greater_than_10']:.1f}%"
        )
        report.append("")
        report.append(
            "Probability Return < -10%: "
            f"{monte_carlo_report['probability_less_than_negative_10']:.1f}%"
        )
        report.append("")
        report.append("Assumption Inputs")
        report.append("")
        report.append(
            "Expected Return: "
            f"{monte_carlo_report['assumption_expected_return']:.2f}%"
        )
        report.append("")
        report.append(
            f"Volatility: {monte_carlo_report['assumption_volatility']:.2f}%"
        )
    else:
        report.append("No Monte Carlo data available.")

    historical_market_data_report = get_historical_market_data_report(
        positions
    )

    report.append("")
    report.append("HISTORICAL MARKET DATA SUMMARY")
    report.append("")

    if historical_market_data_report["tickers"]:
        report.append(
            "Market Data Coverage: "
            f"{historical_market_data_report[
                'market_data_coverage_percent'
            ]:.1f}%"
        )
        report.append(
            "Successful Tickers: "
            f"{historical_market_data_report['successful_tickers']}"
        )
        report.append(
            "Failed Tickers: "
            f"{historical_market_data_report['failed_tickers']}"
        )
        report.append(
            f"Cache Hits: {historical_market_data_report['cache_hits']}"
        )
        report.append(
            "Fresh Downloads: "
            f"{historical_market_data_report['fresh_downloads']}"
        )
        report.append(
            "Skipped Cash Tickers: "
            f"{historical_market_data_report['skipped_cash_tickers']}"
        )
        report.append("")
        report.append(
            "Historical market data is used for future analytics "
            "and does not alter recommendations yet."
        )
    else:
        report.append("No historical market data available.")

    report.append("")
    report.append("HISTORICAL MARKET DATA DETAILS")
    report.append("")

    if historical_market_data_report["tickers"]:
        for ticker_result in historical_market_data_report["tickers"]:
            if ticker_result["status"] == "FAILED":
                report.append(
                    f"{ticker_result['ticker']} | Status FAILED | "
                    f"Error {ticker_result['error']}"
                )
            else:
                latest_close = (
                    f"${ticker_result['latest_close']:.2f}"
                    if ticker_result["latest_close"] is not None
                    else "N/A"
                )
                report.append(
                    f"{ticker_result['ticker']} | "
                    f"Status {ticker_result['status']} | "
                    f"Rows {ticker_result['row_count']} | "
                    f"Start {ticker_result['start_date'] or 'N/A'} | "
                    f"End {ticker_result['end_date'] or 'N/A'} | "
                    f"Latest Close {latest_close} | "
                    f"Source {ticker_result['source'] or 'N/A'}"
                )
    else:
        report.append("No historical market data available.")

    report.append("")
    report.append("CANDIDATE RANKINGS")
    report.append("")

    ranked_candidates = get_ranked_watchlist()

    for rank, candidate in enumerate(ranked_candidates, start=1):
        candidate_score = candidate.get("total_score", 0) or 0
        report.append(
            f"{rank}. {candidate['ticker']} | "
            f"Total Score {candidate_score:g} | "
            f"Asset Class {candidate['asset_class']}"
        )

    report.append("")
    report.append("CANDIDATE VS HOLDINGS")
    report.append("")

    candidate_holding_issue_count = 0

    for candidate in ranked_candidates:
        candidate_score = candidate.get("total_score", 0) or 0

        for position in positions:
            holding_score = get_holding_comparable_score(position)
            action = get_candidate_holding_action(candidate, position)

            if action == "No replacement signal":
                continue

            if (
                action == "Not comparable asset objective"
                and candidate_score < 30
            ):
                continue

            report.append(
                f"{candidate['ticker']} | "
                f"Candidate Score {candidate_score:g} | "
                f"Holding {position['ticker']} | "
                f"Holding Comparable Score {holding_score:g} | "
                f"Action {action}"
            )
            candidate_holding_issue_count += 1

    if candidate_holding_issue_count == 0:
        report.append("No candidate-holding issues detected.")

    report.append("")
    report.append("BUY LIST")
    report.append("")

    if buy_list:
        for rank, candidate in enumerate(buy_list, start=1):
            report.append(
                f"{rank}. {candidate['ticker']} | "
                f"Total Score {candidate['total_score']:g} | "
                f"Asset Class {candidate['asset_class']} | "
                f"Priority {candidate['priority']} | "
                f"Conviction {candidate['conviction']} | "
                f"Reason {candidate['reason']}"
            )
    else:
        report.append("No eligible candidates.")

    report.append("")
    report.append("CAPITAL DEPLOYMENT")
    report.append("")

    if buy_list:
        for amount in DEPLOYMENT_AMOUNTS:
            allocations = capital_deployment_plans[amount]
            allocation_text = " | ".join(
                f"{allocation['ticker']} ${allocation['allocation']}"
                for allocation in allocations
            )
            report.append(f"Next ${amount}: {allocation_text}")
    else:
        report.append("No eligible candidates.")

    report.append("")
    report.append("SELL CANDIDATES")
    report.append("")

    if sell_candidates:
        for candidate in sell_candidates:
            report.append(
                f"{candidate['ticker']} | "
                f"Account {candidate['account']} | "
                f"Conviction {candidate['conviction']} | "
                f"Thesis Status {candidate['thesis_status']} | "
                f"Reason {candidate['reason']}"
            )
    else:
        report.append("No sell candidates.")

    report.append("")
    report.append("REPLACEMENT PLAN")
    report.append("")

    if replacement_plan:
        for replacement in replacement_plan:
            buy_ticker = replacement["buy"] or "None"
            report.append(
                f"Sell: {replacement['sell']} | "
                f"Buy: {buy_ticker} | "
                f"Reason: {replacement['reason']}"
            )
    else:
        report.append("No replacement actions.")

    report.append("")
    report.append("SECURITY CLASSIFICATION")
    report.append("")

    security_tickers = sorted({
        str(item.get("ticker") or "").strip().upper()
        for item in holdings + watchlist
        if str(item.get("ticker") or "").strip()
    })

    for ticker in security_tickers:
        classification = get_security_classification(ticker)
        report.append(
            f"{classification['ticker']} | "
            f"Asset Class {classification['asset_class']} | "
            f"Security Type {classification['security_type']} | "
            f"Risk Bucket {classification['risk_bucket']}"
        )

    report.append("")
    report.append("ACCOUNT TOTALS")
    report.append("")

    for account, value in account_totals.items():
        report.append(f"{account}: ${value:.2f}")

    report.append("")
    report.append(f"Total Portfolio Value: ${total_value:.2f}")

    return order_portfolio_report_sections(report)
