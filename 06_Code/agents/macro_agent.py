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
    regime, confidence, regime_scores = score_macro_regimes(indicators)
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
        "regime": regime,
        "confidence": confidence,
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
    executive_brief = [
        f"Macro Agent Status: {macro_data['status']}",
        f"Current Macro Regime: {macro_data['regime']}",
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
