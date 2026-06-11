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

FACTOR_CATEGORIES = (
    "growth",
    "value",
    "blend",
    "small",
    "mid",
    "large",
    "momentum",
    "quality",
    "income",
    "real_estate",
    "bitcoin",
    "commodity",
    "cash",
    "unknown"
)

FACTOR_TERMS = (
    ("growth", ("growth",)),
    ("value", ("value",)),
    ("blend", ("blend",)),
    ("small", ("small", "small-cap", "micro")),
    ("mid", ("mid", "mid-cap")),
    ("large", ("large", "large-cap")),
    ("momentum", ("momentum",)),
    ("quality", ("quality",)),
    ("income", ("income", "dividend", "yield")),
    ("real_estate", ("reit", "real estate")),
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
    )
)

MARKET_REGIMES = {
    "recession": {
        "preferred_factors": ("quality", "large", "income", "cash"),
        "neutral_factors": ("value",),
        "disfavored_factors": ("small", "commodity", "bitcoin"),
        "confidence": "medium"
    },
    "expansion": {
        "preferred_factors": ("small", "value", "momentum"),
        "neutral_factors": ("growth", "quality"),
        "disfavored_factors": ("cash",),
        "confidence": "medium"
    },
    "inflation": {
        "preferred_factors": ("commodity", "value", "income"),
        "neutral_factors": ("quality",),
        "disfavored_factors": ("growth", "cash"),
        "confidence": "medium"
    },
    "disinflation": {
        "preferred_factors": ("growth", "quality", "large"),
        "neutral_factors": ("value",),
        "disfavored_factors": ("commodity",),
        "confidence": "medium"
    },
    "risk_off": {
        "preferred_factors": ("cash", "quality", "large"),
        "neutral_factors": ("income",),
        "disfavored_factors": ("bitcoin", "commodity", "small"),
        "confidence": "low"
    },
    "risk_on": {
        "preferred_factors": ("momentum", "small", "growth", "bitcoin"),
        "neutral_factors": ("value",),
        "disfavored_factors": ("cash",),
        "confidence": "low"
    }
}

DEFAULT_REGIME = "expansion"

STRESS_SCENARIOS = {
    "2008_STYLE_CRISIS": {
        "equity": -0.50,
        "bond": 0.05,
        "cash": 0.00,
        "bitcoin": -0.80,
        "commodity": -0.40,
        "alternative": -0.35,
        "unknown": -0.25
    },
    "2022_INFLATION_SHOCK": {
        "equity": -0.25,
        "bond": -0.15,
        "cash": 0.00,
        "bitcoin": -0.60,
        "commodity": 0.15,
        "alternative": -0.20,
        "unknown": -0.15
    },
    "DOT_COM_BUST": {
        "equity": -0.35,
        "bond": 0.05,
        "cash": 0.00,
        "bitcoin": -0.70,
        "commodity": -0.10,
        "alternative": -0.25,
        "unknown": -0.20
    },
    "RISK_OFF_LIQUIDITY_EVENT": {
        "equity": -0.20,
        "bond": 0.03,
        "cash": 0.00,
        "bitcoin": -0.50,
        "commodity": -0.25,
        "alternative": -0.30,
        "unknown": -0.15
    }
}

