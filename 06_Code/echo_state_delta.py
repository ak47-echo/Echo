from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
STATE_JSON_PATH = REPORTS_DIR / "echo_state.json"
STATE_DELTA_JSON_PATH = REPORTS_DIR / "echo_state_delta.json"
STATE_DELTA_TEXT_PATH = REPORTS_DIR / "echo_state_delta.txt"
STATE_ARCHIVE_DIR = REPORTS_DIR / "archive" / "state"
STATE_SNAPSHOT_KEEP_COUNT = 10


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _get_path(data, path):

    value = data if isinstance(data, dict) else {}

    for part in path:
        if not isinstance(value, dict):
            return None

        value = value.get(part)

    return value


def _field_value(data, path):

    value = _get_path(data, path)

    if isinstance(value, dict):
        for key in ("title", "theme_title", "name"):
            if value.get(key):
                return _safe_text(value.get(key))

        return None

    return _safe_text(value) or None


def _change(change_type, field, previous, current, material=False,
            reason=""):

    return {
        "change_type": change_type,
        "field": field,
        "previous": previous,
        "current": current,
        "material": bool(material),
        "reason": reason
    }


def _append_field_change(changes, field, previous_state, current_state,
                         path, material=False, reason=""):

    previous = _field_value(previous_state, path)
    current = _field_value(current_state, path)

    if previous == current:
        return None

    change = _change(
        "changed",
        field,
        previous,
        current,
        material,
        reason
    )
    changes.append(change)

    return change


def _risk_key(risk):

    if not isinstance(risk, dict):
        return _safe_text(risk).casefold()

    return "|".join(
        _safe_text(risk.get(key)).casefold()
        for key in ("source", "title")
    )


def _risk_title(risk):

    if isinstance(risk, dict):
        return _safe_text(risk.get("title")) or "Untitled risk"

    return _safe_text(risk) or "Untitled risk"


def _is_high_priority_risk(risk):

    if not isinstance(risk, dict):
        return False

    return _safe_text(risk.get("severity")).upper() in {"HIGH", "CRITICAL"}


def _indexed(items, key_function):

    indexed = {}

    for item in items or []:
        key = key_function(item)

        if key:
            indexed[key] = item

    return indexed


def _new_and_resolved(previous_items, current_items, key_function):

    previous = _indexed(previous_items, key_function)
    current = _indexed(current_items, key_function)
    new_keys = [key for key in current if key not in previous]
    resolved_keys = [key for key in previous if key not in current]

    return (
        [current[key] for key in new_keys],
        [previous[key] for key in resolved_keys]
    )


def _conflict_key(conflict):

    if isinstance(conflict, dict):
        return _safe_text(conflict.get("conflict_title")).casefold()

    return _safe_text(conflict).casefold()


def _action_key(action):

    return _safe_text(action).casefold()


def _risk_change_items(risks):

    return [
        {
            "source": risk.get("source"),
            "severity": risk.get("severity"),
            "title": risk.get("title"),
            "reason": risk.get("reason")
        }
        for risk in risks
        if isinstance(risk, dict)
    ]


def _action_is_material(action, new_risks):

    action_text = _safe_text(action).casefold()

    if not action_text:
        return False

    for risk in new_risks:
        title = _safe_text(risk.get("title")).casefold()

        if title and title in action_text:
            return True

    return any(
        action_text.startswith(prefix)
        for prefix in ("review ", "reevaluate ", "investigate ")
    )


