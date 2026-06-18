import json
import os
import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "02_Data"
REPORTS_DIR = BASE_DIR / "04_Reports"
DEFAULT_IMPORT_DIR = DATA_DIR / "portfolio_imports"
DEFAULT_JSON_PATH = REPORTS_DIR / "portfolio_auto_import.json"
DEFAULT_TEXT_PATH = REPORTS_DIR / "portfolio_auto_import.txt"


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _enabled(value):

    return _safe_text(value).casefold() in {"1", "true", "yes", "on"}


def _base(status="disabled"):

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "status": status,
        "enabled": False,
        "downloads_dir": None,
        "import_dir": str(DEFAULT_IMPORT_DIR),
        "pattern": None,
        "source_file": None,
        "copied_path": None,
        "already_imported": False,
        "warnings": []
    }


def _same_file_content(left, right):

    try:
        if Path(left).stat().st_size != Path(right).stat().st_size:
            return False
        return Path(left).read_bytes() == Path(right).read_bytes()
    except OSError:
        return False


def run_portfolio_auto_import(downloads_dir=None, import_dir=None,
                              pattern=None, enabled=None):

    env_enabled = _enabled(os.getenv("PORTFOLIO_AUTO_IMPORT_ENABLED"))
    enabled = env_enabled if enabled is None else bool(enabled)
    result = _base("disabled")
    result["enabled"] = enabled
    result["downloads_dir"] = _safe_text(
        downloads_dir or os.getenv("PORTFOLIO_DOWNLOADS_DIR")
    )
    result["pattern"] = _safe_text(
        pattern or os.getenv("PORTFOLIO_IMPORT_PATTERN")
        or "All-Accounts-Positions-*.csv"
    )
    import_dir = Path(import_dir or DEFAULT_IMPORT_DIR)
    result["import_dir"] = str(import_dir)

    if not enabled:
        result["warnings"].append("Portfolio auto import is disabled.")
        return result

    if not result["downloads_dir"]:
        result["status"] = "error"
        result["warnings"].append("PORTFOLIO_DOWNLOADS_DIR is not configured.")
        return result

    downloads_path = Path(result["downloads_dir"])
    if not downloads_path.exists():
        result["status"] = "error"
        result["warnings"].append("Downloads directory does not exist.")
        return result

    matches = [
        path for path in downloads_path.glob(result["pattern"])
        if path.is_file()
    ]
    matches = sorted(matches, key=lambda path: path.stat().st_mtime, reverse=True)

    if not matches:
        result["status"] = "no_match"
        result["warnings"].append("No matching portfolio export was found.")
        return result

    source = matches[0]
    target = import_dir / source.name
    result["source_file"] = str(source)
    import_dir.mkdir(parents=True, exist_ok=True)

    if target.exists() and _same_file_content(target, source):
        result["status"] = "already_imported"
        result["copied_path"] = str(target)
        result["already_imported"] = True
        return result

    if target.exists():
        stem = target.stem
        suffix = target.suffix
        target = import_dir / f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"

    try:
        shutil.copy2(source, target)
    except OSError as error:
        result["status"] = "error"
        result["warnings"].append(str(error))
        return result

    result["status"] = "copied"
    result["copied_path"] = str(target)
    return result


def render_portfolio_auto_import_text(result):

    lines = [
        "PORTFOLIO AUTO IMPORT",
        "",
        f"Status: {result.get('status')}",
        f"Enabled: {result.get('enabled')}",
        f"Downloads Dir: {result.get('downloads_dir') or 'None'}",
        f"Pattern: {result.get('pattern') or 'None'}",
        f"Source File: {result.get('source_file') or 'None'}",
        f"Copied Path: {result.get('copied_path') or 'None'}",
        f"Already Imported: {result.get('already_imported')}",
        "",
        "Warnings"
    ]
    lines.extend(result.get("warnings") or ["None"])
    return "\n".join(lines) + "\n"


def write_portfolio_auto_import_json(result, path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def write_portfolio_auto_import_text(result, path=None):

    path = Path(path or DEFAULT_TEXT_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_portfolio_auto_import_text(result), encoding="utf-8")
    except OSError as error:
        return {"success": False, "path": str(path), "error": str(error)}
    return {"success": True, "path": str(path), "error": ""}


def read_portfolio_auto_import(path=None):

    path = Path(path or DEFAULT_JSON_PATH)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return _base("disabled")
    return value if isinstance(value, dict) else _base("disabled")


def run_and_write_portfolio_auto_import(**kwargs):

    result = run_portfolio_auto_import(**kwargs)
    write_portfolio_auto_import_json(result)
    write_portfolio_auto_import_text(result)
    return result