MACRO_REGIME_DEFINITIONS = {
    "EXPANSION": {
        "asset_weights": {
            "equity": 1.00,
            "bitcoin": 0.70,
            "alternative": 0.40,
            "cash": -0.40,
            "bond": -0.20
        },
        "factor_weights": {
            "growth": 0.50,
            "momentum": 0.80,
            "small": 0.60,
            "bitcoin": 0.70
        }
    },
    "DISINFLATION": {
        "asset_weights": {
            "bond": 1.00,
            "equity": 0.30,
            "cash": 0.30,
            "commodity": -0.80
        },
        "factor_weights": {
            "growth": 0.80,
            "quality": 0.70,
            "large": 0.50,
            "commodity": -0.80
        }
    },
    "INFLATION_SHOCK": {
        "asset_weights": {
            "commodity": 1.50,
            "alternative": 0.50,
            "bond": -0.60
        },
        "factor_weights": {
            "commodity": 1.20,
            "value": 0.70,
            "income": 0.40,
            "real_estate": 0.50,
            "growth": -0.40
        }
    },
    "RECESSION": {
        "asset_weights": {
            "bond": 1.00,
            "cash": 0.90,
            "bitcoin": -0.80,
            "commodity": -0.30
        },
        "factor_weights": {
            "quality": 0.90,
            "large": 0.50,
            "income": 0.70,
            "small": -0.40,
            "bitcoin": -0.80
        }
    },
    "STAGFLATION": {
        "asset_weights": {
            "commodity": 1.20,
            "alternative": 0.60,
            "cash": 0.40,
            "bond": -0.30
        },
        "factor_weights": {
            "commodity": 1.00,
            "value": 0.80,
            "income": 0.80,
            "real_estate": 0.70,
            "growth": -0.70
        }
    },
    "RISK_OFF": {
        "asset_weights": {
            "cash": 1.30,
            "bond": 1.10,
            "bitcoin": -1.00,
            "commodity": -0.30
        },
        "factor_weights": {
            "quality": 1.00,
            "large": 0.60,
            "income": 0.50,
            "momentum": -0.50,
            "small": -0.50,
            "bitcoin": -1.00
        }
    }
}

HISTORICAL_RETURN_ASSUMPTIONS = {
    "asset_class": {
        "equity": 8.00,
        "bond": 4.00,
        "cash": 2.50,
        "bitcoin": 12.00,
        "commodity": 5.00,
        "alternative": 6.00,
        "unknown": 5.00
    },
    "factor": {
        "value": 8.50,
        "growth": 8.00,
        "quality": 7.50,
        "momentum": 8.50,
        "small": 8.75,
        "large": 7.50,
        "blend": 8.00,
        "commodity": 5.00,
        "bitcoin": 12.00,
        "cash": 2.50,
        "unknown": 5.00
    }
}

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


def classify_factor(category=None, name=None):

    description = " ".join(
        value
        for value in (
            str(category or "").strip().lower(),
            str(name or "").strip().lower()
        )
        if value
    )

    if "cash" in description:
        return ["cash"]

    factors = [
        factor
        for factor, terms in FACTOR_TERMS
        if any(term in description for term in terms)
    ]

    return factors or ["unknown"]


def get_factor_exposure(positions):

    factor_values = {
        factor: 0
        for factor in FACTOR_CATEGORIES
    }
    total_value = 0

    for position in positions or []:
        try:
            ticker = str(position.get("ticker") or "").strip().upper()
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not math.isfinite(value) or value <= 0:
            continue

        total_value += value

        if ticker == "CASH0":
            factors = ["cash"]
        else:
            factors = classify_factor(
                category=position.get("category"),
                name=position.get("name")
            )

            if factors == ["unknown"] and ticker:
                security_info = get_security_info(ticker)

                if security_info:
                    factors = classify_factor(
                        category=security_info.get("category"),
                        name=security_info.get("name")
                    )

        for factor in factors:
            if factor not in factor_values:
                factor = "unknown"

            factor_values[factor] += value

    if total_value > 0:
        percentages = {
            factor: value / total_value * 100
            for factor, value in factor_values.items()
        }
    else:
        percentages = {
            factor: 0
            for factor in FACTOR_CATEGORIES
        }

    ranked_factors = sorted(
        (
            {
                "factor": factor,
                "value": factor_values[factor],
                "percentage": percentages[factor]
            }
            for factor in FACTOR_CATEGORIES
            if factor_values[factor] > 0
        ),
        key=lambda exposure: (
            -exposure["percentage"],
            FACTOR_CATEGORIES.index(exposure["factor"])
        )
    )

    if ranked_factors:
        dominant_factor = ranked_factors[0]["factor"]
        dominant_percentage = ranked_factors[0]["percentage"]
    else:
        dominant_factor = "unknown"
        dominant_percentage = 0

    non_cash_percentage = max(
        (
            percentages[factor]
            for factor in FACTOR_CATEGORIES
            if factor != "cash"
        ),
        default=0
    )

    if non_cash_percentage >= 50:
        concentration_risk = "HIGH"
    elif non_cash_percentage >= 30:
        concentration_risk = "MEDIUM"
    else:
        concentration_risk = "LOW"

    return {
        "total_value": total_value,
        "factor_values": factor_values,
        "percentages": percentages,
        "dominant_factor": dominant_factor,
        "dominant_percentage": dominant_percentage,
        "concentration_risk": concentration_risk,
        "ranked_factors": ranked_factors
    }