def build_echo_state_delta(previous_state, current_state):

    previous_state = previous_state if isinstance(previous_state, dict) else None
    current_state = current_state if isinstance(current_state, dict) else {}
    has_previous = previous_state is not None
    changes = []
    priority_change = None
    theme_change = None
    macro_regime_change = None
    portfolio_risk_change = None
    stress_scenario_change = None
    news_narrative_change = None

    if has_previous:
        priority_change = _append_field_change(
            changes,
            "top_priority",
            previous_state,
            current_state,
            ("top_priority", "title"),
            True,
            "Top priority changed."
        )
        theme_change = _append_field_change(
            changes,
            "dominant_theme",
            previous_state,
            current_state,
            ("dominant_theme", "theme_title"),
            True,
            "Dominant theme changed."
        )
        portfolio_risk_change = _append_field_change(
            changes,
            "portfolio.current_risk",
            previous_state,
            current_state,
            ("portfolio", "current_risk", "title"),
            True,
            "Portfolio current risk changed."
        )
        stress_scenario_change = _append_field_change(
            changes,
            "portfolio.worst_stress_scenario",
            previous_state,
            current_state,
            ("portfolio", "worst_stress_scenario", "title")
        )
        macro_regime_change = _append_field_change(
            changes,
            "macro.regime",
            previous_state,
            current_state,
            ("macro", "regime", "name"),
            True,
            "Macro regime changed."
        )
        news_narrative_change = _append_field_change(
            changes,
            "news.top_narrative",
            previous_state,
            current_state,
            ("news", "top_narrative", "title")
        )

    previous_risks = (
        previous_state.get("risk_register", [])
        if has_previous
        else []
    )
    current_risks = current_state.get("risk_register", [])
    new_risks, resolved_risks = _new_and_resolved(
        previous_risks,
        current_risks,
        _risk_key
    )
    high_new_risks = [risk for risk in new_risks if _is_high_priority_risk(risk)]
    high_resolved_risks = [
        risk for risk in resolved_risks
        if _is_high_priority_risk(risk)
    ]

    if has_previous:
        for risk in high_new_risks:
            changes.append(_change(
                "added",
                "risk_register",
                None,
                _risk_title(risk),
                True,
                "New high-priority risk appeared."
            ))

        for risk in high_resolved_risks:
            changes.append(_change(
                "removed",
                "risk_register",
                _risk_title(risk),
                None,
                True,
                "Prior high-priority risk disappeared."
            ))

        new_conflicts, resolved_conflicts = _new_and_resolved(
            previous_state.get("conflicts", []),
            current_state.get("conflicts", []),
            _conflict_key
        )

        for conflict in new_conflicts:
            changes.append(_change(
                "added",
                "conflicts",
                None,
                (
                    conflict.get("conflict_title")
                    if isinstance(conflict, dict)
                    else _safe_text(conflict)
                ),
                False,
                "New conflict detected."
            ))

        for conflict in resolved_conflicts:
            changes.append(_change(
                "removed",
                "conflicts",
                (
                    conflict.get("conflict_title")
                    if isinstance(conflict, dict)
                    else _safe_text(conflict)
                ),
                None,
                False,
                "Prior conflict no longer present."
            ))

        new_actions, resolved_actions = _new_and_resolved(
            previous_state.get("action_queue", []),
            current_state.get("action_queue", []),
            _action_key
        )

        for action in new_actions:
            material = _action_is_material(action, high_new_risks)
            changes.append(_change(
                "added",
                "action_queue",
                None,
                _safe_text(action),
                material,
                (
                    "Action queue gained a new high-priority action."
                    if material
                    else "Action queue gained a new action."
                )
            ))

        for action in resolved_actions:
            changes.append(_change(
                "removed",
                "action_queue",
                _safe_text(action),
                None,
                False,
                "Action queue item no longer present."
            ))

    material_changes = [change for change in changes if change["material"]]
    top_change = material_changes[0] if material_changes else (
        changes[0] if changes else None
    )

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "has_previous_state": has_previous,
        "summary": {
            "change_count": len(changes),
            "material_change_count": len(material_changes),
            "top_change": top_change
        },
        "changes": changes,
        "material_changes": material_changes,
        "new_risks": _risk_change_items(new_risks if has_previous else []),
        "resolved_risks": _risk_change_items(
            resolved_risks if has_previous else []
        ),
        "priority_change": priority_change,
        "theme_change": theme_change,
        "macro_regime_change": macro_regime_change,
        "portfolio_risk_change": portfolio_risk_change,
        "stress_scenario_change": stress_scenario_change,
        "news_narrative_change": news_narrative_change
    }


def load_previous_state(path=None):

    path = Path(path) if path else STATE_JSON_PATH

    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None

    return state if isinstance(state, dict) else None


def _snapshot_name(state):

    generated_at = _safe_text(
        state.get("generated_at") if isinstance(state, dict) else ""
    )

    if not generated_at:
        generated_at = _now()

    safe = re.sub(r"[^0-9A-Za-z_-]+", "_", generated_at).strip("_")

    return f"echo_state_{safe}.json"


