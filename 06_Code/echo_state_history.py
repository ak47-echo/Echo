from collections import Counter, OrderedDict
from datetime import datetime
import json
from pathlib import Path


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
STATE_ARCHIVE_DIR = REPORTS_DIR / "archive" / "state"
STATE_HISTORY_JSON_PATH = REPORTS_DIR / "echo_state_history.json"
STATE_HISTORY_TEXT_PATH = REPORTS_DIR / "echo_state_history.txt"


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


def _field_value(state, path):

    value = _get_path(state, path)

    if isinstance(value, dict):
        for key in ("title", "theme_title", "name"):
            if value.get(key):
                return _safe_text(value.get(key))

        return None

    return _safe_text(value) or None


def _sample_timestamp(state):

    return _safe_text(
        state.get("generated_at") if isinstance(state, dict) else ""
    ) or None


def _load_snapshot(path):

    try:
        state = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None

    return state if isinstance(state, dict) else None


def _load_archived_states(state_archive_dir):

    archive_dir = Path(state_archive_dir)

    if not archive_dir.exists() or not archive_dir.is_dir():
        return []

    states = []

    try:
        paths = sorted(archive_dir.glob("*.json"))
    except OSError:
        return []

    for path in paths:
        state = _load_snapshot(path)

        if state is not None:
            states.append(state)

    return sorted(
        states,
        key=lambda state: (
            _sample_timestamp(state) or "",
            json.dumps(state, sort_keys=True)
        )
    )


def _dedupe_samples(states):

    samples = []
    seen = set()

    for state in states:
        if not isinstance(state, dict):
            continue

        timestamp = _sample_timestamp(state)
        key = timestamp or json.dumps(state, sort_keys=True)

        if key in seen:
            continue

        seen.add(key)
        samples.append(state)

    return samples


def _timeline(samples, path, key_name):

    return [
        {
            "generated_at": _sample_timestamp(sample),
            key_name: _field_value(sample, path)
        }
        for sample in samples
    ]


def _risk_key(risk):

    if not isinstance(risk, dict):
        return _safe_text(risk).casefold()

    return "|".join(
        _safe_text(risk.get(key)).casefold()
        for key in ("source", "title")
    )


def _risk_frequency(samples):

    counts = Counter()
    first_seen = OrderedDict()

    for sample in samples:
        seen_in_sample = set()
        risks = (
            sample.get("risk_register", [])
            if isinstance(sample, dict)
            else []
        )

        for risk in risks:
            key = _risk_key(risk)

            if not key or key in seen_in_sample:
                continue

            seen_in_sample.add(key)
            counts[key] += 1

            if key not in first_seen:
                first_seen[key] = {
                    "source": (
                        risk.get("source")
                        if isinstance(risk, dict)
                        else None
                    ),
                    "severity": (
                        risk.get("severity")
                        if isinstance(risk, dict)
                        else None
                    ),
                    "title": (
                        risk.get("title")
                        if isinstance(risk, dict)
                        else _safe_text(risk)
                    ),
                    "reason": (
                        risk.get("reason")
                        if isinstance(risk, dict)
                        else None
                    )
                }

    rows = []

    for key, count in counts.items():
        row = dict(first_seen[key])
        row["count"] = count
        rows.append(row)

    return sorted(
        rows,
        key=lambda row: (
            -row["count"],
            _safe_text(row.get("severity")).casefold(),
            _safe_text(row.get("title")).casefold()
        )
    )


def _action_frequency(samples):

    counts = Counter()

    for sample in samples:
        actions = (
            sample.get("action_queue", [])
            if isinstance(sample, dict)
            else []
        )
        seen_in_sample = set()

        for action in actions:
            text = _safe_text(action)
            key = text.casefold()

            if not key or key in seen_in_sample:
                continue

            seen_in_sample.add(key)
            counts[text] += 1

    return [
        {
            "action": action,
            "count": count
        }
        for action, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0].casefold())
        )
    ]


def _changed_count(samples, path):

    previous = object()
    changes = 0
    initialized = False

    for sample in samples:
        current = _field_value(sample, path)

        if not initialized:
            previous = current
            initialized = True
            continue

        if current != previous:
            changes += 1

        previous = current

    return changes


def _most_common(timeline, key_name):

    counts = Counter(
        item.get(key_name)
        for item in timeline
        if item.get(key_name)
    )

    if not counts:
        return None

    highest = max(counts.values())

    for item in timeline:
        value = item.get(key_name)

        if value and counts[value] == highest:
            return value

    return None


def _lookback(samples, archived_count):

    timestamps = [
        _sample_timestamp(sample)
        for sample in samples
        if _sample_timestamp(sample)
    ]

    return {
        "available_snapshots": archived_count,
        "oldest_snapshot": timestamps[0] if timestamps else None,
        "newest_snapshot": timestamps[-1] if timestamps else None
    }


