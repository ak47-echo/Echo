import csv
import json
import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "02_Data"
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_IMPORT_DIR = DATA_DIR / "portfolio_imports"
DEFAULT_ARCHIVE_DIR = DATA_DIR / "portfolio_archive"
DEFAULT_OUTPUT_PATH = DATA_DIR / "portfolio_current" / "holdings_normalized.csv"
DEFAULT_REPORT_JSON_PATH = REPORTS_DIR / "portfolio_ingestion.json"
DEFAULT_REPORT_TEXT_PATH = REPORTS_DIR / "portfolio_ingestion.txt"

NORMALIZED_COLUMNS = (
    "account",
    "ticker",
    "quantity",
    "cost_basis",
    "market_value",
    "security_name",
    "source_file",
    "imported_at"
)

COLUMN_ALIASES = {
    "account": (
        "account",
        "account_name",
        "account type",
        "accounttype",
        "acct",
        "registration"
    ),
    "ticker": (
        "ticker",
        "symbol",
        "security",
        "security_symbol",
        "security symbol",
        "cusip_ticker"
    ),
    "quantity": (
        "quantity",
        "qty",
        "shares",
        "units",
        "position_quantity"
    ),
    "cost_basis": (
        "cost_basis",
        "cost basis",
        "total_cost",
        "total cost",
        "cost",
        "basis"
    ),
    "market_value": (
        "market_value",
        "market value",
        "value",
        "current_value",
        "current value",
        "position_value"
    ),
    "security_name": (
        "security_name",
        "security name",
        "name",
        "description",
        "security_description"
    )
}


def _now_iso():

    return datetime.now().replace(microsecond=0).isoformat()


def _base_result(status="no_imports"):

    return {
        "schema_version": "1.0",
        "generated_at": _now_iso(),
        "status": status,
        "source_file": None,
        "rows_read": 0,
        "rows_normalized": 0,
        "rows_skipped": 0,
        "warnings": [],
        "output_path": str(DEFAULT_OUTPUT_PATH),
        "archive_path": None,
        "position_count": 0,
        "total_market_value": 0.0,
        "top_positions": [],
        "changes": {
            "new_positions": [],
            "removed_positions": [],
            "quantity_changes": [],
            "market_value_changes": [],
            "total_market_value_change": 0.0
        }
    }


def _canonical_header(value):

    return " ".join(str(value or "").strip().casefold().split())


def _alias_lookup(fieldnames):

    available = {
        _canonical_header(fieldname): fieldname
        for fieldname in (fieldnames or [])
    }
    lookup = {}

    for normalized, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = _canonical_header(alias)

            if key in available:
                lookup[normalized] = available[key]
                break

    return lookup


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


def _row_value(row, lookup, normalized_column):

    source_column = lookup.get(normalized_column)

    if not source_column:
        return ""

    return row.get(source_column, "")


def _read_normalized_positions(path):

    positions = {}
    path = Path(path)

    if not path.exists():
        return positions

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                account = _clean_text(row.get("account"))
                ticker = _normalize_ticker(row.get("ticker"))

                if not account or not ticker:
                    continue

                try:
                    quantity = _parse_number(row.get("quantity"))
                    market_value = _parse_number(row.get("market_value"))
                except (TypeError, ValueError):
                    continue

                positions[(account, ticker)] = {
                    "account": account,
                    "ticker": ticker,
                    "quantity": quantity,
                    "market_value": market_value
                }
    except (OSError, csv.Error, UnicodeDecodeError):
        return {}

    return positions