def _cleanup_state_snapshots(archive_dir=None, keep_count=None):

    archive_dir = Path(archive_dir) if archive_dir else STATE_ARCHIVE_DIR
    keep_count = (
        STATE_SNAPSHOT_KEEP_COUNT
        if keep_count is None
        else max(int(keep_count), 0)
    )

    try:
        snapshots = sorted(
            archive_dir.glob("echo_state_*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )
    except OSError:
        return

    for snapshot in snapshots[keep_count:]:
        try:
            snapshot.unlink()
        except OSError:
            pass


def save_state_snapshot(state, archive_dir=None):

    if not isinstance(state, dict):
        return {
            "success": False,
            "path": "",
            "error": "No previous state available to snapshot."
        }

    archive_dir = Path(archive_dir) if archive_dir else STATE_ARCHIVE_DIR

    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        path = archive_dir / _snapshot_name(state)

        if path.exists():
            path = archive_dir / (
                f"{path.stem}_{datetime.now().strftime('%H%M%S%f')}.json"
            )

        path.write_text(
            json.dumps(state, indent=2, sort_keys=True),
            encoding="utf-8"
        )
        _cleanup_state_snapshots(archive_dir)
    except (OSError, TypeError, ValueError) as error:
        return {
            "success": False,
            "path": str(archive_dir),
            "error": _safe_text(error)[:180]
        }

    return {
        "success": True,
        "path": str(path),
        "error": ""
    }


def render_state_delta_text(delta):

    delta = delta if isinstance(delta, dict) else {}
    summary = delta.get("summary") or {}
    material_count = int(summary.get("material_change_count") or 0)
    top_change = summary.get("top_change")
    lines = [
        "ECHO STATE DELTA",
        "================",
        "",
        f"Schema Version: {delta.get('schema_version') or 'unknown'}",
        f"Generated At: {delta.get('generated_at') or 'unknown'}",
        (
            "Has Previous State: "
            f"{'Yes' if delta.get('has_previous_state') else 'No'}"
        ),
        "",
        (
            "Material Change: "
            f"{'Yes' if material_count else 'No'}"
        ),
        f"Change Count: {summary.get('change_count') or 0}",
        f"Material Change Count: {material_count}",
        "",
        "Most Important Change:"
    ]

    if top_change:
        lines.append(
            f"{top_change.get('field')}: "
            f"{top_change.get('previous') or 'None'} -> "
            f"{top_change.get('current') or 'None'}"
        )
        lines.append(f"Reason: {top_change.get('reason') or 'N/A'}")
    else:
        lines.append("None")

    lines.extend(["", "What Changed:"])

    changes = delta.get("changes") or []

    if changes:
        lines.extend(
            (
                f"- {change.get('field')}: "
                f"{change.get('previous') or 'None'} -> "
                f"{change.get('current') or 'None'}"
            )
            for change in changes[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Risks Appeared:"])
    new_risks = delta.get("new_risks") or []

    if new_risks:
        lines.extend(
            (
                f"- {risk.get('severity') or 'UNKNOWN'} | "
                f"{risk.get('title') or 'Untitled risk'}"
            )
            for risk in new_risks[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Risks Resolved:"])
    resolved_risks = delta.get("resolved_risks") or []

    if resolved_risks:
        lines.extend(
            (
                f"- {risk.get('severity') or 'UNKNOWN'} | "
                f"{risk.get('title') or 'Untitled risk'}"
            )
            for risk in resolved_risks[:10]
        )
    else:
        lines.append("None")

    return "\n".join(lines) + "\n"


def write_state_delta_json(delta, path=None):

    path = Path(path) if path else STATE_DELTA_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(delta, indent=2, sort_keys=True),
            encoding="utf-8"
        )
    except (OSError, TypeError, ValueError) as error:
        return {
            "success": False,
            "path": str(path),
            "error": _safe_text(error)[:180]
        }

    return {
        "success": True,
        "path": str(path),
        "error": ""
    }


def write_state_delta_text(delta, path=None):

    path = Path(path) if path else STATE_DELTA_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_state_delta_text(delta), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {
            "success": False,
            "path": str(path),
            "error": _safe_text(error)[:180]
        }

    return {
        "success": True,
        "path": str(path),
        "error": ""
    }


def read_state_delta(path=None):

    path = Path(path) if path else STATE_DELTA_JSON_PATH

    try:
        delta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_echo_state_delta(None, {})

    return delta if isinstance(delta, dict) else build_echo_state_delta(None, {})
