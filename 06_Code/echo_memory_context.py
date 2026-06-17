from datetime import datetime
import json
from pathlib import Path


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
MEMORY_CONTEXT_JSON_PATH = REPORTS_DIR / "echo_memory_context.json"
MEMORY_CONTEXT_TEXT_PATH = REPORTS_DIR / "echo_memory_context.txt"


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _title(value):

    if isinstance(value, dict):
        for key in ("title", "theme_title", "name", "action", "label"):
            text = _safe_text(value.get(key))
            if text:
                return text

    return _safe_text(value)


def _artifact_present(value):

    return isinstance(value, dict) and bool(value)


def _list(value):

    return value if isinstance(value, list) else []


def _dict(value):

    return value if isinstance(value, dict) else {}


def _signal_score(signal):

    if not isinstance(signal, dict):
        return 0

    try:
        return int(signal.get("score") or signal.get("weight") or 0)
    except (TypeError, ValueError):
        return 0


def _compact_item(layer, item_type, label, payload=None, score=None):

    item = {
        "layer": layer,
        "type": item_type,
        "label": _safe_text(label)
    }

    if score is not None:
        item["score"] = score

    if isinstance(payload, dict):
        compact_payload = {}

        for key, value in payload.items():
            if key in {"metadata", "relationship_index", "entity_index"}:
                continue

            if isinstance(value, (str, int, float, bool)) or value is None:
                compact_payload[key] = value

        if compact_payload:
            item["metadata"] = compact_payload

    return item


def _add_budgeted(target, item, budget):

    if not item or not item.get("label"):
        budget["excluded"] += 1
        return False

    if budget["included"] >= budget["max_items"]:
        budget["excluded"] += 1
        return False

    target.append(item)
    budget["included"] += 1
    return True


def _set_budgeted_current(current_state, key, value, budget):

    if not value:
        budget["excluded"] += 1
        return False

    if budget["included"] >= budget["max_items"]:
        budget["excluded"] += 1
        return False

    current_state[key] = value
    budget["included"] += 1
    return True


def _highest_scoring_signals(change_detection):

    signals = []

    for key in (
        "priority_signals",
        "risk_signals",
        "macro_signals",
        "portfolio_signals",
        "news_signals",
        "action_signals"
    ):
        signals.extend(_list(change_detection.get(key)))

    return sorted(
        [signal for signal in signals if isinstance(signal, dict)],
        key=lambda signal: (
            -_signal_score(signal),
            _safe_text(signal.get("category")),
            _safe_text(signal.get("name"))
        )
    )


def _budgeted_count(items, limit):

    return _list(items)[:max(int(limit or 0), 0)]


def build_echo_memory_context(state, delta, history, change_detection,
                              knowledge_graph, max_items=20):

    state = _dict(state)
    delta = _dict(delta)
    history = _dict(history)
    change_detection = _dict(change_detection)
    knowledge_graph = _dict(knowledge_graph)
    max_items = max(int(max_items or 0), 0)
    budget = {
        "max_items": max_items,
        "included": 0,
        "excluded": 0
    }
    operating_context = {
        "current_state": {},
        "important_changes": [],
        "persistent_patterns": [],
        "top_signals": [],
        "connected_entities": [],
        "recommended_attention": []
    }
    portfolio = _dict(state.get("portfolio"))
    macro = _dict(state.get("macro"))
    news = _dict(state.get("news"))
    detection_summary = _dict(change_detection.get("summary"))
    graph_summary = _dict(knowledge_graph.get("summary"))
    top_priority = _title(state.get("top_priority")) or None
    dominant_theme = _title(state.get("dominant_theme")) or None
    top_signal = _dict(detection_summary.get("top_signal"))

    for key, value in (
        ("top_priority", state.get("top_priority")),
        ("dominant_theme", state.get("dominant_theme")),
        ("portfolio_current_risk", portfolio.get("current_risk")),
        ("portfolio_worst_stress_scenario", portfolio.get("worst_stress_scenario")),
        ("macro_regime", macro.get("regime")),
        ("news_top_narrative", news.get("top_narrative"))
    ):
        label = _title(value)
        if label:
            _set_budgeted_current(
                operating_context["current_state"],
                key,
                value,
                budget
            )

    for change in _budgeted_count(delta.get("material_changes"), 2):
        _add_budgeted(
            operating_context["important_changes"],
            _compact_item(
                "delta",
                "material_change",
                _title(change.get("current")) or change.get("field"),
                change
            ),
            budget
        )

    for risk in _budgeted_count(delta.get("new_risks"), 1):
        _add_budgeted(
            operating_context["important_changes"],
            _compact_item("delta", "new_risk", _title(risk), risk),
            budget
        )

    for risk in _budgeted_count(delta.get("resolved_risks"), 1):
        _add_budgeted(
            operating_context["important_changes"],
            _compact_item("delta", "resolved_risk", _title(risk), risk),
            budget
        )

    for risk in _budgeted_count(history.get("persistent_risks"), 2):
        _add_budgeted(
            operating_context["persistent_patterns"],
            _compact_item("history", "persistent_risk", _title(risk), risk),
            budget
        )

    for action in _budgeted_count(history.get("persistent_actions"), 1):
        _add_budgeted(
            operating_context["persistent_patterns"],
            _compact_item("history", "persistent_action", _title(action), action),
            budget
        )

    if detection_summary:
        _add_budgeted(
            operating_context["top_signals"],
            _compact_item(
                "change_detection",
                "summary",
                (
                    _title(detection_summary.get("top_signal"))
                    or detection_summary.get("change_level")
                    or "Change detection summary"
                ),
                detection_summary
            ),
            budget
        )

    for signal in _highest_scoring_signals(change_detection)[:2]:
        _add_budgeted(
            operating_context["top_signals"],
            _compact_item(
                "change_detection",
                signal.get("type") or "signal",
                signal.get("name"),
                signal,
                _signal_score(signal)
            ),
            budget
        )

    if graph_summary:
        _add_budgeted(
            operating_context["connected_entities"],
            _compact_item(
                "knowledge_graph",
                "summary",
                graph_summary.get("dominant_cluster") or "Knowledge graph summary",
                graph_summary
            ),
            budget
        )

    for node in _budgeted_count(graph_summary.get("top_connected_nodes"), 1):
        _add_budgeted(
            operating_context["connected_entities"],
            _compact_item(
                "knowledge_graph",
                "connected_entity",
                node.get("label"),
                node,
                node.get("degree")
            ),
            budget
        )

    dominant_cluster_id = graph_summary.get("dominant_cluster")
    if dominant_cluster_id:
        for cluster in _list(knowledge_graph.get("clusters")):
            if cluster.get("id") == dominant_cluster_id:
                _add_budgeted(
                    operating_context["connected_entities"],
                    _compact_item(
                        "knowledge_graph",
                        "dominant_cluster",
                        cluster.get("label"),
                        cluster,
                        cluster.get("total_weight")
                    ),
                    budget
                )
                break

    for item in _budgeted_count(change_detection.get("recommended_attention"), 3):
        _add_budgeted(
            operating_context["recommended_attention"],
            _compact_item(
                "change_detection",
                "recommended_attention",
                item.get("name"),
                item,
                _signal_score(item)
            ),
            budget
        )

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "context_mode": "memory_first",
        "summary": {
            "top_priority": top_priority,
            "change_level": detection_summary.get("change_level"),
            "top_signal": _title(top_signal) or None,
            "dominant_theme": dominant_theme,
            "dominant_cluster": graph_summary.get("dominant_cluster"),
            "material_change_count": int(
                detection_summary.get("material_change_count") or 0
            ),
            "persistent_issue_count": int(
                detection_summary.get("persistent_issue_count") or 0
            )
        },
        "operating_context": operating_context,
        "context_budget": {
            "max_items": max_items,
            "included_items": budget["included"],
            "excluded_items": budget["excluded"]
        },
        "source_artifacts": {
            "state": _artifact_present(state),
            "delta": _artifact_present(delta),
            "history": _artifact_present(history),
            "change_detection": _artifact_present(change_detection),
            "knowledge_graph": _artifact_present(knowledge_graph)
        }
    }


