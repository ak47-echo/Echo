import csv
import json
import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "02_Data"
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_CURRENT_HOLDINGS_PATH = (
    DATA_DIR / "portfolio_current" / "holdings_normalized.csv"
)
DEFAULT_SNAPSHOT_DIR = DATA_DIR / "portfolio_archive" / "normalized"
DEFAULT_REPORT_JSON_PATH = REPORTS_DIR / "portfolio_change_detection.json"
DEFAULT_REPORT_TEXT_PATH = REPORTS_DIR / "portfolio_change_detection.txt"
SNAPSHOT_KEEP_COUNT = 20


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _timestamp():

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _clean_text(value):

    return " ".join(str(value or "").strip().split())


def _parse_number(value):

    text = _clean_text(value)

    if not text or text == "--":
        return 0.0

    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace("$", "").replace(",", "")

    if text.endswith("%"):
        text = text[:-1]

    number = float(text)
    return -number if negative else number


def _normalize_account(value):

    return _clean_text(value)


def _normalize_ticker(value):

    ticker = _clean_text(value).upper()
    cash_terms = {
        "CASH",
        "CASH0",
        "CASH & CASH INVESTMENTS",
        "MONEY MARKET",
        "SWEEP",
        "CORE CASH"
    }

    if ticker in cash_terms:
        return "CASH0"

    return ticker


def _is_cash(ticker):

    return _normalize_ticker(ticker) == "CASH0"


def _base_report():

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "has_previous_snapshot": False,
        "summary": {
            "change_count": 0,
            "material_change_count": 0,
            "total_market_value_previous": 0.0,
            "total_market_value_current": 0.0,
            "total_market_value_change": 0.0,
            "top_change": None
        },
        "new_positions": [],
        "removed_positions": [],
        "quantity_changes": [],
        "market_value_changes": [],
        "concentration_changes": [],
        "cash_changes": [],
        "warnings": []
    }


def _read_holdings(path):

    holdings = {}
    warnings = []
    path = Path(path) if path else None

    if not path or not path.exists():
        return holdings, warnings

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            required = {"account", "ticker", "quantity", "market_value"}
            missing = required - set(reader.fieldnames or [])

            if missing:
                warnings.append(
                    f"{path}: missing required columns: "
                    f"{', '.join(sorted(missing))}"
                )
                return holdings, warnings

            for line_number, row in enumerate(reader, start=2):
                account = _normalize_account(row.get("account"))
                ticker = _normalize_ticker(row.get("ticker"))

                if not account or not ticker:
                    warnings.append(
                        f"{path} line {line_number}: missing account or ticker."
                    )
                    continue

                try:
                    quantity = _parse_number(row.get("quantity"))
                    market_value = _parse_number(row.get("market_value"))
                except (TypeError, ValueError):
                    warnings.append(
                        f"{path} line {line_number}: invalid numeric value."
                    )
                    continue

                key = (account.casefold(), ticker)

                if key not in holdings:
                    holdings[key] = {
                        "account": account,
                        "ticker": ticker,
                        "quantity": 0.0,
                        "market_value": 0.0,
                        "security_name": _clean_text(row.get("security_name"))
                    }

                holdings[key]["quantity"] += quantity
                holdings[key]["market_value"] += market_value
    except (OSError, csv.Error, UnicodeDecodeError) as error:
        warnings.append(f"{path}: could not read normalized holdings: {error}")

    return holdings, warnings


def _total_market_value(holdings):

    return round(sum(item["market_value"] for item in holdings.values()), 2)


def _weight(position, total):

    if total <= 0:
        return 0.0

    return (position["market_value"] / total) * 100


def _percent_change(previous, current):

    if abs(previous) <= 0.000001:
        return None

    return ((current - previous) / abs(previous)) * 100


def _material_market_value_change(delta, total_current):

    return abs(delta) > 100 or (
        total_current > 0 and abs(delta) > total_current * 0.01
    )


def _mark(change, material, reason):

    change["material"] = bool(material)
    change["material_reason"] = reason if material else ""
    return change


def _top_change(changes):

    material = [change for change in changes if change.get("material")]
    candidates = material or changes

    if not candidates:
        return None

    def score(change):
        return max(
            abs(float(change.get("delta_market_value") or 0)),
            abs(float(change.get("delta_weight") or 0)) * 1000,
            abs(float(change.get("delta_quantity") or 0)) * 100
        )

    return sorted(candidates, key=score, reverse=True)[0]


