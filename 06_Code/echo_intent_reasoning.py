from datetime import datetime
import json
from pathlib import Path
import re


REPORTS_DIR = Path(__file__).resolve().parent.parent / "04_Reports"
INTENT_REASONING_JSON_PATH = REPORTS_DIR / "echo_intent_reasoning.json"
INTENT_REASONING_TEXT_PATH = REPORTS_DIR / "echo_intent_reasoning.txt"

INTENT_VALUES = {
    "retrieval",
    "explanation",
    "scenario_analysis",
    "critique",
    "prioritization",
    "recommendation",
    "conversation",
    "unknown"
}

KNOWN_ENTITIES = {
    "portfolio",
    "macro",
    "inflation",
    "energy",
    "rates",
    "rate",
    "fed",
    "UNH",
    "SMCI",
    "IBIT"
}

NON_ENTITY_TOKENS = {
    "AI",
    "API",
    "CPI",
    "ETF",
    "ECHO",
    "FED",
    "GDP",
    "LLM",
    "OK",
    "US",
    "USA"
}

INTENT_INSTRUCTIONS = {
    "retrieval": [
        "Answer directly from Echo context.",
        "Prioritize current state, latest priority, and relevant facts.",
        "Do not over-explain unless the user asks why."
    ],
    "explanation": [
        "Explain causal drivers.",
        "Distinguish direct evidence from inference.",
        "Tie answer back to Echo context.",
        "Do not merely restate stored labels."
    ],
    "scenario_analysis": [
        "Estimate first-order impact using available portfolio concentration data.",
        "Discuss second-order consequences.",
        "Identify assumptions explicitly.",
        "Avoid pretending to know exact future outcomes.",
        "Tie scenario back to current risks and priorities."
    ],
    "critique": [
        "Identify weaknesses, blind spots, and asymmetric risks.",
        "Be direct.",
        "Distinguish confirmed data from judgment."
    ],
    "prioritization": [
        "Rank what matters by urgency, impact, and actionability.",
        "Explain why the ordering matters.",
        "Keep the answer decision-useful."
    ],
    "recommendation": [
        "Provide prioritized next steps.",
        "Avoid pretending to give financial advice beyond Echo's analytical context.",
        "Frame as decision support."
    ],
    "conversation": [
        "Respond naturally and briefly unless the user asks for analysis."
    ],
    "unknown": [
        "Answer from available Echo context if possible.",
        "Say what context is missing if the query cannot be answered."
    ]
}


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _safe_text(value):

    return " ".join(str(value or "").split())


def _tokens(text):

    return set(re.findall(r"[A-Za-z][A-Za-z0-9.]{1,10}", _safe_text(text)))


def _lower(text):

    return _safe_text(text).casefold()


def _has_phrase(text, phrases):

    lowered = _lower(text)
    return any(str(phrase).casefold() in lowered for phrase in phrases)


def _dict(value):

    return value if isinstance(value, dict) else {}


def _list(value):

    return value if isinstance(value, list) else []


def _detect_entities(user_query, memory_context=None, context_assembly=None):

    entities = []
    lowered = _lower(user_query)

    for entity in sorted(KNOWN_ENTITIES, key=str.casefold):
        if entity.casefold() in lowered:
            label = "rates" if entity == "rate" else entity

            if label not in entities:
                entities.append(label)

    for token in _tokens(user_query):
        if (
            token.isupper()
            and len(token) <= 5
            and token not in NON_ENTITY_TOKENS
            and token not in entities
        ):
            entities.append(token)

    for source in (
        _dict(memory_context).get("summary"),
        _dict(_dict(memory_context).get("operating_context")).get(
            "current_state"
        ),
        _dict(context_assembly).get("context_blocks")
    ):
        text = json.dumps(source, default=str) if source else ""

        for token in _tokens(user_query):
            if token.isupper() and token in text and token not in entities:
                entities.append(token)

    return entities


def _detect_horizon(user_query):

    text = _lower(user_query)

    for phrase in (
        "tomorrow",
        "next week",
        "this week",
        "next month",
        "next quarter",
        "next year",
        "1 year",
        "one year",
        "next 12 months",
        "12 months"
    ):
        if phrase in text:
            return phrase

    match = re.search(
        r"\b(?:next|over\s+the\s+next)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b",
        text
    )

    if match:
        return f"next {match.group(1)} {match.group(2)}"

    return None


