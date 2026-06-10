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

VALID_ASSET_CLASSES = {
    "equity",
    "bond",
    "cash",
    "bitcoin",
    "commodity",
    "alternative",
    "unknown"
}

PRIORITY_RANKS = {
    "high": 3,
    "medium": 2,
    "low": 1
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

    try:

        with open("../02_Data/security_master.csv", "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row["ticker"].upper() == ticker.upper():

                    return {
                        "ticker": row["ticker"],
                        "name": row["name"],
                        "category": row["category"],
                        "expense_ratio": row["expense_ratio"]
                    }

    except:

        pass

    return None


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

                asset_class = str(row.get("asset_class") or "").strip().lower()
                candidate["asset_class"] = (
                    asset_class if asset_class in VALID_ASSET_CLASSES else "unknown"
                )

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


def get_candidate(ticker):

    if not ticker:
        return None

    for candidate in get_watchlist():

        if candidate["ticker"].upper() == ticker.upper():
            return candidate

    return None


def get_thesis(ticker):

    try:

        with open("../02_Data/theses.csv", "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row["ticker"].upper() == ticker.upper():

                    return {
                        "ticker": row["ticker"],
                        "thesis": row["thesis"],
                        "thesis_status": row["thesis_status"].lower(),
                        "conviction": row["conviction"].lower()
                    }

    except (FileNotFoundError, KeyError, TypeError):

        pass

    return None