def get_default_regime():

    return DEFAULT_REGIME


def get_regime_analysis(factor_exposure, regime):

    normalized_regime = str(regime or "").strip().lower()

    if normalized_regime not in MARKET_REGIMES:
        normalized_regime = get_default_regime()

    regime_preferences = MARKET_REGIMES[normalized_regime]

    try:
        raw_percentages = factor_exposure.get("percentages") or {}
    except AttributeError:
        raw_percentages = {}

    percentages = {}

    for factor in FACTOR_CATEGORIES:
        try:
            percentage = float(raw_percentages.get(factor, 0) or 0)
        except (AttributeError, TypeError, ValueError):
            percentage = 0

        if not math.isfinite(percentage) or percentage < 0:
            percentage = 0

        percentages[factor] = percentage

    preferred_factors = regime_preferences["preferred_factors"]
    disfavored_factors = regime_preferences["disfavored_factors"]
    preferred_exposure = sum(
        percentages[factor]
        for factor in preferred_factors
    )
    disfavored_exposure = sum(
        percentages[factor]
        for factor in disfavored_factors
    )
    alignment_score = max(
        0,
        min(100, preferred_exposure - disfavored_exposure)
    )
    strengths = [
        {
            "factor": factor,
            "percentage": percentages[factor]
        }
        for factor in preferred_factors
        if percentages[factor] > 0
    ]
    gaps = [
        factor
        for factor in preferred_factors
        if percentages[factor] <= 0
    ]
    disfavored_exposures = [
        {
            "factor": factor,
            "percentage": percentages[factor]
        }
        for factor in disfavored_factors
        if percentages[factor] > 0
    ]

    strengths.sort(key=lambda item: -item["percentage"])
    disfavored_exposures.sort(key=lambda item: -item["percentage"])

    return {
        "regime": normalized_regime,
        "confidence": regime_preferences["confidence"],
        "alignment_score": alignment_score,
        "preferred_exposure": preferred_exposure,
        "disfavored_exposure": disfavored_exposure,
        "gaps": gaps,
        "strengths": strengths,
        "disfavored_exposures": disfavored_exposures
    }


