from datetime import datetime
import json
from pathlib import Path


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
CHANGE_DETECTION_JSON_PATH = REPORTS_DIR / "echo_change_detection.json"
CHANGE_DETECTION_TEXT_PATH = REPORTS_DIR / "echo_change_detection.txt"


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
        for key in ("title", "theme_title", "name", "action"):
            if value.get(key):
                return _safe_text(value.get(key))

        return None

    return _safe_text(value) or None


def _severity(value):

    return _safe_text(value).upper()


def _is_high_or_critical(item):

    if not isinstance(item, dict):
        return False

    values = [
        item.get("severity"),
        item.get("priority"),
        item.get("level"),
        item.get("rating")
    ]

    return any(
        _severity(value) in {"HIGH", "CRITICAL", "SEVERE"}
        for value in values
    )


def _contains_critical_label(*values):

    text = " ".join(_safe_text(value).casefold() for value in values)

    return any(label in text for label in ("critical", "severe"))


def _signal(signal_type, category, name, description, score, source,
            is_material=False):

    return {
        "type": signal_type,
        "category": category,
        "name": _safe_text(name) or "Unnamed signal",
        "description": _safe_text(description),
        "score": int(score),
        "source": source,
        "is_material": bool(is_material)
    }


def _risk_name(risk):

    if isinstance(risk, dict):
        return _safe_text(risk.get("title")) or "Untitled risk"

    return _safe_text(risk) or "Untitled risk"


def _action_name(action):

    if isinstance(action, dict):
        return _safe_text(action.get("action")) or _safe_text(action.get("title"))

    return _safe_text(action)


def _positive_sorted(signals):

    return sorted(
        [signal for signal in signals if signal.get("score", 0) > 0],
        key=lambda signal: (
            -signal.get("score", 0),
            signal.get("category", ""),
            signal.get("name", "").casefold()
        )
    )


def _history_count(rows, value, value_key):

    needle = _safe_text(value).casefold()

    if not needle:
        return 0

    for row in rows or []:
        if _safe_text(row.get(value_key)).casefold() == needle:
            return int(row.get("count") or 0)

    return 0


def _change_current(change):

    return (change or {}).get("current") if isinstance(change, dict) else None


def _change_previous(change):

    return (change or {}).get("previous") if isinstance(change, dict) else None


def _new_action_changes(delta):

    changes = delta.get("changes") if isinstance(delta, dict) else []

    return [
        change for change in changes or []
        if (
            isinstance(change, dict)
            and change.get("field") == "action_queue"
            and change.get("change_type") == "added"
        )
    ]


def _change_level(signals, material_change_count):

    if not signals:
        return "none"

    positive = _positive_sorted(signals)
    top_score = positive[0]["score"] if positive else 0
    high_score_count = len([
        signal for signal in positive
        if signal.get("score", 0) >= 40
    ])
    critical_label = any(
        _contains_critical_label(
            signal.get("name"),
            signal.get("description")
        )
        for signal in positive
    )

    if critical_label or high_score_count >= 2:
        return "critical"

    if top_score >= 50 or (
        material_change_count > 0 and top_score >= 35
    ):
        return "high"

    if top_score >= 25 or material_change_count > 0:
        return "moderate"

    return "low"


def _recommended_attention(signals):

    return [
        {
            "category": signal.get("category"),
            "name": signal.get("name"),
            "score": signal.get("score"),
            "description": signal.get("description")
        }
        for signal in _positive_sorted(signals)[:5]
    ]