def build_portfolio_change_report(previous_holdings_path, current_holdings_path):

    report = _base_report()
    previous, previous_warnings = _read_holdings(previous_holdings_path)
    current, current_warnings = _read_holdings(current_holdings_path)
    report["warnings"].extend(previous_warnings)
    report["warnings"].extend(current_warnings)
    report["has_previous_snapshot"] = bool(
        previous_holdings_path and Path(previous_holdings_path).exists()
    )

    previous_total = _total_market_value(previous)
    current_total = _total_market_value(current)
    previous_keys = set(previous)
    current_keys = set(current)

    for key in sorted(current_keys - previous_keys):
        position = current[key]

        if _is_cash(position["ticker"]):
            continue

        if abs(position["market_value"]) <= 0.000001:
            continue

        report["new_positions"].append(_mark(
            {
                "account": position["account"],
                "ticker": position["ticker"],
                "current_quantity": position["quantity"],
                "current_market_value": position["market_value"],
                "current_weight": _weight(position, current_total)
            },
            True,
            "New non-cash position."
        ))

    for key in sorted(previous_keys - current_keys):
        position = previous[key]

        if _is_cash(position["ticker"]):
            continue

        report["removed_positions"].append(_mark(
            {
                "account": position["account"],
                "ticker": position["ticker"],
                "previous_quantity": position["quantity"],
                "previous_market_value": position["market_value"],
                "previous_weight": _weight(position, previous_total)
            },
            True,
            "Removed non-cash position."
        ))

    for key in sorted(previous_keys & current_keys):
        old = previous[key]
        new = current[key]
        cash = _is_cash(new["ticker"])
        delta_quantity = new["quantity"] - old["quantity"]
        delta_market_value = new["market_value"] - old["market_value"]
        old_weight = _weight(old, previous_total)
        new_weight = _weight(new, current_total)
        delta_weight = new_weight - old_weight

        if abs(delta_quantity) > 0.000001:
            report["quantity_changes"].append(_mark(
                {
                    "account": new["account"],
                    "ticker": new["ticker"],
                    "previous_quantity": old["quantity"],
                    "current_quantity": new["quantity"],
                    "delta_quantity": delta_quantity
                },
                not cash,
                "Quantity changed in non-cash position."
            ))

        if abs(delta_market_value) > 0.01:
            report["market_value_changes"].append(_mark(
                {
                    "account": new["account"],
                    "ticker": new["ticker"],
                    "previous_market_value": old["market_value"],
                    "current_market_value": new["market_value"],
                    "delta_market_value": delta_market_value,
                    "percent_change": _percent_change(
                        old["market_value"],
                        new["market_value"]
                    )
                },
                _material_market_value_change(delta_market_value, current_total),
                "Market value changed by more than threshold."
            ))

        if abs(delta_weight) > 0.000001:
            report["concentration_changes"].append(_mark(
                {
                    "account": new["account"],
                    "ticker": new["ticker"],
                    "previous_weight": old_weight,
                    "current_weight": new_weight,
                    "delta_weight": delta_weight
                },
                abs(delta_weight) >= 1,
                "Concentration changed by at least 1 percentage point."
            ))

    previous_cash = 0.0
    current_cash = 0.0

    for key in sorted(previous_keys | current_keys):
        old = previous.get(key)
        new = current.get(key)
        ticker = (new or old or {}).get("ticker")

        if not _is_cash(ticker):
            continue

        old_value = old["market_value"] if old else 0.0
        new_value = new["market_value"] if new else 0.0
        delta_cash = new_value - old_value
        previous_cash += old_value
        current_cash += new_value

        if abs(delta_cash) > 0.01:
            account = (new or old)["account"]
            report["cash_changes"].append(_mark(
                {
                    "account": account,
                    "ticker": "CASH0",
                    "previous_cash": old_value,
                    "current_cash": new_value,
                    "delta_cash": delta_cash
                },
                abs(delta_cash) > 100,
                "Account cash changed by more than $100."
            ))

    total_cash_delta = current_cash - previous_cash

    if abs(total_cash_delta) > 0.01:
        report["cash_changes"].append(_mark(
            {
                "account": "TOTAL",
                "ticker": "CASH0",
                "previous_cash": previous_cash,
                "current_cash": current_cash,
                "delta_cash": total_cash_delta
            },
            abs(total_cash_delta) > 100,
            "Total cash changed by more than $100."
        ))

    all_changes = (
        report["new_positions"]
        + report["removed_positions"]
        + report["quantity_changes"]
        + report["market_value_changes"]
        + report["concentration_changes"]
        + report["cash_changes"]
    )
    material_count = sum(1 for change in all_changes if change.get("material"))
    report["summary"] = {
        "change_count": len(all_changes),
        "material_change_count": material_count,
        "total_market_value_previous": previous_total,
        "total_market_value_current": current_total,
        "total_market_value_change": current_total - previous_total,
        "top_change": _top_change(all_changes)
    }

    return report


