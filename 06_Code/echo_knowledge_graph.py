from collections import Counter, defaultdict, deque
from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
KNOWLEDGE_GRAPH_JSON_PATH = REPORTS_DIR / "echo_knowledge_graph.json"
KNOWLEDGE_GRAPH_TEXT_PATH = REPORTS_DIR / "echo_knowledge_graph.txt"

NODE_TYPES = {
    "theme",
    "risk",
    "action",
    "agent",
    "holding",
    "macro_regime",
    "news_narrative",
    "portfolio_signal",
    "research_signal",
    "priority",
    "stress_scenario"
}
RELATIONSHIPS = {
    "relates_to",
    "causes",
    "influences",
    "appears_with",
    "escalates",
    "deescalates",
    "belongs_to",
    "generated_by"
}
LAYERS = {"state", "delta", "history", "change_detection"}
AGENTS = (
    "Echo",
    "Portfolio Agent",
    "Research Agent",
    "News Agent",
    "Macro Agent"
)


def _now():

    return datetime.now().isoformat(timespec="seconds")


def normalize_entity_id(value):

    text = " ".join(str(value or "").strip().lower().split())
    text = re.sub(r"[\s/\\]+", "_", text)
    text = re.sub(r"[^a-z0-9_-]+", "", text)
    return text.strip("_") or "unknown"


def _safe_text(value):

    return " ".join(str(value or "").split())


def _title(value):

    if isinstance(value, dict):
        for key in (
            "title",
            "theme_title",
            "name",
            "action",
            "ticker",
            "conflict_title"
        ):
            text = _safe_text(value.get(key))
            if text:
                return text

    return _safe_text(value)


def _node_id(node_type, label):

    return f"{node_type}:{normalize_entity_id(label)}"


def _tokens(value):

    return {
        token
        for token in re.findall(r"[a-z0-9]+", _safe_text(value).lower())
        if len(token) >= 3
        and token not in {
            "the",
            "and",
            "for",
            "with",
            "from",
            "this",
            "that",
            "risk",
            "action",
            "review",
            "current"
        }
    }


def _overlaps(left, right):

    return bool(_tokens(left) & _tokens(right))


def _bounded_int(value, default=0):

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class _GraphBuilder:

    def __init__(self):

        self.nodes = {}
        self.edges = {}

    def add_node(self, node_type, label, source, weight, metadata=None):

        label = _safe_text(label)
        if not label:
            return None

        node_type = node_type if node_type in NODE_TYPES else "risk"
        source = source if source in LAYERS else "state"
        node_id = _node_id(node_type, label)

        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
                "source": source,
                "weight": 0,
                "metadata": {}
            }

        node = self.nodes[node_id]
        node["weight"] += _bounded_int(weight)
        node["metadata"].update(metadata if isinstance(metadata, dict) else {})

        return node_id

    def add_edge(self, source, target, relationship, weight, source_layer,
                 metadata=None):

        if not source or not target:
            return None

        relationship = (
            relationship if relationship in RELATIONSHIPS else "relates_to"
        )
        source_layer = source_layer if source_layer in LAYERS else "state"
        key = (source, target, relationship, source_layer)

        if key not in self.edges:
            self.edges[key] = {
                "source": source,
                "target": target,
                "relationship": relationship,
                "weight": 0,
                "source_layer": source_layer,
                "metadata": {}
            }

        edge = self.edges[key]
        edge["weight"] += _bounded_int(weight)
        edge["metadata"].update(metadata if isinstance(metadata, dict) else {})

        return key


def _add_agent_nodes(builder):

    agent_ids = {}

    for agent in AGENTS:
        agent_ids[agent] = builder.add_node(
            "agent",
            agent,
            "state",
            5,
            {"role": "system" if agent == "Echo" else "agent"}
        )

    echo_id = agent_ids["Echo"]
    for agent, agent_id in agent_ids.items():
        if agent == "Echo":
            continue

        builder.add_edge(echo_id, agent_id, "relates_to", 5, "state")
        builder.add_edge(agent_id, echo_id, "belongs_to", 5, "state")

    return agent_ids