def _compare_positions(previous, current):

    previous_keys = set(previous)
    current_keys = set(current)
    quantity_changes = []
    market_value_changes = []

    for key in sorted(previous_keys & current_keys):
        old = previous[key]
        new = current[key]

        if abs(new["quantity"] - old["quantity"]) > 0.000001:
            quantity_changes.append({
                "account": new["account"],
                "ticker": new["ticker"],
                "previous_quantity": old["quantity"],
                "current_quantity": new["quantity"],
                "change": new["quantity"] - old["quantity"]
            })

        if abs(new["market_value"] - old["market_value"]) > 0.01:
            market_value_changes.append({
                "account": new["account"],
                "ticker": new["ticker"],
                "previous_market_value": old["market_value"],
                "current_market_value": new["market_value"],
                "change": new["market_value"] - old["market_value"]
            })

    previous_total = sum(item["market_value"] for item in previous.values())
    current_total = sum(item["market_value"] for item in current.values())

    return {
        "new_positions": [
            current[key]
            for key in sorted(current_keys - previous_keys)
        ],
        "removed_positions": [
            previous[key]
            for key in sorted(previous_keys - current_keys)
        ],
        "quantity_changes": quantity_changes,
        "market_value_changes": market_value_changes,
        "total_market_value_change": current_total - previous_total
    }


def _latest_csv(import_dir):

    files = [
        path for path in Path(import_dir).glob("*.csv")
        if path.is_file()
    ]

    if not files:
        return None

    return max(files, key=lambda path: (path.stat().st_mtime, path.name))


def _archive_source(source_file, archive_dir, imported_at):

    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = imported_at.replace(":", "").replace("-", "").replace("T", "_")
    archive_path = archive_dir / f"{timestamp}_{Path(source_file).name}"
    shutil.copy2(source_file, archive_path)

    archives = sorted(
        [path for path in archive_dir.glob("*.csv") if path.is_file()],
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True
    )

    for old_archive in archives[20:]:
        try:
            old_archive.unlink()
        except OSError:
            pass

    return archive_path


def _write_normalized(rows, output_path):

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=NORMALIZED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _blank_row(row):

    return not any(_clean_text(cell) for cell in row)


def _cell(row, index):

    if index < 0 or index >= len(row):
        return ""

    return row[index]


def _header_index(row, *names):

    wanted = {_canonical_header(name) for name in names}

    for index, value in enumerate(row):
        if _canonical_header(value) in wanted:
            return index

    return None


def _is_schwab_header(row):

    return _header_index(row, "Symbol") is not None


def _is_schwab_sectioned_rows(rows):

    for index, row in enumerate(rows[:-1]):
        first_cell = _clean_text(_cell(row, 0))

        if first_cell and _is_schwab_header(rows[index + 1]):
            return True

    return False


def _add_aggregate_position(aggregate, row):

    key = (row["account"], row["ticker"])

    if key not in aggregate:
        aggregate[key] = {
            "account": row["account"],
            "ticker": row["ticker"],
            "quantity": 0.0,
            "cost_basis": 0.0,
            "market_value": 0.0,
            "security_name": row["security_name"],
            "source_file": row["source_file"],
            "imported_at": row["imported_at"]
        }

    aggregate[key]["quantity"] += row["quantity"]
    aggregate[key]["cost_basis"] += row["cost_basis"]
    aggregate[key]["market_value"] += row["market_value"]

    if not aggregate[key]["security_name"] and row["security_name"]:
        aggregate[key]["security_name"] = row["security_name"]


def _formatted_normalized_rows(aggregate):

    return [
        {
            **row,
            "quantity": f"{row['quantity']:.8f}".rstrip("0").rstrip("."),
            "cost_basis": f"{row['cost_basis']:.2f}",
            "market_value": f"{row['market_value']:.2f}"
        }
        for row in sorted(
            aggregate.values(),
            key=lambda item: (item["account"], item["ticker"])
        )
    ]