def render_memory_context_text(memory_context):

    memory_context = _dict(memory_context)
    summary = _dict(memory_context.get("summary"))
    operating = _dict(memory_context.get("operating_context"))
    current = _dict(operating.get("current_state"))
    lines = [
        "ECHO MEMORY CONTEXT",
        "===================",
        "",
        f"Schema Version: {memory_context.get('schema_version') or 'unknown'}",
        f"Generated At: {memory_context.get('generated_at') or 'unknown'}",
        f"Context Mode: {memory_context.get('context_mode') or 'unknown'}",
        "",
        "What Echo Currently Needs To Know:",
        f"- Top Priority: {summary.get('top_priority') or 'None'}",
        f"- Dominant Theme: {summary.get('dominant_theme') or 'None'}",
        (
            "- Portfolio Risk: "
            f"{_title(current.get('portfolio_current_risk')) or 'None'}"
        ),
        (
            "- Macro Regime: "
            f"{_title(current.get('macro_regime')) or 'None'}"
        ),
        "",
        "What Changed That Matters:"
    ]

    changes = _list(operating.get("important_changes"))
    if changes:
        lines.extend(
            f"- {item.get('type')}: {item.get('label')}"
            for item in changes[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "What Has Persisted:"])
    persistent = _list(operating.get("persistent_patterns"))
    if persistent:
        lines.extend(
            f"- {item.get('type')}: {item.get('label')}"
            for item in persistent[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Connected Entities That Matter:"])
    connected = _list(operating.get("connected_entities"))
    if connected:
        lines.extend(
            (
                f"- {item.get('label')} "
                f"({item.get('type')}, score {item.get('score', 'n/a')})"
            )
            for item in connected[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "What Echo Should Pay Attention To First:"])
    attention = _list(operating.get("recommended_attention"))
    if attention:
        lines.extend(
            (
                f"- {item.get('label')} "
                f"(score {item.get('score', 'n/a')})"
            )
            for item in attention[:10]
        )
    else:
        top_signal = summary.get("top_signal")
        lines.append(top_signal or "None")

    budget = _dict(memory_context.get("context_budget"))
    lines.extend([
        "",
        "Context Budget:",
        f"Max Items: {budget.get('max_items') or 0}",
        f"Included Items: {budget.get('included_items') or 0}",
        f"Excluded Items: {budget.get('excluded_items') or 0}"
    ])

    return "\n".join(lines) + "\n"


def write_memory_context_json(memory_context, path=None):

    path = Path(path) if path else MEMORY_CONTEXT_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(memory_context, indent=2, sort_keys=True),
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


def write_memory_context_text(memory_context, path=None):

    path = Path(path) if path else MEMORY_CONTEXT_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_memory_context_text(memory_context),
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


def read_memory_context(path=None):

    path = Path(path) if path else MEMORY_CONTEXT_JSON_PATH

    try:
        memory_context = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_echo_memory_context({}, {}, {}, {}, {})

    return (
        memory_context
        if isinstance(memory_context, dict)
        else build_echo_memory_context({}, {}, {}, {}, {})
    )