def _add_state_nodes(builder, state, agent_ids):

    state = state if isinstance(state, dict) else {}
    nodes = {
        "top_priority": None,
        "dominant_theme": None,
        "portfolio_risk": None,
        "macro_regime": None,
        "news_narrative": None,
        "risks": [],
        "actions": []
    }

    top_priority = _title(state.get("top_priority"))
    if top_priority:
        nodes["top_priority"] = builder.add_node(
            "priority",
            top_priority,
            "state",
            25,
            state.get("top_priority") or {}
        )

    dominant_theme = _title(state.get("dominant_theme"))
    if dominant_theme:
        nodes["dominant_theme"] = builder.add_node(
            "theme",
            dominant_theme,
            "state",
            25,
            state.get("dominant_theme") or {}
        )

    portfolio = state.get("portfolio") or {}
    portfolio_risk = _title(portfolio.get("current_risk"))
    if portfolio_risk:
        nodes["portfolio_risk"] = builder.add_node(
            "risk",
            portfolio_risk,
            "state",
            10,
            portfolio.get("current_risk") or {}
        )
        nodes["risks"].append(nodes["portfolio_risk"])

    stress = _title(portfolio.get("worst_stress_scenario"))
    if stress:
        stress_id = builder.add_node(
            "stress_scenario",
            stress,
            "state",
            10,
            portfolio.get("worst_stress_scenario") or {}
        )
        builder.add_edge(
            stress_id,
            agent_ids["Portfolio Agent"],
            "relates_to",
            7,
            "state"
        )

    for flag in portfolio.get("concentration_flags") or []:
        label = _title(flag)
        node_type = "holding" if isinstance(flag, dict) and flag.get("ticker") else "risk"
        flag_id = builder.add_node(node_type, label, "state", 10, flag)
        if flag_id:
            builder.add_edge(
                flag_id,
                agent_ids["Portfolio Agent"],
                "relates_to",
                7,
                "state"
            )
            nodes["risks"].append(flag_id)

    for holding in portfolio.get("weak_holdings") or []:
        holding_id = builder.add_node("holding", _title(holding), "state", 10)
        if holding_id:
            builder.add_edge(
                holding_id,
                agent_ids["Portfolio Agent"],
                "relates_to",
                7,
                "state"
            )

    research = state.get("research") or {}
    for conviction in research.get("top_convictions") or []:
        signal_id = builder.add_node(
            "research_signal",
            _title(conviction),
            "state",
            10,
            conviction
        )
        if signal_id:
            builder.add_edge(
                signal_id,
                agent_ids["Research Agent"],
                "relates_to",
                7,
                "state"
            )

    for coverage in research.get("weak_coverage") or []:
        label = _title(coverage.get("area") if isinstance(coverage, dict) else coverage)
        signal_id = builder.add_node(
            "research_signal",
            label,
            "state",
            10,
            coverage
        )
        if signal_id:
            builder.add_edge(
                signal_id,
                agent_ids["Research Agent"],
                "relates_to",
                7,
                "state"
            )

    for priority in research.get("watchlist_priorities") or []:
        signal_id = builder.add_node(
            "research_signal",
            _title(priority),
            "state",
            10
        )
        if signal_id:
            builder.add_edge(
                signal_id,
                agent_ids["Research Agent"],
                "relates_to",
                7,
                "state"
            )

    news = state.get("news") or {}
    narrative = _title(news.get("top_narrative"))
    if narrative:
        nodes["news_narrative"] = builder.add_node(
            "news_narrative",
            narrative,
            "state",
            10,
            news.get("top_narrative") or {}
        )

    for item in (
        list(news.get("market_significant_items") or [])
        + list(news.get("portfolio_relevant_items") or [])
    ):
        narrative_id = builder.add_node(
            "news_narrative",
            _title(item),
            "state",
            10,
            item if isinstance(item, dict) else {}
        )
        if narrative_id:
            builder.add_edge(
                narrative_id,
                agent_ids["News Agent"],
                "relates_to",
                7,
                "state"
            )

    macro = state.get("macro") or {}
    regime = _title(macro.get("regime"))
    if regime:
        nodes["macro_regime"] = builder.add_node(
            "macro_regime",
            regime,
            "state",
            10,
            macro.get("regime") or {}
        )

    for risk in macro.get("top_macro_risks") or []:
        risk_id = builder.add_node("risk", _title(risk), "state", 10, risk)
        if risk_id:
            builder.add_edge(
                risk_id,
                agent_ids["Macro Agent"],
                "relates_to",
                7,
                "state"
            )
            nodes["risks"].append(risk_id)

    for conflict in state.get("conflicts") or []:
        risk_id = builder.add_node("risk", _title(conflict), "state", 10, conflict)
        if risk_id:
            nodes["risks"].append(risk_id)

    for action in state.get("action_queue") or []:
        action_id = builder.add_node("action", _title(action), "state", 10)
        if action_id:
            nodes["actions"].append(action_id)

    for risk in state.get("risk_register") or []:
        risk_id = builder.add_node("risk", _title(risk), "state", 10, risk)
        if risk_id:
            nodes["risks"].append(risk_id)

    for node_id in nodes["risks"]:
        builder.add_edge(
            node_id,
            agent_ids["Portfolio Agent"],
            "relates_to",
            6,
            "state"
        )

    for action_id in nodes["actions"]:
        builder.add_edge(action_id, agent_ids["Echo"], "relates_to", 5, "state")

    if nodes["news_narrative"]:
        builder.add_edge(
            nodes["news_narrative"],
            agent_ids["News Agent"],
            "relates_to",
            7,
            "state"
        )

    if nodes["macro_regime"]:
        builder.add_edge(
            nodes["macro_regime"],
            agent_ids["Macro Agent"],
            "relates_to",
            7,
            "state"
        )

    return nodes