def build_echo_change_detection(current_state, state_delta, state_history):

    current_state = current_state if isinstance(current_state, dict) else {}
    state_delta = state_delta if isinstance(state_delta, dict) else {}
    state_history = state_history if isinstance(state_history, dict) else {}
    summary = state_delta.get("summary") or {}
    history_summary = state_history.get("summary") or {}
    stability = state_history.get("state_stability") or {}
    sample_count = int(state_history.get("sample_count") or 0)
    material_change_count = int(summary.get("material_change_count") or 0)

    priority_signals = []
    risk_signals = []
    macro_signals = []
    portfolio_signals = []
    news_signals = []
    action_signals = []
    deescalations = []

    priority_change = state_delta.get("priority_change")
    if priority_change:
        current = _change_current(priority_change)
        previous = _change_previous(priority_change)
        priority_signals.append(_signal(
            "priority_changed",
            "priority",
            current or "Top priority changed",
            f"Top priority changed from {previous or 'None'} to "
            f"{current or 'None'}.",
            50,
            "delta",
            True
        ))

    theme_change = state_delta.get("theme_change")
    if theme_change:
        current = _change_current(theme_change)
        previous = _change_previous(theme_change)
        priority_signals.append(_signal(
            "theme_changed",
            "priority",
            current or "Dominant theme changed",
            f"Dominant theme changed from {previous or 'None'} to "
            f"{current or 'None'}.",
            20,
            "delta",
            True
        ))

    current_priority = _field_value(current_state, ("top_priority", "title"))
    if (
        current_priority
        and sample_count >= 2
        and current_priority == history_summary.get("most_common_priority")
    ):
        priority_signals.append(_signal(
            "priority_persistent",
            "priority",
            current_priority,
            "Top priority is also the most common historical priority.",
            20,
            "history",
            False
        ))

    priority_risk_count = _history_count(
        state_history.get("risk_frequency"),
        current_priority,
        "title"
    )
    priority_action_count = _history_count(
        state_history.get("action_frequency"),
        current_priority,
        "action"
    )
    if priority_risk_count:
        priority_signals.append(_signal(
            "priority_in_risk_frequency",
            "priority",
            current_priority,
            f"Top priority appears in risk frequency across "
            f"{priority_risk_count} samples.",
            20,
            "history",
            False
        ))
    if priority_action_count:
        priority_signals.append(_signal(
            "priority_in_action_frequency",
            "priority",
            current_priority,
            f"Top priority appears in action frequency across "
            f"{priority_action_count} samples.",
            15,
            "history",
            False
        ))

    for risk in state_delta.get("new_risks") or []:
        score = 40 if _is_high_or_critical(risk) else 30
        signal = _signal(
            "new_risk",
            "risk",
            _risk_name(risk),
            (
                f"New risk appeared with severity "
                f"{risk.get('severity') or 'UNKNOWN'}."
            ),
            score,
            "delta",
            _is_high_or_critical(risk)
        )
        risk_signals.append(signal)

    for risk in state_delta.get("resolved_risks") or []:
        signal = _signal(
            "resolved_risk",
            "risk",
            _risk_name(risk),
            (
                f"Risk resolved or disappeared with prior severity "
                f"{risk.get('severity') or 'UNKNOWN'}."
            ),
            -15,
            "delta",
            False
        )
        risk_signals.append(signal)
        deescalations.append(signal)

    for risk in state_history.get("persistent_risks") or []:
        score = 35 if _is_high_or_critical(risk) else 25
        risk_signals.append(_signal(
            "persistent_risk",
            "risk",
            _risk_name(risk),
            f"Risk appears in {risk.get('count') or 0} state samples.",
            score,
            "history",
            _is_high_or_critical(risk)
        ))

    for risk in current_state.get("risk_register") or []:
        if _is_high_or_critical(risk):
            risk_signals.append(_signal(
                "high_priority_risk",
                "risk",
                _risk_name(risk),
                "Current risk register contains a high-priority risk.",
                20,
                "state",
                True
            ))

    macro_change = state_delta.get("macro_regime_change")
    if macro_change:
        current = _change_current(macro_change)
        previous = _change_previous(macro_change)
        macro_signals.append(_signal(
            "macro_regime_changed",
            "macro",
            current or "Macro regime changed",
            f"Macro regime changed from {previous or 'None'} to "
            f"{current or 'None'}.",
            35,
            "delta",
            True
        ))

    macro_changes = int(stability.get("macro_regime_changed_count") or 0)
    if macro_changes >= 2:
        macro_signals.append(_signal(
            "macro_regime_unstable",
            "macro",
            "Macro regime instability",
            f"Macro regime changed {macro_changes} times across history.",
            20,
            "history",
            False
        ))

    current_regime = _field_value(current_state, ("macro", "regime", "name"))
    if (
        current_regime
        and sample_count >= 2
        and current_regime == history_summary.get("most_common_macro_regime")
    ):
        macro_signals.append(_signal(
            "macro_regime_persistent",
            "macro",
            current_regime,
            "Macro regime is the most common historical regime.",
            15,
            "history",
            False
        ))

    portfolio_change = state_delta.get("portfolio_risk_change")
    if portfolio_change:
        current = _change_current(portfolio_change)
        previous = _change_previous(portfolio_change)
        portfolio_signals.append(_signal(
            "portfolio_risk_changed",
            "portfolio",
            current or "Portfolio risk changed",
            f"Portfolio current risk changed from {previous or 'None'} to "
            f"{current or 'None'}.",
            35,
            "delta",
            True
        ))

    stress_change = state_delta.get("stress_scenario_change")
    if stress_change:
        current = _change_current(stress_change)
        previous = _change_previous(stress_change)
        portfolio_signals.append(_signal(
            "stress_scenario_changed",
            "portfolio",
            current or "Stress scenario changed",
            f"Worst stress scenario changed from {previous or 'None'} to "
            f"{current or 'None'}.",
            20,
            "delta",
            False
        ))

    current_portfolio_risk = _field_value(
        current_state,
        ("portfolio", "current_risk", "title")
    )
    if (
        current_portfolio_risk
        and sample_count >= 2
        and current_portfolio_risk
        == history_summary.get("most_common_portfolio_risk")
    ):
        portfolio_signals.append(_signal(
            "portfolio_risk_persistent",
            "portfolio",
            current_portfolio_risk,
            "Portfolio current risk is the most common historical risk.",
            20,
            "history",
            False
        ))

    portfolio = current_state.get("portfolio") or {}
    for flag in portfolio.get("concentration_flags") or []:
        name = _safe_text(flag.get("title") if isinstance(flag, dict) else flag)
        if not name:
            continue

        portfolio_signals.append(_signal(
            "portfolio_concentration_flag",
            "portfolio",
            name,
            "Current portfolio state includes a concentration flag.",
            15,
            "state",
            False
        ))

    news_change = state_delta.get("news_narrative_change")
    if news_change:
        current = _change_current(news_change)
        previous = _change_previous(news_change)
        news_signals.append(_signal(
            "news_narrative_changed",
            "news",
            current or "News narrative changed",
            f"Top news narrative changed from {previous or 'None'} to "
            f"{current or 'None'}.",
            15,
            "delta",
            False
        ))

    news = current_state.get("news") or {}
    if news.get("market_significant_items"):
        news_signals.append(_signal(
            "market_significant_news",
            "news",
            "Market significant news",
            (
                f"{len(news.get('market_significant_items') or [])} market "
                "significant news items are present."
            ),
            10,
            "state",
            False
        ))

    if news.get("portfolio_relevant_items"):
        news_signals.append(_signal(
            "portfolio_relevant_news",
            "news",
            "Portfolio relevant news",
            (
                f"{len(news.get('portfolio_relevant_items') or [])} portfolio "
                "relevant news items are present."
            ),
            10,
            "state",
            False
        ))

    for change in _new_action_changes(state_delta):
        action = _safe_text(change.get("current"))
        score = 25 if change.get("material") else 10
        action_signals.append(_signal(
            "new_action",
            "action",
            action or "New action",
            "Action queue gained a new item.",
            score,
            "delta",
            bool(change.get("material"))
        ))

    for action in state_history.get("persistent_actions") or []:
        action_signals.append(_signal(
            "persistent_action",
            "action",
            _action_name(action) or "Persistent action",
            f"Action appears in {action.get('count') or 0} state samples.",
            15,
            "history",
            False
        ))

    for action in current_state.get("action_queue") or []:
        text = _action_name(action)
        lowered = text.casefold()
        if lowered.startswith(("review ", "reevaluate ", "investigate ")):
            action_signals.append(_signal(
                "high_priority_action",
                "action",
                text,
                "Current action queue contains a review-class action.",
                10,
                "state",
                False
            ))

    all_signals = (
        priority_signals
        + risk_signals
        + macro_signals
        + portfolio_signals
        + news_signals
        + action_signals
    )
    novel_signals = [
        signal for signal in all_signals
        if signal.get("source") == "delta" and signal.get("score", 0) > 0
    ]
    persistent_signals = [
        signal for signal in all_signals
        if signal.get("source") == "history"
    ]
    escalations = [
        signal for signal in novel_signals
        if signal.get("score", 0) >= 25 or signal.get("is_material")
    ]
    top_signal = _positive_sorted(all_signals)
    top_signal = top_signal[0] if top_signal else (
        all_signals[0] if all_signals else None
    )

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "summary": {
            "change_level": _change_level(all_signals, material_change_count),
            "material_change_count": material_change_count,
            "novel_change_count": len(novel_signals),
            "persistent_issue_count": len(persistent_signals),
            "top_signal": top_signal
        },
        "priority_signals": priority_signals,
        "risk_signals": risk_signals,
        "macro_signals": macro_signals,
        "portfolio_signals": portfolio_signals,
        "news_signals": news_signals,
        "action_signals": action_signals,
        "novel_signals": novel_signals,
        "persistent_signals": persistent_signals,
        "escalations": escalations,
        "deescalations": deescalations,
        "recommended_attention": _recommended_attention(all_signals)
    }