def get_correlation_proxy(positions):

    ticker_positions = {}

    for position in positions or []:
        try:
            ticker = str(
                position.get("ticker") or "UNKNOWN"
            ).strip().upper()
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not ticker:
            ticker = "UNKNOWN"

        if not math.isfinite(value) or value <= 0:
            continue

        ticker_position = ticker_positions.setdefault(
            ticker,
            {
                "ticker": ticker,
                "value": 0,
                "category": "",
                "name": ""
            }
        )
        ticker_position["value"] += value

        category = str(position.get("category") or "").strip()
        name = str(position.get("name") or "").strip()

        if category and not ticker_position["category"]:
            ticker_position["category"] = category

        if name and not ticker_position["name"]:
            ticker_position["name"] = name

    total_value = sum(
        position["value"]
        for position in ticker_positions.values()
    )
    cluster_positions = []

    for ticker_position in ticker_positions.values():
        ticker = ticker_position["ticker"]

        if ticker == "CASH0":
            continue

        category = ticker_position["category"]
        name = ticker_position["name"]

        if not category and not name and ticker != "UNKNOWN":
            security_info = get_security_info(ticker)

            if security_info:
                category = security_info.get("category") or ""
                name = security_info.get("name") or ""

        classification = classify_security(
            ticker,
            category=category,
            name=name
        )
        factors = classify_factor(category=category, name=name)

        cluster_positions.append({
            "ticker": ticker,
            "value": ticker_position["value"],
            "asset_class": classification["asset_class"],
            "security_type": classification["security_type"],
            "factors": factors
        })

    high_groups = {}
    asset_class_groups = {}

    for position in cluster_positions:
        asset_class = position["asset_class"]
        security_type = position["security_type"]
        asset_class_groups.setdefault(asset_class, []).append(position)

        for factor in position["factors"]:
            group_key = (asset_class, security_type, factor)
            high_groups.setdefault(group_key, []).append(position)

    clusters = []

    for group_key, members in high_groups.items():
        unique_members = sorted({
            member["ticker"]
            for member in members
        })

        if len(unique_members) < 2 or total_value <= 0:
            continue

        group_value = sum(member["value"] for member in members)
        exposure = group_value / total_value * 100
        asset_class, security_type, factor = group_key
        high_threshold = (
            50
            if "unknown" in group_key
            else 40
        )

        if exposure < high_threshold:
            continue

        clusters.append({
            "severity": "HIGH",
            "group_name": " / ".join(
                part.replace("_", " ").title()
                for part in (asset_class, security_type, factor)
            ),
            "exposure": exposure,
            "members": unique_members
        })

    for asset_class, members in asset_class_groups.items():
        unique_members = sorted({
            member["ticker"]
            for member in members
        })

        if len(unique_members) < 2 or total_value <= 0:
            continue

        group_value = sum(member["value"] for member in members)
        exposure = group_value / total_value * 100

        if exposure < 30:
            continue

        clusters.append({
            "severity": "MEDIUM",
            "group_name": asset_class.replace("_", " ").title(),
            "exposure": exposure,
            "members": unique_members
        })

    severity_ranks = {
        "HIGH": 0,
        "MEDIUM": 1
    }
    clusters.sort(
        key=lambda cluster: (
            severity_ranks[cluster["severity"]],
            -cluster["exposure"],
            cluster["group_name"]
        )
    )

    if clusters:
        highest_cluster = max(
            clusters,
            key=lambda cluster: (
                cluster["exposure"],
                -severity_ranks[cluster["severity"]],
                cluster["group_name"]
            )
        )
    else:
        highest_cluster = None

    if any(cluster["severity"] == "HIGH" for cluster in clusters):
        portfolio_risk = "HIGH"
    elif any(cluster["severity"] == "MEDIUM" for cluster in clusters):
        portfolio_risk = "MEDIUM"
    else:
        portfolio_risk = "LOW"

    return {
        "total_value": total_value,
        "highest_cluster": highest_cluster,
        "portfolio_risk": portfolio_risk,
        "clusters": clusters
    }


