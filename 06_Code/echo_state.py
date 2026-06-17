from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
STATE_JSON_PATH = REPORTS_DIR / "echo_state.json"
STATE_TEXT_PATH = REPORTS_DIR / "echo_state.txt"
REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "generated_at",
    "top_priority",
    "dominant_theme",
    "portfolio",
    "research",
    "news",
    "macro",
    "conflicts",
    "action_queue",
    "risk_register"
)


def _lines(value):

    if isinstance(value, dict):
        value = value.get("executive_brief", [])

    if isinstance(value, str):
        value = value.splitlines()

    if not isinstance(value, (list, tuple)):
        return []

    return [str(line).strip() for line in value if str(line).strip()]


def _sections(bundle_or_sections):

    if isinstance(bundle_or_sections, dict):
        sections = bundle_or_sections.get("sections", bundle_or_sections)

        if isinstance(sections, dict):
            return sections

    return {}


def _full_lines(report):

    if isinstance(report, dict):
        values = []

        for key in ("executive_brief", "full_report"):
            values.extend(_lines(report.get(key, [])))

        return values

    return _lines(report)


def _field(lines, label):

    prefix = f"{label}:"

    for line in _lines(lines):
        if line.startswith(prefix):
            value = line[len(prefix):].strip()

            if value and value.casefold() not in {"none", "n/a", "unknown"}:
                return value

    return None


def _report_section(lines, heading):

    lines = _lines(lines)

    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []

    section = []

    for line in lines[start:]:
        if line and (
            line.isupper()
            or (
                section
                and line.endswith(":")
                and not line.startswith("-")
            )
        ):
            break

        if line:
            section.append(line)

    return section


def _numbered_after(lines, heading, limit=5):

    lines = _lines(lines)

    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []

    items = []

    for line in lines[start:]:
        if not line:
            if items:
                break
            continue

        match = re.match(r"^\d+\.\s*(.+)$", line)

        if not match:
            if items:
                break
            continue

        items.append(match.group(1).strip())

        if len(items) >= limit:
            break

    return items


def _numbered_blocks(lines, limit=10):

    blocks = []
    current = None

    for line in _lines(lines):
        match = re.match(r"^(\d+)\.\s*(.+)$", line)

        if match:
            if current is not None:
                blocks.append(current)

            current = {
                "rank": int(match.group(1)),
                "title": match.group(2).strip(),
                "fields": {},
                "evidence": []
            }
            continue

        if current is None:
            continue

        if line.startswith("- "):
            current["evidence"].append(line[2:].strip())
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            current["fields"][key.strip()] = value.strip()

    if current is not None:
        blocks.append(current)

    return blocks[:limit]


def _as_int(value):

    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_priority(sections):

    summary = _lines(sections.get("priority_summary", []))
    block = next(iter(_numbered_blocks(sections.get("priority_details", []), 1)),
                 {})
    fields = block.get("fields", {})

    title = block.get("title") or _field(summary, "Top Priority")

    if not title:
        return None

    return {
        "title": title,
        "source_agent": fields.get("Source") or _field(summary, "Priority Source"),
        "severity": fields.get("Severity"),
        "category": fields.get("Category"),
        "risk_timeframe": fields.get("Risk Timeframe"),
        "reason": fields.get("Reason")
    }


def _parse_dominant_theme(sections):

    summary = _lines(sections.get("theme_summary", []))
    theme = _field(summary, "Dominant Theme")

    if not theme:
        return None

    return {
        "theme_title": theme,
        "theme_score": _as_int(_field(summary, "Dominant Theme Score")),
        "theme_strength": _field(summary, "Dominant Theme Strength"),
        "theme_reason": _field(summary, "Dominant Theme Reason")
    }


def _parse_portfolio(sections):

    executive = _lines(sections.get("executive_summary", []))
    portfolio_lines = _full_lines(sections.get("portfolio", []))
    concentrations = []

    for line in _report_section(portfolio_lines, "CONCENTRATION RISK DETAILS"):
        parts = [part.strip() for part in line.split("|")]

        if len(parts) >= 3 and parts[0] in {"HIGH", "MEDIUM", "LOW"}:
            concentrations.append({
                "severity": parts[0],
                "ticker": parts[1],
                "description": " | ".join(parts[2:])
            })

    weak_holdings = []

    for line in _report_section(
        _full_lines(sections.get("research", [])),
        "Holding Thesis Quality:"
    ):
        if "Research Status STRONG" in line:
            continue

        if line.casefold() == "none":
            continue

        weak_holdings.append(line)

    return {
        "current_risk": {
            "title": _field(executive, "Top Portfolio Risk"),
            "source": "Echo executive summary"
        },
        "worst_stress_scenario": {
            "title": (
                _field(executive, "Worst Stress Scenario")
                or _field(
                    _report_section(portfolio_lines, "STRESS TEST SUMMARY"),
                    "Worst Scenario"
                )
            )
        },
        "concentration_flags": concentrations,
        "weak_holdings": weak_holdings[:10]
    }


