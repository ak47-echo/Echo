import csv
import io
import math
import urllib.request
import zipfile
from datetime import date, timedelta

try:
    import requests
except ImportError:
    requests = None


FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

MACRO_SERIES = (
    {"series_id": "CPIAUCSL", "name": "Consumer Price Index", "required": True},
    {"series_id": "UNRATE", "name": "Unemployment Rate", "required": True},
    {
        "series_id": "FEDFUNDS",
        "name": "Effective Federal Funds Rate",
        "required": True
    },
    {"series_id": "DGS10", "name": "10-Year Treasury Yield", "required": True},
    {"series_id": "DGS2", "name": "2-Year Treasury Yield", "required": True},
    {
        "series_id": "T10Y2Y",
        "name": "10Y Minus 2Y Treasury Spread",
        "required": True
    },
    {"series_id": "GDP", "name": "Gross Domestic Product", "required": True},
    {
        "series_id": "DCOILWTICO",
        "name": "WTI Crude Oil Price",
        "required": True
    },
    {
        "series_id": "DEXUSEU",
        "name": "U.S. Dollar to Euro Exchange Rate",
        "required": False
    }
)

REGIME_ORDER = (
    "EXPANSION",
    "DISINFLATION",
    "INFLATION_SHOCK",
    "RECESSION_RISK",
    "STAGFLATION_RISK",
    "RISK_OFF"
)

MACRO_PRIORITY_REGIME_ORDER = (
    "Inflation Stress",
    "Disinflation / Soft Landing",
    "Growth Slowdown",
    "Recession Risk",
    "Liquidity Stress",
    "Rate Shock",
    "Credit Stress",
    "Energy Shock",
    "Geopolitical Macro Shock",
    "Neutral / Mixed"
)

MACRO_REGIME_BASE_WEIGHTS = {
    "Inflation Stress": 72,
    "Disinflation / Soft Landing": 45,
    "Growth Slowdown": 58,
    "Recession Risk": 82,
    "Liquidity Stress": 86,
    "Rate Shock": 80,
    "Credit Stress": 84,
    "Energy Shock": 78,
    "Geopolitical Macro Shock": 76,
    "Neutral / Mixed": 20
}

SEVERITY_MODIFIERS = {
    "HIGH": 12,
    "MEDIUM": 6,
    "LOW": 0
}

MARKET_IMPACT_MODIFIERS = {
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 1
}

PORTFOLIO_RELEVANCE_MODIFIERS = {
    "HIGH": 8,
    "MEDIUM": 4,
    "LOW": 1
}

DIRECTIONAL_CLARITY_MODIFIERS = {
    "HIGH": 5,
    "MEDIUM": 3,
    "LOW": 0
}


def _network_timeout(timeout):

    try:
        return max(0.1, min(float(timeout), 10.0))
    except (TypeError, ValueError):
        return 10.0


def _safe_error(error):

    text = " ".join(str(error).split())
    return text[:180] if text else "Unknown error"


def _parse_fred_csv(content, series_id):

    if isinstance(content, bytes):
        content = content.decode("utf-8-sig", errors="replace")

    observations = []
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        raise ValueError("FRED response has no CSV header")

    date_field = next(
        (
            field for field in reader.fieldnames
            if field and field.lower() in {"observation_date", "date"}
        ),
        None
    )
    value_field = next(
        (
            field for field in reader.fieldnames
            if field and field.upper() == series_id.upper()
        ),
        None
    )

    if date_field is None or value_field is None:
        raise ValueError("FRED response is missing expected columns")

    for row in reader:
        raw_value = (row.get(value_field) or "").strip()
        raw_date = (row.get(date_field) or "").strip()

        if raw_value in {"", ".", "NA", "N/A"} or not raw_date:
            continue

        try:
            observation_date = date.fromisoformat(raw_date)
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if math.isfinite(value):
            observations.append({
                "date": observation_date,
                "value": value
            })

    observations.sort(key=lambda observation: observation["date"])

    if not observations:
        raise ValueError("FRED response has no valid observations")

    return observations