def get_stress_test_report(positions):

    ticker_positions = {}

    for position in positions or []:
        try:
            ticker = str(
                position.get("ticker") or "UNKNOWN"
            ).strip().upper()
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not ticker:
            ticker = "UNKNOWN"

        if not math.isfinite(value) or value <= 0:
            continue

        ticker_position = ticker_positions.setdefault(
            ticker,
            {
                "ticker": ticker,
                "value": 0,
                "category": "",
                "name": ""
            }
        )
        ticker_position["value"] += value

        category = str(position.get("category") or "").strip()
        name = str(position.get("name") or "").strip()

        if category and not ticker_position["category"]:
            ticker_position["category"] = category

        if name and not ticker_position["name"]:
            ticker_position["name"] = name

    total_value = sum(
        position["value"]
        for position in ticker_positions.values()
    )
    classified_positions = []

    for ticker_position in ticker_positions.values():
        ticker = ticker_position["ticker"]
        category = ticker_position["category"]
        name = ticker_position["name"]

        if not category and not name and ticker != "UNKNOWN":
            security_info = get_security_info(ticker)

            if security_info:
                category = security_info.get("category") or ""
                name = security_info.get("name") or ""

        classification = classify_security(
            ticker,
            category=category,
            name=name
        )
        asset_class = classification.get("asset_class", "unknown")

        if asset_class not in EXPOSURE_CATEGORIES:
            asset_class = "unknown"

        classified_positions.append({
            "ticker": ticker,
            "value": ticker_position["value"],
            "asset_class": asset_class
        })

    scenarios = []

    if total_value > 0:
        for scenario_name, assumptions in STRESS_SCENARIOS.items():
            contributions = []

            for position in classified_positions:
                stressed_return = assumptions.get(
                    position["asset_class"],
                    assumptions["unknown"]
                )
                dollar_impact = position["value"] * stressed_return
                contributions.append({
                    "ticker": position["ticker"],
                    "asset_class": position["asset_class"],
                    "dollar_impact": dollar_impact
                })

            estimated_dollar_impact = sum(
                contribution["dollar_impact"]
                for contribution in contributions
            )
            portfolio_impact = (
                estimated_dollar_impact / total_value * 100
            )
            stressed_value = total_value + estimated_dollar_impact
            loss_contributors = [
                contribution
                for contribution in contributions
                if contribution["dollar_impact"] < 0
            ]
            gain_contributors = [
                contribution
                for contribution in contributions
                if contribution["dollar_impact"] > 0
            ]
            largest_loss_contributor = (
                min(
                    loss_contributors,
                    key=lambda contribution: (
                        contribution["dollar_impact"],
                        contribution["ticker"]
                    )
                )["ticker"]
                if loss_contributors
                else None
            )
            largest_gain_contributor = (
                max(
                    gain_contributors,
                    key=lambda contribution: (
                        contribution["dollar_impact"],
                        contribution["ticker"]
                    )
                )["ticker"]
                if gain_contributors
                else None
            )

            scenarios.append({
                "scenario": scenario_name,
                "stressed_value": stressed_value,
                "estimated_dollar_impact": estimated_dollar_impact,
                "portfolio_impact": portfolio_impact,
                "largest_loss_contributor": largest_loss_contributor,
                "largest_gain_contributor": largest_gain_contributor,
                "contributions": contributions
            })

    scenarios.sort(
        key=lambda scenario: (
            scenario["portfolio_impact"],
            scenario["scenario"]
        )
    )

    return {
        "total_value": total_value,
        "worst_scenario": scenarios[0] if scenarios else None,
        "scenarios": scenarios
    }