def _add_history_nodes(builder, history, current_nodes):

    history = history if isinstance(history, dict) else {}
    persistent_risk_ids = []
    persistent_action_ids = []

    for risk in history.get("persistent_risks") or []:
        risk_id = builder.add_node("risk", _title(risk), "history", 15, risk)
        if risk_id:
            persistent_risk_ids.append(risk_id)

    for action in history.get("persistent_actions") or []:
        action_id = builder.add_node(
            "action",
            _title(action),
            "history",
            15,
            action
        )
        if action_id:
            persistent_action_ids.append(action_id)

    current_risk_ids = set(current_nodes.get("risks") or [])
    for risk_id in persistent_risk_ids:
        if risk_id in current_risk_ids:
            builder.add_edge(
                risk_id,
                risk_id,
                "appears_with",
                0,
                "history"
            )
            continue

        label = builder.nodes[risk_id]["label"]
        for current_id in current_risk_ids:
            if _overlaps(label, builder.nodes[current_id]["label"]):
                builder.add_edge(
                    risk_id,
                    current_id,
                    "appears_with",
                    8,
                    "history"
                )

    return {
        "persistent_risks": persistent_risk_ids,
        "persistent_actions": persistent_action_ids
    }


def _signal_node_type(signal):

    category = _safe_text((signal or {}).get("category")).casefold()
    signal_type = _safe_text((signal or {}).get("type")).casefold()

    if "priority" in category:
        return "priority"
    if "macro" in category:
        return "macro_regime"
    if "portfolio" in category:
        return "portfolio_signal"
    if "news" in category:
        return "news_narrative"
    if "action" in category or "action" in signal_type:
        return "action"
    if "risk" in category or "risk" in signal_type:
        return "risk"

    return "research_signal"


def _signal_agent(signal):

    category = _safe_text((signal or {}).get("category")).casefold()

    if "portfolio" in category or "risk" in category:
        return "Portfolio Agent"
    if "macro" in category:
        return "Macro Agent"
    if "news" in category:
        return "News Agent"
    if "research" in category:
        return "Research Agent"

    return "Echo"


def _add_change_detection_nodes(builder, detection, agent_ids):

    detection = detection if isinstance(detection, dict) else {}
    added = []

    for bucket in (
        "priority_signals",
        "risk_signals",
        "macro_signals",
        "portfolio_signals",
        "news_signals",
        "action_signals"
    ):
        for signal in detection.get(bucket) or []:
            label = _title(signal.get("name") if isinstance(signal, dict) else signal)
            score = _bounded_int(
                signal.get("score") if isinstance(signal, dict) else None,
                10
            )
            node_id = builder.add_node(
                _signal_node_type(signal),
                label,
                "change_detection",
                score if score > 0 else 10,
                signal
            )
            if node_id:
                added.append((node_id, signal))
                builder.add_edge(
                    node_id,
                    agent_ids[_signal_agent(signal)],
                    "generated_by",
                    6,
                    "change_detection"
                )

    escalation_names = {
        _safe_text(signal.get("name")).casefold()
        for signal in detection.get("escalations") or []
        if isinstance(signal, dict)
    }
    deescalation_names = {
        _safe_text(signal.get("name")).casefold()
        for signal in detection.get("deescalations") or []
        if isinstance(signal, dict)
    }

    for node_id, signal in added:
        label_key = _safe_text(signal.get("name")).casefold()
        relationship = None
        if label_key in escalation_names:
            relationship = "escalates"
        elif label_key in deescalation_names:
            relationship = "deescalates"

        if not relationship:
            continue

        for target_id, target in builder.nodes.items():
            if node_id == target_id:
                continue

            if target["type"] in {"risk", "action"} and _overlaps(
                target["label"],
                signal.get("name")
            ):
                builder.add_edge(
                    node_id,
                    target_id,
                    relationship,
                    abs(_bounded_int(signal.get("score"), 10)),
                    "change_detection"
                )

    return added


