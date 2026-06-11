import csv
import math


WATCHLIST_FIELDS = (
    "ticker",
    "category",
    "priority",
    "thesis_status",
    "conviction",
    "notes"
)

WATCHLIST_SCORE_FIELDS = (
    "quality_score",
    "valuation_score",
    "diversification_score",
    "risk_score"
)

ASSET_CLASS_TERMS = (
    ("cash", ("cash",)),
    ("bond", ("treasury", "bond", "fixed income", "short-term", "income")),
    ("bitcoin", ("bitcoin", "crypto")),
    (
        "commodity",
        (
            "commodity",
            "energy",
            "marine shipping",
            "mlp",
            "natural resource",
            "oil",
            "gas",
            "tanker"
        )
    ),
    (
        "equity",
        (
            "equity",
            "growth",
            "value",
            "blend",
            "large",
            "mid",
            "small",
            "stock"
        )
    ),
    (
        "alternative",
        (
            "reit",
            "real estate",
            "infrastructure",
            "private",
            "alternative"
        )
    )
)

ETF_TERMS = (
    "etf",
    "fund",
    "trust",
    "ishares",
    "spdr",
    "schwab",
    "vanguard",
    "invesco",
    "alpha architect"
)

EXPOSURE_CATEGORIES = (
    "equity",
    "bond",
    "cash",
    "bitcoin",
    "commodity",
    "alternative",
    "unknown"
)

PRIORITY_RANKS = {
    "high": 3,
    "medium": 2,
    "low": 1
}

HOLDING_CONVICTION_SCORES = {
    "high": 30,
    "medium": 20,
    "low": 10
}

RESEARCH_HEALTH_SEVERITY_RANKS = {
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3
}


def get_score(value):

    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0

    if not math.isfinite(score) or score < 1 or score > 10:
        return 0

    return score