def _parse_schwab_sectioned_rows(rows, source_file, imported_at, result):

    aggregate = {}
    account = ""
    header = None
    symbol_index = None
    description_index = None
    quantity_index = None
    market_value_index = None
    cost_basis_index = None
    index = 0

    while index < len(rows):
        row = rows[index]

        if _blank_row(row):
            index += 1
            continue

        first_cell = _clean_text(_cell(row, 0))

        if first_cell and index + 1 < len(rows) and _is_schwab_header(
            rows[index + 1]
        ):
            account = first_cell
            header = rows[index + 1]
            symbol_index = _header_index(header, "Symbol")
            description_index = _header_index(header, "Description")
            quantity_index = _header_index(header, "Qty (Quantity)")
            market_value_index = _header_index(
                header,
                "Mkt Val (Market Value)"
            )
            cost_basis_index = _header_index(header, "Cost Basis")
            index += 2
            continue

        if header is None or _is_schwab_header(row):
            index += 1
            continue

        symbol_text = _clean_text(_cell(row, symbol_index))

        if not symbol_text:
            index += 1
            continue

        if symbol_text.casefold() == "positions total":
            index += 1
            continue

        result["rows_read"] += 1
        ticker = _normalize_ticker(symbol_text)
        security_name = _clean_text(_cell(row, description_index))

        if ticker == "CASH0" and (
            not security_name or security_name == "--"
        ):
            security_name = "Cash & Cash Investments"

        try:
            market_value = _parse_number(_cell(row, market_value_index))
            cost_basis = _parse_number(_cell(row, cost_basis_index))
            quantity = _parse_number(_cell(row, quantity_index))
        except (TypeError, ValueError):
            result["rows_skipped"] += 1
            result["warnings"].append(
                f"{source_file.name} line {index + 1}: invalid numeric value."
            )
            index += 1
            continue

        if ticker == "CASH0" and quantity == 0 and market_value > 0:
            quantity = market_value

        _add_aggregate_position(
            aggregate,
            {
                "account": account,
                "ticker": ticker,
                "quantity": quantity,
                "cost_basis": cost_basis,
                "market_value": market_value,
                "security_name": security_name,
                "source_file": source_file.name,
                "imported_at": imported_at
            }
        )
        index += 1

    return _formatted_normalized_rows(aggregate)


def ingest_latest_portfolio_import(import_dir, output_path, archive_dir):

    import_dir = Path(import_dir)
    output_path = Path(output_path)
    archive_dir = Path(archive_dir)
    result = _base_result()
    result["output_path"] = str(output_path)

    try:
        import_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        result["status"] = "error"
        result["warnings"].append(f"Directory setup failed: {error}")
        return result

    source_file = _latest_csv(import_dir)

    if source_file is None:
        if not output_path.exists():
            try:
                _write_normalized([], output_path)
            except OSError as error:
                result["status"] = "error"
                result["warnings"].append(
                    f"Empty normalized output setup failed: {error}"
                )
        return result

    imported_at = result["generated_at"]
    previous_positions = _read_normalized_positions(output_path)
    result["source_file"] = str(source_file)

    try:
        archive_path = _archive_source(source_file, archive_dir, imported_at)
        result["archive_path"] = str(archive_path)
    except OSError as error:
        result["warnings"].append(
            f"{source_file.name}: source archive failed: {error}"
        )

    try:
        with source_file.open("r", newline="", encoding="utf-8-sig") as file:
            raw_rows = list(csv.reader(file))

        if _is_schwab_sectioned_rows(raw_rows):
            rows = _parse_schwab_sectioned_rows(
                raw_rows,
                source_file,
                imported_at,
                result
            )
            _write_normalized(rows, output_path)
        else:
            with source_file.open("r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    result["warnings"].append(
                        f"{source_file.name}: Empty CSV or missing header."
                    )
                    result["status"] = "partial"
                    return result

                lookup = _alias_lookup(reader.fieldnames)

                if "ticker" not in lookup:
                    result["warnings"].append(
                        f"{source_file.name}: Missing ticker/symbol column."
                    )
                    result["status"] = "error"
                    return result

                aggregate = {}

                for line_number, row in enumerate(reader, start=2):
                    result["rows_read"] += 1
                    ticker = _normalize_ticker(_row_value(row, lookup, "ticker"))

                    if not ticker:
                        result["rows_skipped"] += 1
                        result["warnings"].append(
                            f"{source_file.name} line {line_number}: missing ticker."
                        )
                        continue

                    try:
                        quantity = _parse_number(
                            _row_value(row, lookup, "quantity")
                        )
                        cost_basis = _parse_number(
                            _row_value(row, lookup, "cost_basis")
                        )
                        market_value = _parse_number(
                            _row_value(row, lookup, "market_value")
                        )
                    except (TypeError, ValueError):
                        result["rows_skipped"] += 1
                        result["warnings"].append(
                            f"{source_file.name} line {line_number}: invalid numeric value."
                        )
                        continue

                    account = _clean_text(_row_value(row, lookup, "account"))
                    security_name = _clean_text(
                        _row_value(row, lookup, "security_name")
                    )
                    _add_aggregate_position(
                        aggregate,
                        {
                            "account": account,
                            "ticker": ticker,
                            "quantity": quantity,
                            "cost_basis": cost_basis,
                            "market_value": market_value,
                            "security_name": security_name,
                            "source_file": source_file.name,
                            "imported_at": imported_at
                        }
                    )

                rows = _formatted_normalized_rows(aggregate)
                _write_normalized(rows, output_path)
    except (OSError, csv.Error, UnicodeDecodeError) as error:
        result["status"] = "error"
        result["warnings"].append(
            f"{source_file.name}: CSV ingestion failed: {error}"
        )
        return result

    current_positions = _read_normalized_positions(output_path)
    result["rows_normalized"] = len(rows)
    result["position_count"] = len(rows)
    result["total_market_value"] = round(
        sum(item["market_value"] for item in current_positions.values()),
        2
    )
    result["top_positions"] = sorted(
        current_positions.values(),
        key=lambda item: item["market_value"],
        reverse=True
    )[:10]
    result["changes"] = _compare_positions(previous_positions, current_positions)
    result["status"] = "partial" if result["warnings"] else "success"

    return result