def get_macro_regime_report(positions):

    portfolio_exposure = get_portfolio_exposure(positions)
    factor_exposure = get_factor_exposure(positions)
    total_value = portfolio_exposure["total_value"]

    if total_value <= 0:
        return {
            "total_value": 0,
            "current_regime": "UNKNOWN",
            "confidence": 0,
            "alignment_level": "LOW",
            "top_signal": "No positive portfolio value",
            "top_supporting_signals": [],
            "regime_ranking": []
        }

    asset_percentages = portfolio_exposure["percentages"]
    factor_percentages = factor_exposure["percentages"]
    regime_ranking = []

    for regime, definition in MACRO_REGIME_DEFINITIONS.items():
        raw_score = 0
        supporting_signals = []

        for asset_class, weight in definition["asset_weights"].items():
            exposure = asset_percentages.get(asset_class, 0)
            contribution = exposure * weight
            raw_score += contribution

            if contribution > 0:
                supporting_signals.append({
                    "signal": (
                        f"{asset_class.replace('_', ' ').title()} "
                        f"asset exposure {exposure:.1f}%"
                    ),
                    "contribution": contribution
                })

        for factor, weight in definition["factor_weights"].items():
            exposure = factor_percentages.get(factor, 0)
            contribution = exposure * weight
            raw_score += contribution

            if contribution > 0:
                supporting_signals.append({
                    "signal": (
                        f"{factor.replace('_', ' ').title()} "
                        f"factor exposure {exposure:.1f}%"
                    ),
                    "contribution": contribution
                })

        supporting_signals.sort(
            key=lambda signal: (
                -signal["contribution"],
                signal["signal"]
            )
        )
        score = max(raw_score, 0)
        regime_ranking.append({
            "regime": regime,
            "score": score,
            "confidence": 0,
            "alignment_level": "LOW",
            "top_signal": (
                supporting_signals[0]["signal"]
                if supporting_signals
                else "No supporting signals"
            ),
            "supporting_signals": supporting_signals
        })

    total_score = sum(
        regime["score"]
        for regime in regime_ranking
    )

    for regime in regime_ranking:
        if total_score > 0:
            confidence = regime["score"] / total_score * 100
        else:
            confidence = 0

        if confidence >= 35:
            alignment_level = "HIGH"
        elif confidence >= 20:
            alignment_level = "MEDIUM"
        else:
            alignment_level = "LOW"

        regime["confidence"] = confidence
        regime["alignment_level"] = alignment_level

    regime_ranking.sort(
        key=lambda regime: (
            -regime["score"],
            regime["regime"]
        )
    )

    if total_score <= 0:
        return {
            "total_value": total_value,
            "current_regime": "UNKNOWN",
            "confidence": 0,
            "alignment_level": "LOW",
            "top_signal": "No classified macro signals",
            "top_supporting_signals": [],
            "regime_ranking": regime_ranking
        }

    current_regime = regime_ranking[0]

    return {
        "total_value": total_value,
        "current_regime": current_regime["regime"],
        "confidence": current_regime["confidence"],
        "alignment_level": current_regime["alignment_level"],
        "top_signal": current_regime["top_signal"],
        "top_supporting_signals": current_regime["supporting_signals"],
        "regime_ranking": regime_ranking
    }