def build_echo_state_history(current_state, state_archive_dir):

    archived_states = _load_archived_states(state_archive_dir)
    current = current_state if isinstance(current_state, dict) else {}
    samples = _dedupe_samples(archived_states + [current])
    priority_history = _timeline(
        samples,
        ("top_priority", "title"),
        "top_priority"
    )
    theme_history = _timeline(
        samples,
        ("dominant_theme", "theme_title"),
        "dominant_theme"
    )
    macro_regime_history = _timeline(
        samples,
        ("macro", "regime", "name"),
        "macro_regime"
    )
    portfolio_risk_history = _timeline(
        samples,
        ("portfolio", "current_risk", "title"),
        "portfolio_risk"
    )
    stress_scenario_history = _timeline(
        samples,
        ("portfolio", "worst_stress_scenario", "title"),
        "stress_scenario"
    )
    news_narrative_history = _timeline(
        samples,
        ("news", "top_narrative", "title"),
        "news_narrative"
    )
    risk_frequency = _risk_frequency(samples)
    action_frequency = _action_frequency(samples)
    persistent_risks = [
        risk for risk in risk_frequency
        if risk["count"] >= 2
    ]
    persistent_actions = [
        action for action in action_frequency
        if action["count"] >= 2
    ]

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "sample_count": len(samples),
        "lookback": _lookback(samples, len(archived_states)),
        "priority_history": priority_history,
        "theme_history": theme_history,
        "macro_regime_history": macro_regime_history,
        "portfolio_risk_history": portfolio_risk_history,
        "stress_scenario_history": stress_scenario_history,
        "news_narrative_history": news_narrative_history,
        "risk_frequency": risk_frequency,
        "action_frequency": action_frequency,
        "persistent_risks": persistent_risks,
        "persistent_actions": persistent_actions,
        "state_stability": {
            "priority_changed_count": _changed_count(
                samples,
                ("top_priority", "title")
            ),
            "theme_changed_count": _changed_count(
                samples,
                ("dominant_theme", "theme_title")
            ),
            "macro_regime_changed_count": _changed_count(
                samples,
                ("macro", "regime", "name")
            ),
            "portfolio_risk_changed_count": _changed_count(
                samples,
                ("portfolio", "current_risk", "title")
            )
        },
        "summary": {
            "dominant_persistent_risk": (
                persistent_risks[0] if persistent_risks else None
            ),
            "dominant_persistent_action": (
                persistent_actions[0] if persistent_actions else None
            ),
            "most_common_priority": _most_common(
                priority_history,
                "top_priority"
            ),
            "most_common_theme": _most_common(
                theme_history,
                "dominant_theme"
            ),
            "most_common_macro_regime": _most_common(
                macro_regime_history,
                "macro_regime"
            ),
            "most_common_portfolio_risk": _most_common(
                portfolio_risk_history,
                "portfolio_risk"
            )
        }
    }


def render_state_history_text(history):

    history = history if isinstance(history, dict) else {}
    summary = history.get("summary") or {}
    stability = history.get("state_stability") or {}
    persistent_risks = history.get("persistent_risks") or []
    persistent_actions = history.get("persistent_actions") or []
    lines = [
        "ECHO STATE HISTORY",
        "==================",
        "",
        f"Schema Version: {history.get('schema_version') or 'unknown'}",
        f"Generated At: {history.get('generated_at') or 'unknown'}",
        f"State Samples: {history.get('sample_count') or 0}",
        (
            "Archived Snapshots: "
            f"{(history.get('lookback') or {}).get('available_snapshots') or 0}"
        ),
        "",
        "Most Common Operating Picture:",
        (
            "Priority: "
            f"{summary.get('most_common_priority') or 'None'}"
        ),
        (
            "Theme: "
            f"{summary.get('most_common_theme') or 'None'}"
        ),
        (
            "Macro Regime: "
            f"{summary.get('most_common_macro_regime') or 'None'}"
        ),
        (
            "Portfolio Risk: "
            f"{summary.get('most_common_portfolio_risk') or 'None'}"
        ),
        "",
        "Persistent Risks:"
    ]

    if persistent_risks:
        lines.extend(
            (
                f"- {risk.get('title') or 'Untitled risk'} "
                f"({risk.get('count')} samples)"
            )
            for risk in persistent_risks[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Persistent Actions:"])

    if persistent_actions:
        lines.extend(
            (
                f"- {action.get('action') or 'Untitled action'} "
                f"({action.get('count')} samples)"
            )
            for action in persistent_actions[:10]
        )
    else:
        lines.append("None")

    lines.extend([
        "",
        "Operating Picture Stability:",
        (
            "Priority Changes: "
            f"{stability.get('priority_changed_count') or 0}"
        ),
        (
            "Theme Changes: "
            f"{stability.get('theme_changed_count') or 0}"
        ),
        (
            "Macro Regime Changes: "
            f"{stability.get('macro_regime_changed_count') or 0}"
        ),
        (
            "Portfolio Risk Changes: "
            f"{stability.get('portfolio_risk_changed_count') or 0}"
        )
    ])

    return "\n".join(lines) + "\n"


def write_state_history_json(history, path=None):

    path = Path(path) if path else STATE_HISTORY_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(history, indent=2, sort_keys=True),
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


def write_state_history_text(history, path=None):

    path = Path(path) if path else STATE_HISTORY_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_state_history_text(history), encoding="utf-8")
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


def read_state_history(path=None):

    path = Path(path) if path else STATE_HISTORY_JSON_PATH

    try:
        history = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_echo_state_history({}, STATE_ARCHIVE_DIR)

    return (
        history
        if isinstance(history, dict)
        else build_echo_state_history({}, STATE_ARCHIVE_DIR)
    )