def _add_core_relationships(builder, current_nodes):

    top_priority = current_nodes.get("top_priority")
    dominant_theme = current_nodes.get("dominant_theme")
    portfolio_risk = current_nodes.get("portfolio_risk")
    macro_regime = current_nodes.get("macro_regime")
    news_narrative = current_nodes.get("news_narrative")

    if top_priority and dominant_theme:
        builder.add_edge(top_priority, dominant_theme, "relates_to", 12, "state")

    if top_priority and portfolio_risk:
        builder.add_edge(top_priority, portfolio_risk, "relates_to", 12, "state")

    if macro_regime and portfolio_risk:
        builder.add_edge(
            macro_regime,
            portfolio_risk,
            "influences",
            10,
            "state"
        )

    if news_narrative and dominant_theme:
        builder.add_edge(
            news_narrative,
            dominant_theme,
            "influences",
            10,
            "state"
        )

    for action_id in current_nodes.get("actions") or []:
        action_label = builder.nodes[action_id]["label"]

        for risk_id in current_nodes.get("risks") or []:
            risk_label = builder.nodes[risk_id]["label"]
            if _overlaps(action_label, risk_label):
                builder.add_edge(
                    action_id,
                    risk_id,
                    "relates_to",
                    8,
                    "state"
                )


def _entity_index(nodes):

    index = defaultdict(list)

    for node in nodes:
        key = normalize_entity_id(node.get("label"))
        if node["id"] not in index[key]:
            index[key].append(node["id"])

    return dict(sorted(index.items()))


def _relationship_index(edges):

    index = defaultdict(list)

    for position, edge in enumerate(edges):
        index[edge["relationship"]].append({
            "id": f"edge:{position + 1}",
            "source": edge["source"],
            "target": edge["target"],
            "weight": edge["weight"],
            "source_layer": edge["source_layer"]
        })

    return dict(sorted(index.items()))


def _clusters(nodes, edges):

    labels = {node["id"]: node for node in nodes}
    graph = defaultdict(set)

    for edge in edges:
        graph[edge["source"]].add(edge["target"])
        graph[edge["target"]].add(edge["source"])

    clusters = []
    seen = set()

    for node in nodes:
        node_id = node["id"]
        if node_id in seen:
            continue

        queue = deque([node_id])
        component = []
        seen.add(node_id)

        while queue:
            current = queue.popleft()
            component.append(current)

            for neighbor in sorted(graph[current]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        component_nodes = [labels[item] for item in component if item in labels]
        primary = max(
            component_nodes,
            key=lambda item: (item.get("weight", 0), item.get("label", "")),
            default=None
        )
        cluster_id = f"cluster:{len(clusters) + 1}"
        clusters.append({
            "id": cluster_id,
            "label": primary["label"] if primary else cluster_id,
            "node_ids": sorted(component),
            "total_weight": sum(node.get("weight", 0) for node in component_nodes),
            "primary_node": primary["id"] if primary else None
        })

    return sorted(
        clusters,
        key=lambda cluster: (-cluster["total_weight"], cluster["id"])
    )


def _top_connected(nodes, edges, limit=10):

    degree = Counter()

    for edge in edges:
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1

    by_id = {node["id"]: node for node in nodes}
    rows = []

    for node_id, count in degree.items():
        node = by_id.get(node_id)
        if node:
            rows.append({
                "id": node_id,
                "label": node["label"],
                "type": node["type"],
                "degree": count,
                "weight": node["weight"]
            })

    return sorted(
        rows,
        key=lambda row: (-row["degree"], -row["weight"], row["label"])
    )[:limit]


def build_echo_knowledge_graph(current_state, state_delta, state_history,
                               change_detection):

    builder = _GraphBuilder()
    agent_ids = _add_agent_nodes(builder)
    current_nodes = _add_state_nodes(builder, current_state, agent_ids)
    _add_history_nodes(builder, state_history, current_nodes)
    _add_change_detection_nodes(builder, change_detection, agent_ids)
    _add_core_relationships(builder, current_nodes)

    nodes = sorted(
        builder.nodes.values(),
        key=lambda node: (node["type"], node["label"].casefold(), node["id"])
    )
    edges = sorted(
        builder.edges.values(),
        key=lambda edge: (
            edge["source"],
            edge["target"],
            edge["relationship"],
            edge["source_layer"]
        )
    )
    clusters = _clusters(nodes, edges)
    top_connected = _top_connected(nodes, edges)
    dominant_cluster = clusters[0]["id"] if clusters else None

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "top_connected_nodes": top_connected,
            "dominant_cluster": dominant_cluster
        },
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "entity_index": _entity_index(nodes),
        "relationship_index": _relationship_index(edges)
    }