def render_portfolio_change_report_text(report):

    summary = report.get("summary") or {}
    lines = [
        "PORTFOLIO CHANGE DETECTION",
        "",
        f"Schema Version: {report.get('schema_version') or 'unknown'}",
        f"Generated At: {report.get('generated_at') or 'unknown'}",
        (
            "Has Previous Snapshot: "
            f"{'Yes' if report.get('has_previous_snapshot') else 'No'}"
        ),
        f"Change Count: {summary.get('change_count') or 0}",
        f"Material Change Count: {summary.get('material_change_count') or 0}",
        "Previous Total Market Value: "
        f"${float(summary.get('total_market_value_previous') or 0):.2f}",
        "Current Total Market Value: "
        f"${float(summary.get('total_market_value_current') or 0):.2f}",
        "Total Market Value Change: "
        f"${float(summary.get('total_market_value_change') or 0):+.2f}",
        "",
        "What changed since the last portfolio snapshot?"
    ]
    top_change = summary.get("top_change")
    lines.append(
        json.dumps(top_change, sort_keys=True)
        if top_change else
        "No holdings-level changes detected."
    )

    sections = (
        ("What positions are new?", "new_positions"),
        ("What positions were removed?", "removed_positions"),
        ("Which positions changed size?", "quantity_changes"),
        ("Which market values changed?", "market_value_changes"),
        ("How did concentration change?", "concentration_changes"),
        ("Did cash change?", "cash_changes")
    )

    for title, key in sections:
        lines.extend(["", title])
        values = report.get(key) or []
        lines.extend(
            [json.dumps(item, sort_keys=True) for item in values[:30]]
            or ["None"]
        )

    lines.extend(["", "Warnings"])
    lines.extend(report.get("warnings") or ["None"])

    return "\n".join(lines) + "\n"


def write_portfolio_change_report_json(report, path=None):

    path = Path(path or DEFAULT_REPORT_JSON_PATH)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8"
        )
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}

    return {"success": True, "path": str(path), "error": ""}


def write_portfolio_change_report_text(report, path=None):

    path = Path(path or DEFAULT_REPORT_TEXT_PATH)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_portfolio_change_report_text(report), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}

    return {"success": True, "path": str(path), "error": ""}


def read_portfolio_change_report(path=None):

    path = Path(path or DEFAULT_REPORT_JSON_PATH)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return _base_report()

    return data if isinstance(data, dict) else _base_report()


def cleanup_old_normalized_snapshots(snapshot_dir=None, keep_count=None):

    snapshot_dir = Path(snapshot_dir or DEFAULT_SNAPSHOT_DIR)
    keep_count = SNAPSHOT_KEEP_COUNT if keep_count is None else int(keep_count)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshots = sorted(
        [path for path in snapshot_dir.glob("*.csv") if path.is_file()],
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True
    )
    deleted = []

    for path in snapshots[keep_count:]:
        try:
            path.unlink()
            deleted.append(str(path))
        except OSError:
            pass

    return deleted


def archive_normalized_snapshot(current_path=None, snapshot_dir=None):

    current_path = Path(current_path or DEFAULT_CURRENT_HOLDINGS_PATH)

    if not current_path.exists():
        return None

    snapshot_dir = Path(snapshot_dir or DEFAULT_SNAPSHOT_DIR)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / f"{_timestamp()}_holdings_normalized.csv"
    suffix = 1

    while snapshot_path.exists():
        snapshot_path = snapshot_dir / (
            f"{_timestamp()}_{suffix}_holdings_normalized.csv"
        )
        suffix += 1

    shutil.copy2(current_path, snapshot_path)
    cleanup_old_normalized_snapshots(snapshot_dir)
    return snapshot_path


def build_and_write_portfolio_change_report(previous_holdings_path=None,
                                            current_holdings_path=None):

    report = build_portfolio_change_report(
        previous_holdings_path,
        current_holdings_path or DEFAULT_CURRENT_HOLDINGS_PATH
    )
    json_result = write_portfolio_change_report_json(report)
    text_result = write_portfolio_change_report_text(report)

    return {
        "report": report,
        "json_result": json_result,
        "text_result": text_result
    }