def render_portfolio_ingestion_text(ingestion):

    lines = [
        "PORTFOLIO INGESTION",
        "",
        f"Status: {ingestion.get('status')}",
        f"Generated At: {ingestion.get('generated_at')}",
        f"Source File: {ingestion.get('source_file') or 'None'}",
        f"Output Path: {ingestion.get('output_path') or 'None'}",
        f"Archive Path: {ingestion.get('archive_path') or 'None'}",
        f"Rows Read: {ingestion.get('rows_read') or 0}",
        f"Rows Normalized: {ingestion.get('rows_normalized') or 0}",
        f"Rows Skipped: {ingestion.get('rows_skipped') or 0}",
        f"Position Count: {ingestion.get('position_count') or 0}",
        "Total Market Value: "
        f"${float(ingestion.get('total_market_value') or 0):.2f}",
        ""
    ]
    changes = ingestion.get("changes") or {}
    lines.extend([
        "CHANGE DETECTION",
        "",
        f"New Positions: {len(changes.get('new_positions') or [])}",
        f"Removed Positions: {len(changes.get('removed_positions') or [])}",
        f"Quantity Changes: {len(changes.get('quantity_changes') or [])}",
        "Market Value Changes: "
        f"{len(changes.get('market_value_changes') or [])}",
        "Total Market Value Change: "
        f"${float(changes.get('total_market_value_change') or 0):+.2f}",
        ""
    ])

    for label, key in (
        ("New Positions", "new_positions"),
        ("Removed Positions", "removed_positions"),
        ("Quantity Changes", "quantity_changes"),
        ("Market Value Changes", "market_value_changes")
    ):
        values = changes.get(key) or []
        lines.append(label)
        lines.extend(
            [
                json.dumps(item, sort_keys=True)
                for item in values[:20]
            ] or ["None"]
        )
        lines.append("")

    lines.append("Warnings")
    lines.extend(ingestion.get("warnings") or ["None"])

    return "\n".join(lines)


def write_portfolio_ingestion_json(ingestion, path=None):

    path = Path(path or DEFAULT_REPORT_JSON_PATH)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(ingestion, indent=2, sort_keys=True),
            encoding="utf-8"
        )
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}

    return {"success": True, "path": str(path), "error": ""}


def write_portfolio_ingestion_text(ingestion, path=None):

    path = Path(path or DEFAULT_REPORT_TEXT_PATH)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_portfolio_ingestion_text(ingestion), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}

    return {"success": True, "path": str(path), "error": ""}


def read_portfolio_ingestion(path=None):

    path = Path(path or DEFAULT_REPORT_JSON_PATH)

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _base_result("no_imports")


def ingest_default_portfolio_import():

    return ingest_latest_portfolio_import(
        DEFAULT_IMPORT_DIR,
        DEFAULT_OUTPUT_PATH,
        DEFAULT_ARCHIVE_DIR
    )