def _default_fetcher(series, timeout=10):

    timeout = _network_timeout(timeout)
    url = FRED_CSV_URL.format(series_id=series["series_id"])
    headers = {
        "Accept": "text/csv,*/*;q=0.8"
    }

    if requests is not None:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content

    request = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _default_batch_fetcher(series, timeout=10):

    timeout = _network_timeout(timeout)
    series_ids = ",".join(item["series_id"] for item in series)
    url = FRED_CSV_URL.format(series_id=series_ids)
    headers = {"Accept": "text/csv,application/zip,*/*;q=0.8"}

    if requests is not None:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _batch_csv_documents(content):

    if zipfile.is_zipfile(io.BytesIO(content)):
        documents = []

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".csv"):
                    documents.append(archive.read(name))

        if not documents:
            raise ValueError("FRED batch response has no CSV documents")

        return documents

    return [content]


def _normalize_batch_series(series, content):

    documents = _batch_csv_documents(content)

    for document in documents:
        try:
            observations = _parse_fred_csv(
                document,
                series["series_id"]
            )
            return _normalize_series(series, observations)
        except ValueError:
            continue

    return _failed_series(
        series,
        "FRED batch response is missing valid series observations"
    )


def _subtract_years(value, years):

    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(
            year=value.year - years,
            month=2,
            day=28
        )


def _observation_at_or_before(observations, target_date):

    for observation in reversed(observations):
        if observation["date"] <= target_date:
            return observation

    return None


def _percent_change(latest_value, prior_value):

    if prior_value in (None, 0):
        return None

    change = ((latest_value / prior_value) - 1.0) * 100.0
    return change if math.isfinite(change) else None