def get_security_info(ticker):

    normalized_ticker = str(ticker or "").strip()

    if not normalized_ticker:
        return None

    try:

        with open("../02_Data/security_master.csv", "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                row_ticker = str(row.get("ticker") or "").strip()

                if row_ticker.upper() == normalized_ticker.upper():

                    return {
                        "ticker": row_ticker,
                        "name": str(row.get("name") or "").strip(),
                        "category": str(row.get("category") or "").strip(),
                        "expense_ratio": str(
                            row.get("expense_ratio") or ""
                        ).strip()
                    }

    except (FileNotFoundError, OSError, csv.Error):

        pass

    return None


def classify_security(ticker, category=None, name=None):

    normalized_ticker = str(ticker or "").strip().upper()
    description = " ".join(
        value
        for value in (
            str(category or "").strip().lower(),
            str(name or "").strip().lower()
        )
        if value
    )

    if normalized_ticker == "CASH0":
        asset_class = "cash"
    else:
        asset_class = "unknown"

        for candidate_asset_class, terms in ASSET_CLASS_TERMS:
            if any(term in description for term in terms):
                asset_class = candidate_asset_class
                break

    if normalized_ticker == "CASH0":
        security_type = "cash"
    elif any(term in description for term in ETF_TERMS):
        security_type = "ETF"
    elif asset_class in {"equity", "commodity", "bitcoin", "alternative"}:
        security_type = "stock"
    else:
        security_type = "unknown"

    if asset_class in {"cash", "bond"}:
        risk_bucket = "low"
    elif asset_class == "equity" and security_type == "ETF":
        risk_bucket = "medium"
    elif asset_class == "equity" and security_type == "stock":
        risk_bucket = "high"
    elif asset_class in {"bitcoin", "commodity", "alternative"}:
        risk_bucket = "speculative"
    else:
        risk_bucket = "unknown"

    return {
        "ticker": normalized_ticker,
        "asset_class": asset_class,
        "security_type": security_type,
        "risk_bucket": risk_bucket
    }


def get_security_classification(ticker):

    security_info = get_security_info(ticker)

    if security_info:
        return classify_security(
            ticker,
            category=security_info.get("category"),
            name=security_info.get("name")
        )

    return classify_security(ticker)


def get_portfolio_exposure(positions):

    category_values = {
        category: 0
        for category in EXPOSURE_CATEGORIES
    }

    for position in positions or []:
        try:
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not math.isfinite(value) or value <= 0:
            continue

        try:
            classification = classify_security(
                position.get("ticker"),
                category=position.get("category"),
                name=position.get("name")
            )
        except AttributeError:
            classification = {"asset_class": "unknown"}

        asset_class = classification.get("asset_class", "unknown")

        if asset_class == "unknown":
            try:
                classification = get_security_classification(
                    position.get("ticker")
                )
            except AttributeError:
                classification = {"asset_class": "unknown"}

            asset_class = classification.get("asset_class", "unknown")

        if asset_class not in category_values:
            asset_class = "unknown"

        category_values[asset_class] += value

    total_value = sum(category_values.values())

    if total_value > 0:
        percentages = {
            category: value / total_value * 100
            for category, value in category_values.items()
        }
    else:
        percentages = {
            category: 0
            for category in EXPOSURE_CATEGORIES
        }

    top_asset_classes = sorted(
        (
            {
                "asset_class": category,
                "value": category_values[category],
                "percentage": percentages[category]
            }
            for category in EXPOSURE_CATEGORIES
            if category_values[category] > 0
        ),
        key=lambda exposure: (
            -exposure["percentage"],
            EXPOSURE_CATEGORIES.index(exposure["asset_class"])
        )
    )

    if top_asset_classes:
        largest_asset_class = top_asset_classes[0]["asset_class"]
        largest_percentage = top_asset_classes[0]["percentage"]
    else:
        largest_asset_class = "unknown"
        largest_percentage = 0

    if largest_percentage <= 60:
        diversification_score = "HIGH"
    elif largest_percentage <= 80:
        diversification_score = "MEDIUM"
    else:
        diversification_score = "LOW"

    return {
        "total_value": total_value,
        "category_values": category_values,
        "percentages": percentages,
        "largest_asset_class": largest_asset_class,
        "largest_percentage": largest_percentage,
        "diversification_score": diversification_score,
        "top_asset_classes": top_asset_classes
    }


def get_concentration_risk(positions):

    ticker_values = {}

    for position in positions or []:
        try:
            ticker = str(position.get("ticker") or "UNKNOWN").strip().upper()
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not ticker:
            ticker = "UNKNOWN"

        if not math.isfinite(value) or value <= 0:
            continue

        ticker_values[ticker] = ticker_values.get(ticker, 0) + value

    total_value = sum(ticker_values.values())
    ranked_positions = sorted(
        ticker_values.items(),
        key=lambda item: (-item[1], item[0])
    )

    position_concentrations = []

    for ticker, value in ranked_positions:
        percentage = value / total_value * 100 if total_value > 0 else 0

        if percentage >= 25:
            severity = "HIGH"
        elif percentage >= 15:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        position_concentrations.append({
            "ticker": ticker,
            "value": value,
            "percentage": percentage,
            "severity": severity
        })

    if position_concentrations:
        largest_position = position_concentrations[0]
    else:
        largest_position = {
            "ticker": "None",
            "value": 0,
            "percentage": 0,
            "severity": "LOW"
        }

    if total_value > 0:
        top_3_concentration = (
            sum(value for _, value in ranked_positions[:3])
            / total_value
            * 100
        )
        top_5_concentration = (
            sum(value for _, value in ranked_positions[:5])
            / total_value
            * 100
        )
    else:
        top_3_concentration = 0
        top_5_concentration = 0

    largest_percentage = largest_position["percentage"]

    if largest_percentage >= 25 or top_5_concentration >= 75:
        portfolio_risk = "HIGH"
    elif largest_percentage >= 15 or top_5_concentration >= 60:
        portfolio_risk = "MEDIUM"
    else:
        portfolio_risk = "LOW"

    alert_eligible_positions = [
        position
        for position in position_concentrations
        if position["ticker"] != "CASH0"
    ]
    elevated_issues = [
        position
        for position in alert_eligible_positions
        if position["severity"] in {"HIGH", "MEDIUM"}
    ]
    detail_rows = (
        elevated_issues
        if elevated_issues
        else [
            position
            for position in alert_eligible_positions
            if position["severity"] == "LOW"
        ]
    )

    return {
        "total_value": total_value,
        "ticker_values": ticker_values,
        "largest_position": largest_position,
        "top_3_concentration": top_3_concentration,
        "top_5_concentration": top_5_concentration,
        "portfolio_risk": portfolio_risk,
        "position_concentrations": position_concentrations,
        "detail_rows": detail_rows
    }


def get_watchlist():

    watchlist = []

    try:

        with open("../02_Data/watchlist.csv", "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                candidate = {}

                for field in WATCHLIST_FIELDS:
                    value = row.get(field)
                    candidate[field] = value.strip() if value and value.strip() else "Unknown"

                classification = get_security_classification(
                    candidate["ticker"]
                )
                candidate["asset_class"] = classification["asset_class"]

                for field in WATCHLIST_SCORE_FIELDS:
                    candidate[field] = get_score(row.get(field))

                candidate["total_score"] = sum(
                    candidate[field] for field in WATCHLIST_SCORE_FIELDS
                )

                watchlist.append(candidate)

    except (FileNotFoundError, OSError, csv.Error):

        pass

    return watchlist


def get_ranked_watchlist():

    return sorted(
        get_watchlist(),
        key=lambda candidate: candidate.get("total_score", 0) or 0,
        reverse=True
    )


def get_buy_list_reason(candidate):

    total_score = candidate.get("total_score", 0) or 0
    priority = str(candidate.get("priority", "")).strip().lower()
    asset_class = str(candidate.get("asset_class", "unknown")).strip().lower()

    if priority == "high" and total_score >= 30 and asset_class == "equity":
        return "Highest ranked equity candidate."

    if priority == "high":
        return "High priority research candidate."

    if priority == "medium":
        return "Diversification or secondary opportunity."

    if priority == "low" and asset_class == "cash":
        return "Cash management candidate; excluded from growth deployment."

    return "Lower priority monitoring candidate."


def get_buy_list():

    buy_list = []

    for candidate in get_ranked_watchlist():
        total_score = candidate.get("total_score", 0) or 0
        thesis_status = str(candidate.get("thesis_status", "")).strip().lower()
        priority = str(candidate.get("priority", "")).strip().lower()
        asset_class = str(candidate.get("asset_class", "unknown")).strip().lower()

        if (
            thesis_status == "inactive"
            or total_score <= 0
            or (asset_class == "cash" and priority != "high")
        ):
            continue

        buy_candidate = candidate.copy()
        buy_candidate["reason"] = get_buy_list_reason(candidate)
        buy_list.append(buy_candidate)

    return sorted(
        buy_list,
        key=lambda candidate: (
            -(candidate.get("total_score", 0) or 0),
            -PRIORITY_RANKS.get(
                str(candidate.get("priority", "")).strip().lower(),
                0
            )
        )
    )


def get_holding_asset_class(position):

    return classify_security(
        position.get("ticker"),
        category=position.get("category"),
        name=position.get("name")
    )["asset_class"]


def are_asset_classes_compatible(candidate, position):

    candidate_asset_class = str(
        candidate.get("asset_class", "unknown")
    ).strip().lower()
    holding_asset_class = get_holding_asset_class(position)

    if candidate_asset_class == "unknown":
        return False

    compatible_holding_classes = {
        "equity": {"equity"},
        "cash": {"cash"},
        "bond": {"bond", "cash"},
        "bitcoin": {"bitcoin"},
        "commodity": {"commodity"},
        "alternative": {"alternative", "bitcoin"}
    }

    return holding_asset_class in compatible_holding_classes.get(
        candidate_asset_class,
        set()
    )


def get_holding_comparable_score(position):

    thesis_status = str(
        position.get("thesis_status", "missing")
    ).strip().lower()
    conviction = str(position.get("conviction", "unrated")).strip().lower()

    if thesis_status in {"inactive", "missing"} or conviction == "unrated":
        return 0

    return HOLDING_CONVICTION_SCORES.get(conviction, 0)


def get_compatible_candidates(position, candidates):

    return [
        candidate
        for candidate in candidates
        if are_asset_classes_compatible(candidate, position)
    ]


def get_sell_candidates(positions, buy_list, allocation_differences):

    sell_candidates = []

    for position in positions:
        ticker = str(position.get("ticker", "")).strip().upper()
        thesis_status = str(
            position.get("thesis_status", "missing")
        ).strip().lower()
        conviction = str(position.get("conviction", "unrated")).strip().lower()

        if ticker == "CASH0":
            continue

        if thesis_status == "active" and conviction == "high":
            continue

        compatible_candidates = get_compatible_candidates(position, buy_list)

        if not compatible_candidates:
            continue

        holding_score = get_holding_comparable_score(position)
        has_superior_candidate = any(
            (candidate.get("total_score", 0) or 0) > holding_score
            for candidate in compatible_candidates
        )

        if thesis_status == "inactive":
            priority = 1
            reason = "Investment thesis no longer active."
        elif conviction == "low" and has_superior_candidate:
            priority = 2
            reason = "Higher ranked candidate available."
        elif (
            allocation_differences.get(ticker, 0) > 10
            and conviction != "high"
        ):
            priority = 3
            reason = "Position size exceeds target allocation."
        else:
            continue

        sell_candidate = position.copy()
        sell_candidate["priority"] = priority
        sell_candidate["reason"] = reason
        sell_candidates.append(sell_candidate)

    return sorted(
        sell_candidates,
        key=lambda candidate: (
            candidate["priority"],
            candidate.get("ticker", ""),
            candidate.get("account", "")
        )
    )


def get_replacement_plan(sell_candidates, buy_list):

    replacement_plan = []

    for holding in sell_candidates:
        holding_score = get_holding_comparable_score(holding)
        compatible_candidates = get_compatible_candidates(holding, buy_list)
        superior_candidates = [
            candidate
            for candidate in compatible_candidates
            if (candidate.get("total_score", 0) or 0) > holding_score
        ]

        if superior_candidates:
            replacement = max(
                superior_candidates,
                key=lambda candidate: candidate.get("total_score", 0) or 0
            )
            buy_ticker = replacement["ticker"]
            reason = holding["reason"]
        else:
            buy_ticker = None
            reason = "No superior compatible candidate identified."

        replacement_plan.append({
            "sell": holding["ticker"],
            "account": holding["account"],
            "buy": buy_ticker,
            "reason": reason
        })

    return replacement_plan


def get_candidate(ticker):

    if not ticker:
        return None

    for candidate in get_watchlist():

        if candidate["ticker"].upper() == ticker.upper():
            return candidate

    return None


def get_theses():

    theses = {}

    try:

        with open("../02_Data/theses.csv", "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:
                ticker = str(row.get("ticker") or "").strip()

                if not ticker:
                    continue

                theses[ticker.upper()] = {
                    "ticker": ticker,
                    "thesis": str(row.get("thesis") or "").strip(),
                    "thesis_status": str(
                        row.get("thesis_status") or ""
                    ).strip().lower(),
                    "conviction": str(
                        row.get("conviction") or ""
                    ).strip().lower()
                }

    except (FileNotFoundError, OSError, csv.Error):

        pass

    return theses


def get_thesis(ticker):

    if not ticker:
        return None

    return get_theses().get(str(ticker).strip().upper())


def get_unique_tickers(items):

    return {
        str(item.get("ticker") or "").strip().upper()
        for item in items
        if str(item.get("ticker") or "").strip()
    }


def get_uncovered_holdings(holdings):

    covered_tickers = set(get_theses())

    return sorted(
        get_unique_tickers(holdings) - covered_tickers
    )


def get_uncovered_watchlist(watchlist):

    covered_tickers = set(get_theses())

    return sorted(
        get_unique_tickers(watchlist) - covered_tickers
    )


def get_research_coverage(holdings, watchlist):

    holding_tickers = get_unique_tickers(holdings)
    watchlist_tickers = get_unique_tickers(watchlist)
    uncovered_holdings = get_uncovered_holdings(holdings)
    uncovered_watchlist = get_uncovered_watchlist(watchlist)

    return {
        "total_holdings": len(holding_tickers),
        "covered_holdings": len(holding_tickers) - len(uncovered_holdings),
        "uncovered_holdings": len(uncovered_holdings),
        "total_watchlist_candidates": len(watchlist_tickers),
        "covered_watchlist_candidates": (
            len(watchlist_tickers) - len(uncovered_watchlist)
        ),
        "uncovered_watchlist_candidates": len(uncovered_watchlist)
    }


def get_research_health_checks(holdings, watchlist, allocation_differences):

    health_checks = []

    for holding in holdings:
        ticker = str(holding.get("ticker") or "Unknown").strip().upper()
        thesis_status = str(
            holding.get("thesis_status") or "missing"
        ).strip().lower()
        conviction = str(
            holding.get("conviction") or "unrated"
        ).strip().lower()

        if thesis_status == "inactive":
            health_checks.append({
                "severity": "HIGH",
                "ticker": ticker,
                "issue": "Thesis inactive",
                "recommendation": "Review immediately"
            })

        if conviction == "low":
            health_checks.append({
                "severity": "MEDIUM",
                "ticker": ticker,
                "issue": "Low conviction holding",
                "recommendation": "Reevaluate thesis"
            })

        if (
            allocation_differences.get(ticker, 0) >= 5
            and conviction != "high"
        ):
            health_checks.append({
                "severity": "MEDIUM",
                "ticker": ticker,
                "issue": "Overweight position with conviction not high",
                "recommendation": "Review position size"
            })

    for candidate in watchlist:
        ticker = str(candidate.get("ticker") or "Unknown").strip().upper()
        thesis_status = str(
            candidate.get("thesis_status") or "unknown"
        ).strip().lower()
        conviction = str(
            candidate.get("conviction") or "unknown"
        ).strip().lower()

        try:
            total_score = float(candidate.get("total_score", 0) or 0)
        except (TypeError, ValueError):
            total_score = 0

        if total_score < 30:
            continue

        if conviction == "low":
            health_checks.append({
                "severity": "MEDIUM",
                "ticker": ticker,
                "issue": "High scoring candidate with low conviction",
                "recommendation": "Reevaluate candidate conviction"
            })

        if thesis_status == "inactive":
            health_checks.append({
                "severity": "HIGH",
                "ticker": ticker,
                "issue": "High score candidate thesis inactive",
                "recommendation": "Review immediately"
            })
        elif thesis_status == "watch":
            health_checks.append({
                "severity": "LOW",
                "ticker": ticker,
                "issue": "High score candidate still in watch status",
                "recommendation": "Complete research review"
            })

    return sorted(
        health_checks,
        key=lambda check: (
            RESEARCH_HEALTH_SEVERITY_RANKS.get(check["severity"], 99),
            check["ticker"],
            check["issue"]
        )
    )


def get_investment_committee_summary(
    buy_list,
    sell_candidates,
    replacement_plan,
    research_health_checks,
    capital_deployment
):

    summary = {
        "top_buy_candidate": None,
        "top_sell_candidate": None,
        "top_replacement_plan": None,
        "top_research_issue": None,
        "top_capital_deployment": None
    }

    if buy_list:
        candidate = buy_list[0]
        ticker = str(candidate.get("ticker") or "Unknown").strip().upper()
        reason = str(candidate.get("reason") or "No reason provided.").strip()
        summary["top_buy_candidate"] = f"{ticker} | Reason {reason}"

    if sell_candidates:
        candidate = sell_candidates[0]
        ticker = str(candidate.get("ticker") or "Unknown").strip().upper()
        reason = str(candidate.get("reason") or "No reason provided.").strip()
        summary["top_sell_candidate"] = f"{ticker} | Reason {reason}"

    if replacement_plan:
        replacement = replacement_plan[0]
        sell_ticker = str(
            replacement.get("sell") or "Unknown"
        ).strip().upper()
        raw_buy_ticker = replacement.get("buy")
        buy_ticker = (
            str(raw_buy_ticker).strip().upper()
            if raw_buy_ticker
            else "None"
        )
        reason = str(
            replacement.get("reason") or "No reason provided."
        ).strip()
        summary["top_replacement_plan"] = (
            f"Sell {sell_ticker} / Buy {buy_ticker} | Reason {reason}"
        )

    if research_health_checks:
        issue = min(
            research_health_checks,
            key=lambda check: (
                RESEARCH_HEALTH_SEVERITY_RANKS.get(
                    str(check.get("severity") or "").strip().upper(),
                    99
                ),
                str(check.get("ticker") or ""),
                str(check.get("issue") or "")
            )
        )
        severity = str(issue.get("severity") or "UNKNOWN").strip().upper()
        ticker = str(issue.get("ticker") or "Unknown").strip().upper()
        issue_text = str(issue.get("issue") or "Unknown issue").strip()
        summary["top_research_issue"] = (
            f"{severity} | {ticker} | Issue {issue_text}"
        )

    if capital_deployment:
        formatted_allocations = []

        for allocation in capital_deployment:
            ticker = str(
                allocation.get("ticker") or "Unknown"
            ).strip().upper()

            try:
                amount = int(allocation.get("allocation", 0) or 0)
            except (TypeError, ValueError):
                amount = 0

            formatted_allocations.append(f"{ticker} ${max(amount, 0)}")

        allocation_text = " | ".join(formatted_allocations)

        if allocation_text:
            summary["top_capital_deployment"] = (
                f"Next $1000 | {allocation_text}"
            )

    return summary


def get_decision_guardrails(
    buy_list,
    sell_candidates,
    replacement_plan,
    watchlist,
    positions,
    total_portfolio_value
):

    guardrails = []
    buy_candidates_by_ticker = {
        str(candidate.get("ticker") or "").strip().upper(): candidate
        for candidate in buy_list
        if str(candidate.get("ticker") or "").strip()
    }
    positions_by_key = {
        (
            str(position.get("ticker") or "").strip().upper(),
            str(position.get("account") or "").strip().lower()
        ): position
        for position in positions
        if str(position.get("ticker") or "").strip()
    }

    try:
        portfolio_value = float(total_portfolio_value or 0)
    except (TypeError, ValueError):
        portfolio_value = 0

    if not math.isfinite(portfolio_value) or portfolio_value < 0:
        portfolio_value = 0

    for replacement in replacement_plan:
        sell_ticker = str(
            replacement.get("sell") or "Unknown"
        ).strip().upper()
        buy_ticker = str(replacement.get("buy") or "").strip().upper()
        account = str(replacement.get("account") or "").strip().lower()

        if not buy_ticker:
            continue

        holding = positions_by_key.get((sell_ticker, account))

        if holding is None:
            holding = next(
                (
                    position
                    for position in positions
                    if str(position.get("ticker") or "").strip().upper()
                    == sell_ticker
                ),
                {}
            )

        candidate = buy_candidates_by_ticker.get(buy_ticker, {})
        holding_asset_class = get_holding_asset_class(holding)
        candidate_asset_class = str(
            candidate.get("asset_class") or "unknown"
        ).strip().lower()

        if holding_asset_class != candidate_asset_class:
            guardrails.append({
                "severity": "HIGH",
                "ticker": sell_ticker,
                "issue": "Replacement changes asset objective",
                "recommendation": "Manual review required before action"
            })

        holding_score = get_holding_comparable_score(holding)

        try:
            candidate_score = float(candidate.get("total_score", 0) or 0)
        except (TypeError, ValueError):
            candidate_score = 0

        if not math.isfinite(candidate_score):
            candidate_score = 0

        score_advantage = candidate_score - holding_score

        if 0 < score_advantage < 10:
            guardrails.append({
                "severity": "MEDIUM",
                "ticker": sell_ticker,
                "issue": "Replacement advantage is not material",
                "recommendation": "Avoid unnecessary trading"
            })

    for sell_candidate in sell_candidates:
        ticker = str(
            sell_candidate.get("ticker") or "Unknown"
        ).strip().upper()

        try:
            position_value = float(sell_candidate.get("value", 0) or 0)
        except (TypeError, ValueError):
            position_value = 0

        if not math.isfinite(position_value) or position_value < 0:
            position_value = 0

        if portfolio_value > 0 and position_value / portfolio_value > 0.20:
            guardrails.append({
                "severity": "HIGH",
                "ticker": ticker,
                "issue": "Major position change",
                "recommendation": "Require manual review before sale"
            })

    for candidate in watchlist:
        ticker = str(
            candidate.get("ticker") or "Unknown"
        ).strip().upper()
        thesis_status = str(
            candidate.get("thesis_status") or "unknown"
        ).strip().lower()

        try:
            total_score = float(candidate.get("total_score", 0) or 0)
        except (TypeError, ValueError):
            total_score = 0

        if not math.isfinite(total_score):
            total_score = 0

        if total_score >= 30 and thesis_status == "watch":
            guardrails.append({
                "severity": "MEDIUM",
                "ticker": ticker,
                "issue": "High-scoring candidate still in watch status",
                "recommendation": "Complete research before deployment"
            })

    if buy_list:
        top_buy = buy_list[0]
        priority = str(top_buy.get("priority") or "unknown").strip().lower()

        if priority == "low":
            guardrails.append({
                "severity": "MEDIUM",
                "ticker": str(
                    top_buy.get("ticker") or "Unknown"
                ).strip().upper(),
                "issue": "Low-priority candidate ranked as top buy",
                "recommendation": "Review scoring inputs"
            })

    return sorted(
        guardrails,
        key=lambda guardrail: (
            RESEARCH_HEALTH_SEVERITY_RANKS.get(
                guardrail.get("severity"),
                99
            ),
            guardrail.get("ticker", ""),
            guardrail.get("issue", "")
        )
    )