def _parse_research(sections):

    research = sections.get("research", {})
    executive = _lines(research)
    full = _full_lines(research)
    top_convictions = []
    highest = _field(executive, "Highest Conviction Holding")

    if highest:
        top_convictions.append({
            "ticker": highest,
            "basis": "Highest conviction holding"
        })

    coverage = _report_section(full, "Coverage Summary:")
    weak_coverage = []

    for label in ("Uncovered Holdings", "Uncovered Watchlist"):
        value = _field(coverage, label)

        if value and value.casefold() != "none":
            weak_coverage.append({
                "area": label,
                "items": [
                    item.strip()
                    for item in value.split(",")
                    if item.strip()
                ]
            })

    priorities = _numbered_after(full, "Top Research Priorities:", limit=5)

    if not priorities:
        priority = _field(executive, "Top Research Priority")
        priorities = [priority] if priority else []

    return {
        "top_convictions": top_convictions,
        "weak_coverage": weak_coverage,
        "watchlist_priorities": priorities
    }


def _parse_news(sections):

    news = sections.get("news", {})
    executive = _lines(news)
    full = _full_lines(news)
    top_narrative = _field(executive, "Top Market Narrative")

    return {
        "top_narrative": (
            {
                "title": top_narrative,
                "score": _as_int(_field(executive, "Top Narrative Score")),
                "supporting_articles": _as_int(
                    _field(executive, "Supporting Articles")
                ),
                "representative_headline": _field(
                    executive,
                    "Representative Headline"
                ),
                "reason": _field(executive, "Top Narrative Reason")
            }
            if top_narrative
            else None
        ),
        "market_significant_items": _numbered_blocks(
            _report_section(full, "Top Ranked Stories:"),
            limit=5
        ),
        "portfolio_relevant_items": _report_section(
            full,
            "Portfolio-Relevant Stories:"
        )[:5]
    }


def _parse_macro(sections):

    macro = sections.get("macro", {})
    executive = _lines(macro)
    full = _full_lines(macro)
    top_priority = _field(executive, "Top Macro Priority")
    regime = _field(executive, "Current Macro Regime")

    return {
        "regime": {
            "name": regime,
            "confidence": _field(executive, "Confidence"),
            "top_priority": top_priority,
            "reason": _field(executive, "Top Macro Reason")
        },
        "top_macro_risks": _numbered_blocks(
            _report_section(full, "Ranked Macro Priority Signals:"),
            limit=5
        ),
        "regime_score": _as_int(
            re.search(
                r"Regime Score\s+(\d+)",
                top_priority or ""
            ).group(1)
        ) if re.search(r"Regime Score\s+(\d+)", top_priority or "") else None
    }


def _parse_conflicts(sections):

    conflicts = []

    for block in _numbered_blocks(sections.get("theme_conflict_details", [])):
        fields = block.get("fields", {})
        title = block.get("title")

        if not title or title == "No deterministic theme conflicts detected.":
            continue

        conflicts.append({
            "conflict_title": title,
            "conflict_type": fields.get("Conflict Type"),
            "conflict_severity": fields.get("Conflict Severity"),
            "affected_holdings": [
                item.strip()
                for item in (fields.get("Affected Holdings") or "").split(",")
                if item.strip() and item.strip().casefold() != "none"
            ],
            "conflict_reason": fields.get("Conflict Reason"),
            "suggested_review_area": fields.get("Suggested Review Area"),
            "evidence": block.get("evidence", [])
        })

    return conflicts