def render_change_detection_text(detection):

    detection = detection if isinstance(detection, dict) else {}
    summary = detection.get("summary") or {}
    lines = [
        "ECHO CHANGE DETECTION",
        "=====================",
        "",
        f"Schema Version: {detection.get('schema_version') or 'unknown'}",
        f"Generated At: {detection.get('generated_at') or 'unknown'}",
        f"Change Level: {summary.get('change_level') or 'unknown'}",
        (
            "Material Change Count: "
            f"{summary.get('material_change_count') or 0}"
        ),
        (
            "Novel Change Count: "
            f"{summary.get('novel_change_count') or 0}"
        ),
        (
            "Persistent Issue Count: "
            f"{summary.get('persistent_issue_count') or 0}"
        ),
        "",
        "Most Important Signal:"
    ]

    top_signal = summary.get("top_signal")
    if top_signal:
        lines.append(
            f"{top_signal.get('category')}: {top_signal.get('name')} "
            f"(score {top_signal.get('score')})"
        )
        lines.append(top_signal.get("description") or "No description.")
    else:
        lines.append("None")

    lines.extend(["", "What Changed That Matters:"])
    novel_signals = detection.get("novel_signals") or []
    if novel_signals:
        lines.extend(
            (
                f"- {signal.get('category')}: {signal.get('name')} "
                f"(score {signal.get('score')})"
            )
            for signal in _positive_sorted(novel_signals)[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "What Persists That Matters:"])
    persistent_signals = detection.get("persistent_signals") or []
    if persistent_signals:
        lines.extend(
            (
                f"- {signal.get('category')}: {signal.get('name')} "
                f"(score {signal.get('score')})"
            )
            for signal in _positive_sorted(persistent_signals)[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Escalations:"])
    escalations = detection.get("escalations") or []
    if escalations:
        lines.extend(
            (
                f"- {signal.get('category')}: {signal.get('name')} "
                f"(score {signal.get('score')})"
            )
            for signal in _positive_sorted(escalations)[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Deescalations:"])
    deescalations = detection.get("deescalations") or []
    if deescalations:
        lines.extend(
            (
                f"- {signal.get('category')}: {signal.get('name')} "
                f"(score {signal.get('score')})"
            )
            for signal in deescalations[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Recommended Attention:"])
    attention = detection.get("recommended_attention") or []
    if attention:
        lines.extend(
            (
                f"- {item.get('category')}: {item.get('name')} "
                f"(score {item.get('score')})"
            )
            for item in attention
        )
    else:
        lines.append("None")

    return "\n".join(lines) + "\n"


def write_change_detection_json(detection, path=None):

    path = Path(path) if path else CHANGE_DETECTION_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(detection, indent=2, sort_keys=True),
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


def write_change_detection_text(detection, path=None):

    path = Path(path) if path else CHANGE_DETECTION_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_change_detection_text(detection), encoding="utf-8")
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


def read_change_detection(path=None):

    path = Path(path) if path else CHANGE_DETECTION_JSON_PATH

    try:
        detection = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_echo_change_detection({}, {}, {})

    return (
        detection
        if isinstance(detection, dict)
        else build_echo_change_detection({}, {}, {})
    )
