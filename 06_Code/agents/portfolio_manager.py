import csv
import yfinance as yf
from agents.policy_agent import get_policy
from agents.research_agent import get_security_info


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


def load_targets():

    targets = {}

    with open("../02_Data/targets.csv", "r") as file:

        reader = csv.DictReader(file)

        for row in reader:
            targets[row["ticker"]] = float(row["target_percent"])

    return targets


def get_portfolio_report():

    report = []
    holdings = []
    positions = []

    total_value = 0
    account_totals = {}
    ticker_totals = {}

    targets = load_targets()
    policy = get_policy()

    with open("../02_Data/holdings.csv", "r") as file:

        reader = csv.DictReader(file)

        for row in reader:
            holdings.append(row)

    report.append("Portfolio Manager operational.")
    report.append("")

    for holding in holdings:

        account = holding["account"]
        account_type = get_account_type(account)
        ticker = holding["ticker"]
        shares = float(holding["shares"])
        cost_basis = float(holding["cost_basis"])

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
                security_info = get_security_info(ticker)

                if security_info:
                    security_name = security_info["name"]
                    category = security_info["category"]
                    expense_ratio = float(security_info["expense_ratio"])
                else:
                    security_name = "Unknown"
                    category = "Unknown"
                    expense_ratio = 0

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
                "gain_loss_percent": gain_loss_percent
            })

        except:
            report.append(
                f"WARNING: {account} | {ticker}: Price lookup failed; position excluded from calculations."
            )

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
            f"Gain/Loss {position['gain_loss_percent']:.2f}%"
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

        elif difference <= -5:
            report.append(
                f"{ticker}: UNDERWEIGHT by {abs(difference):.2f}%"
            )

    report.append("")
    report.append("TAX IMPACT NOTES")
    report.append("")

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
        
        elif account_type == "Taxable":

            if gain_loss >= 1000:

                report.append(
                    f"{ticker}: LARGE taxable gain (${gain_loss:.2f}). Significant tax impact if sold."
                )

            elif gain_loss >= 500:

                report.append(
                    f"{ticker}: Moderate taxable gain (${gain_loss:.2f}). Review tax consequences before selling."
                )

        elif gain_loss <= -500:

            report.append(
                f"{ticker}: Large unrealized loss (${abs(gain_loss):.2f}). Strong tax-loss harvesting candidate."
            )

        elif gain_loss <= -100:

            report.append(
                f"{ticker}: Moderate unrealized loss (${abs(gain_loss):.2f}). Possible tax-loss harvesting candidate."
            )

        else:

            report.append(
                f"{ticker}: No material tax consideration."
            )

    report.append("")
    report.append("RECOMMENDATIONS")
    report.append("")

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

        for position in related_positions:

            if position["account_type"] == "Taxable":

                if position["gain_loss"] > 0:
                    taxable_gain += position["gain_loss"]

                elif position["gain_loss"] < 0:
                    taxable_loss += abs(position["gain_loss"])

            elif position["account_type"] == "Roth":
                roth_value += position["value"]

        if difference >= 10:

            if taxable_gain >= 1000:
                report.append(
                    f"{ticker}: Severely overweight, but selling may trigger large taxable gain. Recommendation: Hold, monitor, and reduce only with deliberate tax planning."
                )

            elif taxable_loss >= 500:
                report.append(
                    f"{ticker}: Severely overweight and has material taxable loss. Recommendation: Consider trimming or tax-loss harvesting review."
                )

            else:
                report.append(
                    f"{ticker}: Severely overweight. Recommendation: Consider trimming position."
                )

        elif difference >= 5:

            if taxable_gain >= 1000:
                report.append(
                    f"{ticker}: Moderately overweight, but taxable gain is significant. Recommendation: Avoid impulsive sale."
                )

            else:
                report.append(
                    f"{ticker}: Moderately overweight. Recommendation: Do not add more capital."
                )

        elif difference <= -10:

            report.append(
                f"{ticker}: Severely underweight. Recommendation: Prioritize future contributions here."
            )

        elif difference <= -5:

            report.append(
                f"{ticker}: Moderately underweight. Recommendation: Consider adding with new cash."
            )

    report.append("")
    report.append("ACCOUNT TOTALS")
    report.append("")

    for account, value in account_totals.items():
        report.append(f"{account}: ${value:.2f}")

    report.append("")
    report.append(f"Total Portfolio Value: ${total_value:.2f}")

    return report