def _normalize_series(series, observations):

    latest = observations[-1]
    previous = observations[-2] if len(observations) >= 2 else None
    three_month_prior = _observation_at_or_before(
        observations,
        latest["date"] - timedelta(days=90)
    )
    twelve_month_prior = _observation_at_or_before(
        observations,
        _subtract_years(latest["date"], 1)
    )

    return {
        "series_id": series["series_id"],
        "name": series["name"],
        "required": series["required"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "previous_value": (
            previous["value"] if previous is not None else None
        ),
        "change": (
            latest["value"] - previous["value"]
            if previous is not None
            else None
        ),
        "three_month_change": (
            _percent_change(
                latest["value"],
                three_month_prior["value"]
            )
            if three_month_prior is not None
            else None
        ),
        "twelve_month_change": (
            _percent_change(
                latest["value"],
                twelve_month_prior["value"]
            )
            if twelve_month_prior is not None
            else None
        ),
        "observations": observations,
        "status": "OK",
        "error": ""
    }


def _failed_series(series, error):

    return {
        "series_id": series["series_id"],
        "name": series["name"],
        "required": series["required"],
        "latest_value": None,
        "latest_date": None,
        "previous_value": None,
        "change": None,
        "three_month_change": None,
        "twelve_month_change": None,
        "observations": [],
        "status": "FAILED",
        "error": _safe_error(error)
    }


def _fetch_and_normalize(series, fetcher, timeout):

    try:
        content = fetcher(series, timeout)
        observations = _parse_fred_csv(content, series["series_id"])
        return _normalize_series(series, observations)
    except Exception as error:
        return _failed_series(series, error)


def collect_macro_data(series=None, fetcher=None, timeout=10):

    series = tuple(series if series is not None else MACRO_SERIES)

    if not series:
        return []

    if fetcher is None:
        try:
            content = _default_batch_fetcher(series, timeout)
        except Exception as error:
            return [
                _failed_series(definition, error)
                for definition in series
            ]

        return [
            _normalize_batch_series(definition, content)
            for definition in series
        ]

    return [
        _fetch_and_normalize(
            definition,
            fetcher,
            timeout
        )
        for definition in series
    ]


def _year_over_year_values(series):

    if not series or series["status"] != "OK":
        return None, None

    observations = series["observations"]

    if len(observations) < 2:
        return None, None

    latest = observations[-1]
    previous = observations[-2]
    latest_base = _observation_at_or_before(
        observations,
        _subtract_years(latest["date"], 1)
    )
    previous_base = _observation_at_or_before(
        observations,
        _subtract_years(previous["date"], 1)
    )

    if latest_base is None or previous_base is None:
        return None, None

    return (
        _percent_change(latest["value"], latest_base["value"]),
        _percent_change(previous["value"], previous_base["value"])
    )


def classify_inflation(cpi_series):

    latest_yoy, prior_yoy = _year_over_year_values(cpi_series)

    if latest_yoy is None or prior_yoy is None:
        return "UNKNOWN", "Insufficient CPI history for year-over-year trend."

    difference = latest_yoy - prior_yoy

    if difference >= 0.20:
        status = "RISING"
    elif difference <= -0.20:
        status = "FALLING"
    else:
        status = "STABLE"

    detail = (
        f"CPI YoY {latest_yoy:.2f}% versus prior YoY "
        f"{prior_yoy:.2f}% ({difference:+.2f} pp)."
    )
    return status, detail


def classify_labor(unemployment_series):

    if not unemployment_series or unemployment_series["status"] != "OK":
        return "UNKNOWN", "Unemployment rate unavailable."

    value = unemployment_series["latest_value"]

    if value < 4.5:
        status = "STRONG"
    elif value >= 5.5:
        status = "WEAK"
    else:
        status = "NEUTRAL"

    return status, f"Unemployment rate {value:.2f}%."


def classify_policy_rate(fed_funds_series):

    if not fed_funds_series or fed_funds_series["status"] != "OK":
        return "UNKNOWN", "Effective federal funds rate unavailable."

    value = fed_funds_series["latest_value"]

    if value >= 4.0:
        status = "RESTRICTIVE"
    elif value <= 2.0:
        status = "ACCOMMODATIVE"
    else:
        status = "NEUTRAL"

    return status, f"Effective federal funds rate {value:.2f}%."


def classify_yield_curve(spread_series, ten_year_series=None,
                         two_year_series=None):

    spread = None
    source = ""

    if spread_series and spread_series["status"] == "OK":
        spread = spread_series["latest_value"]
        source = "T10Y2Y"
    elif (
        ten_year_series
        and two_year_series
        and ten_year_series["status"] == "OK"
        and two_year_series["status"] == "OK"
    ):
        spread = (
            ten_year_series["latest_value"]
            - two_year_series["latest_value"]
        )
        source = "DGS10 minus DGS2"

    if spread is None:
        return "UNKNOWN", "Treasury yield spread unavailable."

    if spread < 0:
        status = "INVERTED"
    elif spread >= 1.0:
        status = "STEEP"
    else:
        status = "FLAT"

    return status, f"{source} spread {spread:.2f} percentage points."


def classify_growth(gdp_series):

    latest_yoy, _ = _year_over_year_values(gdp_series)

    if latest_yoy is None:
        return "UNKNOWN", "Insufficient GDP history for year-over-year growth."

    if latest_yoy > 2.0:
        status = "EXPANDING"
    elif latest_yoy < 1.0:
        status = "SLOWING"
    else:
        status = "MODERATE"

    return status, f"Nominal GDP YoY growth {latest_yoy:.2f}%."


def classify_energy(oil_series):

    if not oil_series or oil_series["status"] != "OK":
        return "UNKNOWN", "WTI crude oil data unavailable."

    change = oil_series["three_month_change"]

    if change is None:
        return "UNKNOWN", "Insufficient WTI history for 3-month change."

    if change > 10.0:
        status = "RISING"
    elif change < -10.0:
        status = "FALLING"
    else:
        status = "STABLE"

    return status, f"WTI 3-month change {change:+.2f}%."


def score_macro_regimes(indicators):

    inflation = indicators["inflation"]["status"]
    labor = indicators["labor"]["status"]
    policy = indicators["policy_rate"]["status"]
    yield_curve = indicators["yield_curve"]["status"]
    growth = indicators["growth"]["status"]
    energy = indicators["energy"]["status"]
    scores = {regime: 0 for regime in REGIME_ORDER}

    if labor == "STRONG":
        scores["EXPANSION"] += 2
    if growth == "EXPANDING":
        scores["EXPANSION"] += 2
    if yield_curve in {"STEEP", "FLAT"}:
        scores["EXPANSION"] += 1
    if inflation in {"STABLE", "FALLING"}:
        scores["EXPANSION"] += 1

    if inflation == "FALLING":
        scores["DISINFLATION"] += 3
    if labor in {"NEUTRAL", "STRONG"}:
        scores["DISINFLATION"] += 1
    if policy == "RESTRICTIVE":
        scores["DISINFLATION"] += 1
    if energy in {"FALLING", "STABLE"}:
        scores["DISINFLATION"] += 1

    if inflation == "RISING":
        scores["INFLATION_SHOCK"] += 3
    if energy == "RISING":
        scores["INFLATION_SHOCK"] += 2
    if policy == "RESTRICTIVE":
        scores["INFLATION_SHOCK"] += 1

    if yield_curve == "INVERTED":
        scores["RECESSION_RISK"] += 3
    if labor == "WEAK":
        scores["RECESSION_RISK"] += 2
    if growth == "SLOWING":
        scores["RECESSION_RISK"] += 2
    if policy == "RESTRICTIVE":
        scores["RECESSION_RISK"] += 1

    if inflation == "RISING":
        scores["STAGFLATION_RISK"] += 2
    if labor == "WEAK":
        scores["STAGFLATION_RISK"] += 2
    if growth == "SLOWING":
        scores["STAGFLATION_RISK"] += 2
    if energy == "RISING":
        scores["STAGFLATION_RISK"] += 1

    if yield_curve == "INVERTED":
        scores["RISK_OFF"] += 2
    if labor == "WEAK":
        scores["RISK_OFF"] += 2
    if energy == "RISING":
        scores["RISK_OFF"] += 1
    if growth == "SLOWING":
        scores["RISK_OFF"] += 2

    top_score = max(scores.values(), default=0)
    regime = (
        next(name for name in REGIME_ORDER if scores[name] == top_score)
        if top_score > 0
        else "UNKNOWN"
    )

    if top_score >= 6:
        confidence = "HIGH"
    elif top_score >= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return regime, confidence, scores


def _point_change(series, days=90):

    if not series or series["status"] != "OK":
        return None

    latest_date = series["latest_date"]

    if latest_date is None:
        return None

    prior = _observation_at_or_before(
        series["observations"],
        latest_date - timedelta(days=days)
    )

    if prior is None:
        return None

    return series["latest_value"] - prior["value"]


def _priority_tier(score):

    if score >= 85:
        return "HIGH"

    if score >= 60:
        return "MEDIUM"

    return "LOW"


def _macro_priority_signal(label, status, detail, regime, severity,
                           market_impact, portfolio_relevance,
                           directional_clarity, reason):

    score = min(
        100,
        MACRO_REGIME_BASE_WEIGHTS[regime]
        + SEVERITY_MODIFIERS[severity]
        + MARKET_IMPACT_MODIFIERS[market_impact]
        + PORTFOLIO_RELEVANCE_MODIFIERS[portfolio_relevance]
        + DIRECTIONAL_CLARITY_MODIFIERS[directional_clarity]
    )

    return {
        "label": label,
        "status": status,
        "detail": detail,
        "macro_regime": regime,
        "regime_score": score,
        "priority_tier": _priority_tier(score),
        "severity": severity,
        "market_impact": market_impact,
        "portfolio_relevance": portfolio_relevance,
        "directional_clarity": directional_clarity,
        "ranking_reason": reason
    }


def build_macro_priority_signals(indicators, series_by_id):

    inflation = indicators["inflation"]
    labor = indicators["labor"]
    policy = indicators["policy_rate"]
    yield_curve = indicators["yield_curve"]
    growth = indicators["growth"]
    energy = indicators["energy"]
    fed_funds_change = _point_change(series_by_id.get("FEDFUNDS"))
    ten_year_change = _point_change(series_by_id.get("DGS10"))
    two_year_change = _point_change(series_by_id.get("DGS2"))
    signals = []

    if inflation["status"] == "RISING":
        signals.append(_macro_priority_signal(
            "Inflation Trend",
            inflation["status"],
            inflation["detail"],
            "Inflation Stress",
            "HIGH",
            "HIGH",
            "HIGH",
            "HIGH",
            (
                "Rising inflation can reprice Fed expectations, broad "
                "equities, long-duration growth assets, and drawdown risk."
            )
        ))
    elif inflation["status"] == "FALLING":
        signals.append(_macro_priority_signal(
            "Inflation Trend",
            inflation["status"],
            inflation["detail"],
            "Disinflation / Soft Landing",
            "MEDIUM",
            "MEDIUM",
            "MEDIUM",
            "HIGH",
            (
                "Falling inflation supports a soft-landing backdrop and "
                "reduces pressure on rates-sensitive assets."
            )
        ))
    else:
        signals.append(_macro_priority_signal(
            "Inflation Trend",
            inflation["status"],
            inflation["detail"],
            "Neutral / Mixed",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "MEDIUM",
            "Inflation does not show a clear market-moving directional shock."
        ))

    if labor["status"] == "WEAK":
        signals.append(_macro_priority_signal(
            "Labor Market",
            labor["status"],
            labor["detail"],
            "Recession Risk",
            "HIGH",
            "HIGH",
            "HIGH",
            "HIGH",
            (
                "Labor weakness raises recession risk and broad portfolio "
                "drawdown risk."
            )
        ))
    elif labor["status"] == "STRONG":
        signals.append(_macro_priority_signal(
            "Labor Market",
            labor["status"],
            labor["detail"],
            "Disinflation / Soft Landing",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "HIGH",
            (
                "A strong labor market supports growth unless it conflicts "
                "with inflation or rate stress."
            )
        ))
    else:
        signals.append(_macro_priority_signal(
            "Labor Market",
            labor["status"],
            labor["detail"],
            "Neutral / Mixed",
            "LOW",
            "LOW",
            "LOW",
            "MEDIUM",
            "Labor data is not signaling a major market regime shift."
        ))

    policy_rate_shock = (
        fed_funds_change is not None
        and abs(fed_funds_change) >= 0.25
    )
    policy_severity = "HIGH" if policy_rate_shock else "MEDIUM"
    policy_reason = (
        "Policy-rate movement can directly affect broad equities, "
        "long-duration growth assets, Bitcoin proxies, and rates-sensitive "
        "holdings."
    )

    if policy["status"] == "RESTRICTIVE" or policy_rate_shock:
        signals.append(_macro_priority_signal(
            "Policy Rate",
            policy["status"],
            policy["detail"],
            "Rate Shock",
            policy_severity,
            "HIGH",
            "HIGH",
            "HIGH" if policy_rate_shock else "MEDIUM",
            policy_reason
        ))
    elif policy["status"] == "ACCOMMODATIVE":
        signals.append(_macro_priority_signal(
            "Policy Rate",
            policy["status"],
            policy["detail"],
            "Disinflation / Soft Landing",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "MEDIUM",
            "Accommodative policy can support risk assets and liquidity."
        ))
    else:
        signals.append(_macro_priority_signal(
            "Policy Rate",
            policy["status"],
            policy["detail"],
            "Neutral / Mixed",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "LOW",
            "Policy rate is not showing a clear shock signal."
        ))

    rate_move_shock = any(
        change is not None and abs(change) >= 0.50
        for change in (ten_year_change, two_year_change)
    )

    if rate_move_shock:
        yield_regime = "Rate Shock"
        yield_severity = "HIGH"
        yield_reason = (
            "Large Treasury-yield moves reprice discount rates, "
            "growth assets, Bitcoin proxies, and rates-sensitive holdings."
        )
    elif yield_curve["status"] == "INVERTED":
        yield_regime = "Recession Risk"
        yield_severity = "HIGH"
        yield_reason = (
            "An inverted yield curve is a higher-priority recession and "
            "drawdown-risk signal than routine macro data."
        )
    elif yield_curve["status"] == "FLAT":
        yield_regime = "Growth Slowdown"
        yield_severity = "MEDIUM"
        yield_reason = (
            "A flat curve can indicate slower growth expectations and "
            "less favorable risk appetite."
        )
    else:
        yield_regime = "Neutral / Mixed"
        yield_severity = "LOW"
        yield_reason = "Yield curve does not show acute stress."

    signals.append(_macro_priority_signal(
        "Yield Curve",
        yield_curve["status"],
        yield_curve["detail"],
        yield_regime,
        yield_severity,
        "HIGH" if yield_regime in {"Rate Shock", "Recession Risk"} else "MEDIUM",
        "HIGH" if yield_regime in {"Rate Shock", "Recession Risk"} else "MEDIUM",
        "HIGH" if yield_regime in {"Rate Shock", "Recession Risk"} else "MEDIUM",
        yield_reason
    ))

    if growth["status"] == "SLOWING":
        signals.append(_macro_priority_signal(
            "Growth",
            growth["status"],
            growth["detail"],
            "Growth Slowdown",
            "MEDIUM",
            "MEDIUM",
            "HIGH",
            "HIGH",
            (
                "Slowing growth affects earnings expectations and broad "
                "portfolio drawdown risk."
            )
        ))
    elif growth["status"] == "EXPANDING":
        signals.append(_macro_priority_signal(
            "Growth",
            growth["status"],
            growth["detail"],
            "Disinflation / Soft Landing",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "HIGH",
            "Expanding growth supports a constructive macro backdrop."
        ))
    else:
        signals.append(_macro_priority_signal(
            "Growth",
            growth["status"],
            growth["detail"],
            "Neutral / Mixed",
            "LOW",
            "LOW",
            "LOW",
            "MEDIUM",
            "Growth data is not showing a high-priority macro risk."
        ))

    if energy["status"] == "RISING":
        signals.append(_macro_priority_signal(
            "Energy",
            energy["status"],
            energy["detail"],
            "Energy Shock",
            "HIGH",
            "HIGH",
            "HIGH",
            "HIGH",
            (
                "Rising energy can pressure inflation, margins, energy "
                "holdings, and broad market risk appetite."
            )
        ))
    elif energy["status"] == "FALLING":
        signals.append(_macro_priority_signal(
            "Energy",
            energy["status"],
            energy["detail"],
            "Disinflation / Soft Landing",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "HIGH",
            "Falling energy prices can reduce inflation pressure."
        ))
    else:
        signals.append(_macro_priority_signal(
            "Energy",
            energy["status"],
            energy["detail"],
            "Neutral / Mixed",
            "LOW",
            "LOW",
            "MEDIUM",
            "MEDIUM",
            "Energy data does not show a disruption or shock."
        ))

    return sorted(
        signals,
        key=lambda signal: (
            -signal["regime_score"],
            MACRO_PRIORITY_REGIME_ORDER.index(signal["macro_regime"]),
            signal["label"]
        )
    )


def analyze_macro_data(series_results):

    by_id = {
        series["series_id"]: series
        for series in series_results
    }
    indicator_values = {
        "inflation": classify_inflation(by_id.get("CPIAUCSL")),
        "labor": classify_labor(by_id.get("UNRATE")),
        "policy_rate": classify_policy_rate(by_id.get("FEDFUNDS")),
        "yield_curve": classify_yield_curve(
            by_id.get("T10Y2Y"),
            by_id.get("DGS10"),
            by_id.get("DGS2")
        ),
        "growth": classify_growth(by_id.get("GDP")),
        "energy": classify_energy(by_id.get("DCOILWTICO"))
    }
    indicators = {
        name: {"status": value[0], "detail": value[1]}
        for name, value in indicator_values.items()
    }
    legacy_regime, legacy_confidence, regime_scores = score_macro_regimes(
        indicators
    )
    macro_priority_signals = build_macro_priority_signals(indicators, by_id)
    top_priority = (
        macro_priority_signals[0]
        if macro_priority_signals
        else {
            "label": "Macro Regime",
            "status": "UNKNOWN",
            "detail": "No macro priority signals available.",
            "macro_regime": "Neutral / Mixed",
            "regime_score": 0,
            "priority_tier": "LOW",
            "ranking_reason": "No classified macro signals were available."
        }
    )
    confidence = top_priority["priority_tier"]
    required = [
        series for series in series_results
        if series["required"]
    ]
    successful_required = sum(
        series["status"] == "OK"
        for series in required
    )

    if successful_required >= 5:
        agent_status = "ACTIVE"
    elif successful_required >= 1:
        agent_status = "DEGRADED"
    else:
        agent_status = "OFFLINE"

    return {
        "status": agent_status,
        "regime": top_priority["macro_regime"],
        "confidence": confidence,
        "top_priority": top_priority,
        "macro_priority_signals": macro_priority_signals,
        "legacy_regime": legacy_regime,
        "legacy_confidence": legacy_confidence,
        "indicators": indicators,
        "regime_scores": regime_scores,
        "failed_series_count": sum(
            series["status"] == "FAILED"
            for series in series_results
        ),
        "successful_required_count": successful_required,
        "series_results": series_results
    }


def _format_value(value):

    if value is None:
        return "N/A"

    return f"{value:.4f}".rstrip("0").rstrip(".")


def build_macro_report(macro_data):

    indicators = macro_data["indicators"]
    top_priority = macro_data["top_priority"]
    executive_brief = [
        f"Macro Agent Status: {macro_data['status']}",
        f"Current Macro Regime: {macro_data['regime']}",
        (
            f"Top Macro Priority: {top_priority['label']} | "
            f"Macro Regime {top_priority['macro_regime']} | "
            f"Regime Score {top_priority['regime_score']} | "
            f"Priority Tier {top_priority['priority_tier']}"
        ),
        f"Top Macro Reason: {top_priority['ranking_reason']}",
        f"Confidence: {macro_data['confidence']}",
        f"Inflation Trend: {indicators['inflation']['status']}",
        f"Labor Market: {indicators['labor']['status']}",
        f"Policy Rate: {indicators['policy_rate']['status']}",
        f"Yield Curve: {indicators['yield_curve']['status']}",
        f"Growth: {indicators['growth']['status']}",
        f"Energy: {indicators['energy']['status']}",
        f"Failed Series: {macro_data['failed_series_count']}",
        "",
        (
            "Macro Agent is observational only and does not generate "
            "investment recommendations."
        )
    ]
    full_report = ["Series Health:"]

    if macro_data["series_results"]:
        for series in macro_data["series_results"]:
            latest_date = (
                series["latest_date"].isoformat()
                if series["latest_date"] is not None
                else "N/A"
            )
            full_report.append(
                f"{series['series_id']} | Name {series['name']} | "
                f"Status {series['status']} | Latest {latest_date} "
                f"{_format_value(series['latest_value'])} | "
                f"Error {series['error'] or 'None'}"
            )
    else:
        full_report.append("No macro data sources connected.")

    full_report.extend(["", "Ranked Macro Priority Signals:"])

    for rank, signal in enumerate(macro_data["macro_priority_signals"], start=1):
        full_report.extend([
            f"{rank}. {signal['label']}: {signal['status']}",
            f"   Macro Regime: {signal['macro_regime']}",
            f"   Regime Score: {signal['regime_score']}",
            f"   Priority Tier: {signal['priority_tier']}",
            f"   Reason: {signal['ranking_reason']}",
            f"   Detail: {signal['detail']}",
            (
                "   Components: "
                f"Severity {signal['severity']} | "
                f"Market Impact {signal['market_impact']} | "
                f"Portfolio Relevance {signal['portfolio_relevance']} | "
                f"Directional Clarity {signal['directional_clarity']}"
            )
        ])

    full_report.extend(["", "Macro Indicators:"])

    for label, key in (
        ("Inflation Trend", "inflation"),
        ("Labor Market", "labor"),
        ("Policy Rate", "policy_rate"),
        ("Yield Curve", "yield_curve"),
        ("Growth", "growth"),
        ("Energy", "energy")
    ):
        indicator = indicators[key]
        full_report.append(
            f"{label}: {indicator['status']} | "
            f"Detail {indicator['detail']}"
        )

    full_report.extend(["", "Regime Scores:"])
    sorted_scores = sorted(
        macro_data["regime_scores"].items(),
        key=lambda item: (-item[1], REGIME_ORDER.index(item[0]))
    )

    for regime, score in sorted_scores:
        full_report.append(f"{regime} | Score {score}")

    full_report.extend([
        "",
        "Legacy Aggregate Regime:",
        (
            f"{macro_data['legacy_regime']} | "
            f"Confidence {macro_data['legacy_confidence']}"
        )
    ])

    full_report.extend([
        "",
        "Data Notes:",
        "- Macro data may lag.",
        "- FRED series have different publication frequencies.",
        "- This report is observational only."
    ])

    return {
        "executive_brief": executive_brief,
        "full_report": full_report,
        "data": macro_data
    }


def get_macro_report(series=None, fetcher=None, timeout=10):

    return build_macro_report(
        analyze_macro_data(
            collect_macro_data(
                series=series,
                fetcher=fetcher,
                timeout=timeout
            )
        )
    )