def get_tax_optimization_report(positions):

    analyzed_positions = []
    total_value = 0
    total_taxable_value = 0
    total_tax_advantaged_value = 0
    total_unrealized_gains = 0
    total_unrealized_losses = 0

    for position in positions or []:
        try:
            ticker = str(
                position.get("ticker") or "UNKNOWN"
            ).strip().upper()
            account = str(position.get("account") or "").strip()
            account_type = str(
                position.get("account_type") or ""
            ).strip()
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not ticker:
            ticker = "UNKNOWN"

        if not math.isfinite(value) or value < 0:
            value = 0

        account_description = f"{account_type} {account}".strip().lower()

        if any(
            term in account_description
            for term in (
                "roth",
                "traditional ira",
                "ira",
                "401k",
                "401(k)",
                "tax deferred",
                "tax-deferred"
            )
        ):
            tax_status = "Tax Advantaged"
        elif any(
            term in account_description
            for term in ("brokerage", "taxable")
        ):
            tax_status = "Taxable"
        else:
            tax_status = "Unknown"

        raw_gain_loss = position.get("gain_loss")

        try:
            gain_loss = float(raw_gain_loss)
        except (TypeError, ValueError):
            raw_cost_basis = position.get("cost_basis")

            try:
                cost_basis = float(raw_cost_basis)
            except (TypeError, ValueError):
                cost_basis = 0

            if not math.isfinite(cost_basis) or cost_basis < 0:
                cost_basis = 0

            gain_loss = (
                value - cost_basis
                if raw_cost_basis not in (None, "")
                else 0
            )

        if not math.isfinite(gain_loss):
            gain_loss = 0

        raw_gain_loss_percent = position.get("gain_loss_percent")

        try:
            gain_loss_percent = float(raw_gain_loss_percent)
        except (TypeError, ValueError):
            try:
                cost_basis = float(position.get("cost_basis", 0) or 0)
            except (TypeError, ValueError):
                cost_basis = 0

            if math.isfinite(cost_basis) and cost_basis > 0:
                gain_loss_percent = gain_loss / cost_basis * 100
            else:
                gain_loss_percent = 0

        if not math.isfinite(gain_loss_percent):
            gain_loss_percent = 0

        if gain_loss_percent >= 20:
            gain_status = "Large Gain"
        elif gain_loss_percent > 0:
            gain_status = "Gain"
        elif gain_loss_percent <= -20:
            gain_status = "Large Loss"
        elif gain_loss_percent < 0:
            gain_status = "Loss"
        else:
            gain_status = "Neutral"

        if tax_status == "Taxable" and gain_loss < 0:
            tax_flag = "Tax Loss Harvest Candidate"
        elif tax_status == "Taxable" and gain_status == "Large Gain":
            tax_flag = "Large Taxable Gain"
        elif tax_status == "Taxable":
            tax_flag = "Taxable Position"
        elif tax_status == "Tax Advantaged":
            tax_flag = "Tax Efficient Location"
        else:
            tax_flag = "Unknown Account Status"

        if tax_status == "Taxable" and gain_status == "Large Gain":
            sort_group = 0
        elif tax_status == "Taxable" and gain_status == "Large Loss":
            sort_group = 1
        elif tax_status == "Taxable":
            sort_group = 2
        elif tax_status == "Tax Advantaged":
            sort_group = 3
        else:
            sort_group = 4

        total_value += value

        if tax_status == "Taxable":
            total_taxable_value += value
        elif tax_status == "Tax Advantaged":
            total_tax_advantaged_value += value

        if gain_loss > 0:
            total_unrealized_gains += gain_loss
        elif gain_loss < 0:
            total_unrealized_losses += abs(gain_loss)

        analyzed_positions.append({
            "ticker": ticker,
            "account": account,
            "tax_status": tax_status,
            "value": value,
            "gain_loss": gain_loss,
            "gain_loss_percent": gain_loss_percent,
            "gain_status": gain_status,
            "tax_flag": tax_flag,
            "sort_group": sort_group
        })

    taxable_gain_positions = [
        position
        for position in analyzed_positions
        if position["tax_status"] == "Taxable"
        and position["gain_loss"] > 0
    ]
    taxable_loss_positions = [
        position
        for position in analyzed_positions
        if position["tax_status"] == "Taxable"
        and position["gain_loss"] < 0
    ]
    largest_taxable_gain = (
        max(
            taxable_gain_positions,
            key=lambda position: (
                position["gain_loss"],
                position["ticker"],
                position["account"]
            )
        )
        if taxable_gain_positions
        else None
    )
    largest_taxable_loss = (
        min(
            taxable_loss_positions,
            key=lambda position: (
                position["gain_loss"],
                position["ticker"],
                position["account"]
            )
        )
        if taxable_loss_positions
        else None
    )

    analyzed_positions.sort(
        key=lambda position: (
            position["sort_group"],
            -abs(position["gain_loss"]),
            position["ticker"],
            position["account"]
        )
    )

    if total_value > 0:
        taxable_percentage = total_taxable_value / total_value * 100
        tax_advantaged_percentage = (
            total_tax_advantaged_value / total_value * 100
        )
    else:
        taxable_percentage = 0
        tax_advantaged_percentage = 0

    return {
        "total_value": total_value,
        "total_taxable_value": total_taxable_value,
        "total_tax_advantaged_value": total_tax_advantaged_value,
        "taxable_percentage": taxable_percentage,
        "tax_advantaged_percentage": tax_advantaged_percentage,
        "total_unrealized_gains": total_unrealized_gains,
        "total_unrealized_losses": total_unrealized_losses,
        "largest_taxable_gain": largest_taxable_gain,
        "largest_taxable_loss": largest_taxable_loss,
        "tax_loss_harvest_candidates_count": len(taxable_loss_positions),
        "large_taxable_gain_positions_count": len(taxable_gain_positions),
        "positions": analyzed_positions
    }