def _classify_intent(user_query, context_budget=None):

    text = _lower(user_query)
    query_class = _dict(context_budget).get("query_class")

    if query_class == "conversational" or _has_phrase(text, (
        "good morning",
        "good afternoon",
        "good evening",
        "joke",
        "make me laugh"
    )) or text.strip(" ?!.") in {
        "hi",
        "hello",
        "hey",
        "thanks",
        "thank you"
    }:
        return "conversation", "light", "conversational", "Casual prompt."

    if _has_phrase(text, (
        "challenge",
        "underestimating",
        "where am i wrong",
        "blind spot",
        "blindspot",
        "strongest counterargument",
        "weakness"
    )):
        return "critique", "deep", "challenge", "Critique wording detected."

    if _has_phrase(text, (
        "what should i do",
        "next step",
        "recommend",
        "action plan",
        "how should i respond",
        "what would you do"
    )):
        return (
            "recommendation",
            "moderate",
            "analytical",
            "Recommendation framing detected."
        )

    if _has_phrase(text, (
        "what should i focus on",
        "what matters most",
        "highest leverage",
        "rank",
        "order of importance",
        "attention"
    )):
        return (
            "prioritization",
            "moderate",
            "executive",
            "Prioritization wording detected."
        )

    if _has_phrase(text, (
        "what happens if",
        "what would happen if",
        "if ",
        "scenario",
        "fell",
        "dropped",
        "rose",
        "shock",
        "stress",
        "consequences",
        "impact",
        "downside",
        "upside",
        "over next",
        "over the next",
        "next 12 months"
    )):
        return (
            "scenario_analysis",
            "deep",
            "scenario",
            "Scenario or consequence wording detected."
        )

    if _has_phrase(text, (
        "why",
        "explain",
        "what is driving",
        "what caused",
        "why does this matter",
        "why is"
    )):
        return "explanation", "moderate", "analytical", "Explanation wording detected."

    if _has_phrase(text, (
        "what is",
        "current status",
        "summary",
        "top priority",
        "what changed",
        "what persists",
        "portfolio summary",
        "macro regime"
    )) or query_class in {"memory", "agent_specific", "multi_agent"}:
        return "retrieval", "light", "brief", "Retrieval/status wording detected."

    return "unknown", "none", "brief", "No deterministic reasoning intent matched."


def _required_context(intent, entities, context_budget=None, agent_routing=None):

    context = ["response_composer", "context_assembly"]
    query_class = _dict(context_budget).get("query_class")
    routed_agents = (
        _list(_dict(agent_routing).get("primary_agents"))
        + _list(_dict(agent_routing).get("secondary_agents"))
    )

    if query_class in {"memory", "conversational"} or intent in {
        "retrieval",
        "prioritization",
        "conversation"
    }:
        context.append("memory_context")

    if query_class == "portfolio_change":
        context.append("portfolio_change_detection")

    if intent in {"explanation", "scenario_analysis", "critique", "recommendation"}:
        context.extend(["memory_context", "agent_context", "current_state"])

    if any(entity in {"portfolio", "UNH", "SMCI", "IBIT"} for entity in entities):
        context.append("portfolio_context")

    if any(entity in {"macro", "inflation", "energy", "rates", "fed"} for entity in entities):
        context.append("macro_context")

    for agent in routed_agents:
        item = f"{agent}_context"

        if item not in context:
            context.append(item)

    unique_context = []

    for item in context:
        if item not in unique_context:
            unique_context.append(item)

    return unique_context


def classify_reasoning_intent(
    user_query,
    context_budget=None,
    agent_routing=None,
    context_assembly=None,
    memory_context=None
):

    query = _safe_text(user_query)
    intent, depth, style, reason = _classify_intent(query, context_budget)
    entities = _detect_entities(query, memory_context, context_assembly)
    horizon = _detect_horizon(query)
    confidence = "high" if intent != "unknown" else "low"

    if intent == "retrieval" and entities:
        confidence = "medium"

    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "query": query,
        "reasoning_intent": intent if intent in INTENT_VALUES else "unknown",
        "reasoning_depth": depth,
        "answer_style": style,
        "required_context": _required_context(
            intent,
            entities,
            context_budget,
            agent_routing
        ),
        "reasoning_instructions": list(INTENT_INSTRUCTIONS.get(
            intent,
            INTENT_INSTRUCTIONS["unknown"]
        )),
        "detected_entities": entities,
        "detected_horizon": horizon,
        "confidence": confidence,
        "reason": reason
    }


def render_intent_reasoning_text(intent_reasoning):

    intent = _dict(intent_reasoning)
    lines = [
        "ECHO INTENT REASONING",
        "=====================",
        "",
        f"Schema Version: {intent.get('schema_version') or 'unknown'}",
        f"Generated At: {intent.get('generated_at') or 'unknown'}",
        f"Query: {intent.get('query') or ''}",
        f"Reasoning Intent: {intent.get('reasoning_intent') or 'unknown'}",
        f"Reasoning Depth: {intent.get('reasoning_depth') or 'none'}",
        f"Answer Style: {intent.get('answer_style') or 'brief'}",
        f"Detected Horizon: {intent.get('detected_horizon') or 'None'}",
        f"Confidence: {intent.get('confidence') or 'low'}",
        "",
        "Detected Entities:"
    ]
    lines.extend([f"- {entity}" for entity in _list(
        intent.get("detected_entities")
    )] or ["None"])
    lines.extend(["", "Required Context:"])
    lines.extend([f"- {item}" for item in _list(
        intent.get("required_context")
    )] or ["None"])
    lines.extend(["", "Reasoning Instructions:"])
    lines.extend([f"- {item}" for item in _list(
        intent.get("reasoning_instructions")
    )] or ["None"])
    lines.extend(["", f"Reason: {intent.get('reason') or 'None'}"])

    return "\n".join(lines) + "\n"


def write_intent_reasoning_json(intent_reasoning, path=None):

    path = Path(path) if path else INTENT_REASONING_JSON_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(intent_reasoning, indent=2, sort_keys=True),
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


def write_intent_reasoning_text(intent_reasoning, path=None):

    path = Path(path) if path else INTENT_REASONING_TEXT_PATH

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_intent_reasoning_text(intent_reasoning),
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


def read_intent_reasoning(path=None):

    path = Path(path) if path else INTENT_REASONING_JSON_PATH

    try:
        intent_reasoning = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return classify_reasoning_intent("")

    return (
        intent_reasoning
        if isinstance(intent_reasoning, dict)
        else classify_reasoning_intent("")
    )