def render_knowledge_graph_text(graph):

    graph = graph if isinstance(graph, dict) else {}
    summary = graph.get("summary") or {}
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    clusters = graph.get("clusters") or []
    node_by_id = {node.get("id"): node for node in nodes}
    dominant = next(
        (
            cluster for cluster in clusters
            if cluster.get("id") == summary.get("dominant_cluster")
        ),
        None
    )
    agent_degrees = Counter()

    for edge in edges:
        for endpoint in (edge.get("source"), edge.get("target")):
            node = node_by_id.get(endpoint)
            if node and node.get("type") == "agent":
                agent_degrees[node.get("label")] += 1

    linked_edges = [
        edge for edge in edges
        if (
            node_by_id.get(edge.get("source"), {}).get("type")
            in {"risk", "theme", "action", "priority"}
            or node_by_id.get(edge.get("target"), {}).get("type")
            in {"risk", "theme", "action", "priority"}
        )
    ]
    lines = [
        "ECHO KNOWLEDGE GRAPH",
        "====================",
        "",
        f"Schema Version: {graph.get('schema_version') or 'unknown'}",
        f"Generated At: {graph.get('generated_at') or 'unknown'}",
        f"Node Count: {summary.get('node_count') or 0}",
        f"Edge Count: {summary.get('edge_count') or 0}",
        "",
        "Most Connected Entities:"
    ]

    top_nodes = summary.get("top_connected_nodes") or []
    if top_nodes:
        lines.extend(
            (
                f"- {node.get('label')} ({node.get('type')}, "
                f"degree {node.get('degree')}, weight {node.get('weight')})"
            )
            for node in top_nodes[:10]
        )
    else:
        lines.append("None")

    lines.extend(["", "Dominant Cluster:"])
    if dominant:
        primary = node_by_id.get(dominant.get("primary_node"), {})
        lines.extend([
            f"Cluster: {dominant.get('label')}",
            f"Primary Node: {primary.get('label') or 'None'}",
            f"Total Weight: {dominant.get('total_weight') or 0}",
            f"Node Count: {len(dominant.get('node_ids') or [])}"
        ])
    else:
        lines.append("None")

    lines.extend(["", "Linked Risks, Themes, And Actions:"])
    if linked_edges:
        for edge in linked_edges[:15]:
            source = node_by_id.get(edge.get("source"), {})
            target = node_by_id.get(edge.get("target"), {})
            lines.append(
                f"- {source.get('label') or edge.get('source')} "
                f"{edge.get('relationship')} "
                f"{target.get('label') or edge.get('target')} "
                f"(weight {edge.get('weight')})"
            )
    else:
        lines.append("None")

    lines.extend(["", "Agent Connectivity:"])
    if agent_degrees:
        for agent, degree in sorted(
            agent_degrees.items(),
            key=lambda item: (-item[1], item[0])
        ):
            lines.append(f"- {agent}: {degree} connected edges")
    else:
        lines.append("None")

    return "\n".join(lines) + "\n"


def write_knowledge_graph_json(graph, path=None):

    path = Path(path) if path else KNOWLEDGE_GRAPH_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(graph, indent=2, sort_keys=True),
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


def write_knowledge_graph_text(graph, path=None):

    path = Path(path) if path else KNOWLEDGE_GRAPH_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_knowledge_graph_text(graph), encoding="utf-8")
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


def read_knowledge_graph(path=None):

    path = Path(path) if path else KNOWLEDGE_GRAPH_JSON_PATH

    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return build_echo_knowledge_graph({}, {}, {}, {})

    return (
        graph
        if isinstance(graph, dict)
        else build_echo_knowledge_graph({}, {}, {}, {})
    )