def get_historical_return_report(positions):

    ticker_positions = {}

    for position in positions or []:
        try:
            ticker = str(
                position.get("ticker") or "UNKNOWN"
            ).strip().upper()
            value = float(position.get("value", 0) or 0)
        except (AttributeError, TypeError, ValueError):
            continue

        if not ticker:
            ticker = "UNKNOWN"

        if not math.isfinite(value) or value <= 0:
            continue

        ticker_position = ticker_positions.setdefault(
            ticker,
            {
                "ticker": ticker,
                "value": 0,
                "category": "",
                "name": ""
            }
        )
        ticker_position["value"] += value

        category = str(position.get("category") or "").strip()
        name = str(position.get("name") or "").strip()

        if category and not ticker_position["category"]:
            ticker_position["category"] = category

        if name and not ticker_position["name"]:
            ticker_position["name"] = name

    total_value = sum(
        position["value"]
        for position in ticker_positions.values()
    )

    if total_value <= 0:
        return {
            "total_value": 0,
            "portfolio_implied_return": 0,
            "largest_return_contributor": None,
            "highest_return_assumption": None,
            "lowest_return_assumption": None,
            "total_positions_included": 0,
            "unknown_classification_count": 0,
            "positions": []
        }

    asset_assumptions = HISTORICAL_RETURN_ASSUMPTIONS["asset_class"]
    factor_assumptions = HISTORICAL_RETURN_ASSUMPTIONS["factor"]
    analyzed_positions = []
    unknown_classification_count = 0

    for ticker_position in ticker_positions.values():
        ticker = ticker_position["ticker"]
        category = ticker_position["category"]
        name = ticker_position["name"]

        if not category and not name and ticker != "UNKNOWN":
            security_info = get_security_info(ticker)

            if security_info:
                category = security_info.get("category") or ""
                name = security_info.get("name") or ""

        classification = classify_security(
            ticker,
            category=category,
            name=name
        )
        asset_class = classification.get("asset_class", "unknown")

        if asset_class not in asset_assumptions:
            asset_class = "unknown"

        if ticker == "CASH0":
            factors = ["cash"]
        else:
            factors = classify_factor(category=category, name=name)

        normalized_factors = [
            factor if factor in factor_assumptions else "unknown"
            for factor in factors
        ]

        if not normalized_factors:
            normalized_factors = ["unknown"]

        asset_return = asset_assumptions[asset_class]
        factor_return = sum(
            factor_assumptions[factor]
            for factor in normalized_factors
        ) / len(normalized_factors)
        blended_return = asset_return * 0.50 + factor_return * 0.50
        allocation = ticker_position["value"] / total_value * 100
        weighted_contribution = allocation / 100 * blended_return

        if asset_class == "unknown" or "unknown" in normalized_factors:
            unknown_classification_count += 1

        analyzed_positions.append({
            "ticker": ticker,
            "value": ticker_position["value"],
            "allocation": allocation,
            "asset_class": asset_class,
            "factors": normalized_factors,
            "factor": ", ".join(normalized_factors),
            "asset_class_return": asset_return,
            "factor_return": factor_return,
            "blended_return": blended_return,
            "weighted_contribution": weighted_contribution
        })

    analyzed_positions.sort(
        key=lambda position: (
            -position["weighted_contribution"],
            position["ticker"]
        )
    )
    portfolio_implied_return = sum(
        position["weighted_contribution"]
        for position in analyzed_positions
    )
    largest_return_contributor = analyzed_positions[0]
    highest_return_assumption = max(
        analyzed_positions,
        key=lambda position: (
            position["blended_return"],
            position["ticker"]
        )
    )
    lowest_return_assumption = min(
        analyzed_positions,
        key=lambda position: (
            position["blended_return"],
            position["ticker"]
        )
    )

    return {
        "total_value": total_value,
        "portfolio_implied_return": portfolio_implied_return,
        "largest_return_contributor": largest_return_contributor,
        "highest_return_assumption": highest_return_assumption,
        "lowest_return_assumption": lowest_return_assumption,
        "total_positions_included": len(analyzed_positions),
        "unknown_classification_count": unknown_classification_count,
        "positions": analyzed_positions
    }


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