def _build_risk_register(state):

    risks = []
    priority = state.get("top_priority")

    if priority:
        risks.append({
            "source": "top_priority",
            "severity": priority.get("severity"),
            "title": priority.get("title"),
            "reason": priority.get("reason")
        })

    for flag in state.get("portfolio", {}).get("concentration_flags", [])[:5]:
        risks.append({
            "source": "portfolio_concentration",
            "severity": flag.get("severity"),
            "title": flag.get("ticker"),
            "reason": flag.get("description")
        })

    for conflict in state.get("conflicts", [])[:5]:
        risks.append({
            "source": "conflict",
            "severity": conflict.get("conflict_severity"),
            "title": conflict.get("conflict_title"),
            "reason": conflict.get("conflict_reason")
        })

    for risk in state.get("macro", {}).get("top_macro_risks", [])[:3]:
        risks.append({
            "source": "macro",
            "severity": risk.get("fields", {}).get("Priority Tier"),
            "title": risk.get("title"),
            "reason": risk.get("fields", {}).get("Reason")
        })

    return risks[:15]


def build_echo_state(bundle_or_sections=None, generated_at=None):

    sections = _sections(bundle_or_sections)
    state = {
        "schema_version": "1.0",
        "generated_at": (
            generated_at
            or datetime.now().isoformat(timespec="seconds")
        ),
        "top_priority": _parse_priority(sections),
        "dominant_theme": _parse_dominant_theme(sections),
        "portfolio": _parse_portfolio(sections),
        "research": _parse_research(sections),
        "news": _parse_news(sections),
        "macro": _parse_macro(sections),
        "conflicts": _parse_conflicts(sections),
        "action_queue": _numbered_after(
            sections.get("executive_summary", []),
            "Priority Action Queue:",
            limit=5
        ),
        "risk_register": []
    }
    state["risk_register"] = _build_risk_register(state)

    return state


def validate_echo_state(state):

    if not isinstance(state, dict):
        return False

    return all(key in state for key in REQUIRED_TOP_LEVEL_KEYS)


def render_echo_state_summary(state):

    state = state if isinstance(state, dict) else {}
    portfolio = state.get("portfolio") or {}
    research = state.get("research") or {}
    news = state.get("news") or {}
    macro = state.get("macro") or {}
    lines = [
        "ECHO STATE SUMMARY",
        "==================",
        "",
        f"Schema Version: {state.get('schema_version') or 'unknown'}",
        f"Generated At: {state.get('generated_at') or 'unknown'}",
        "",
        "Top Priority: "
        f"{(state.get('top_priority') or {}).get('title') or 'None'}",
        "Dominant Theme: "
        f"{(state.get('dominant_theme') or {}).get('theme_title') or 'None'}",
        "Portfolio Risk: "
        f"{(portfolio.get('current_risk') or {}).get('title') or 'None'}",
        "Worst Stress Scenario: "
        f"{(portfolio.get('worst_stress_scenario') or {}).get('title') or 'None'}",
        "Top News Narrative: "
        f"{(news.get('top_narrative') or {}).get('title') or 'None'}",
        "Macro Regime: "
        f"{(macro.get('regime') or {}).get('name') or 'None'}",
        "",
        f"Concentration Flags: {len(portfolio.get('concentration_flags') or [])}",
        f"Weak Holdings: {len(portfolio.get('weak_holdings') or [])}",
        f"Research Coverage Gaps: {len(research.get('weak_coverage') or [])}",
        f"Conflicts: {len(state.get('conflicts') or [])}",
        f"Action Queue Items: {len(state.get('action_queue') or [])}",
        f"Risk Register Items: {len(state.get('risk_register') or [])}",
        "",
        "Action Queue:"
    ]

    actions = state.get("action_queue") or []

    if actions:
        lines.extend(
            f"{index}. {action}"
            for index, action in enumerate(actions, start=1)
        )
    else:
        lines.append("None")

    return "\n".join(lines) + "\n"


def write_echo_state(state, reports_dir=None):

    reports_dir = Path(reports_dir) if reports_dir else REPORTS_DIR
    json_path = reports_dir / "echo_state.json"
    text_path = reports_dir / "echo_state.txt"

    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(state, indent=2, sort_keys=True),
            encoding="utf-8"
        )
        text_path.write_text(render_echo_state_summary(state), encoding="utf-8")
    except (OSError, TypeError, ValueError) as error:
        return {
            "success": False,
            "json_path": str(json_path),
            "text_path": str(text_path),
            "error": " ".join(str(error).split())[:180]
        }

    return {
        "success": True,
        "json_path": str(json_path),
        "text_path": str(text_path),
        "error": ""
    }


def read_echo_state(path=None):

    path = Path(path) if path else STATE_JSON_PATH

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_echo_state({})
