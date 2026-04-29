from __future__ import annotations

from collections import Counter
from typing import Any


DEFAULT_FEATURES = {
    "avg_decision_time": 3.0,
    "hint_count": 0.0,
    "risk_ratio": 0.0,
    "exploration_score": 0.0,
    "retry_rate": 0.0,
    "puzzle_success_rate": 0.0,
    "hidden_discovery_ratio": 0.0,
    "choice_count": 0.0,
}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def engineer_features(events: list[dict[str, Any]]) -> dict[str, float]:
    """Convert raw browser events into compact ML features."""
    if not events:
        return dict(DEFAULT_FEATURES)

    counts = Counter(event.get("type", "unknown") for event in events)

    decision_times = [
        max(0.05, _number(event.get("decision_time"), 0.0))
        for event in events
        if event.get("type") in {"risk_choice", "puzzle_attempt", "path_choice"}
        and event.get("decision_time") is not None
    ]

    risk_events = [
        event for event in events if event.get("type") == "risk_choice"
    ]
    risk_count = sum(1 for event in risk_events if event.get("choice") == "risk")

    puzzle_attempts = [
        event for event in events if event.get("type") == "puzzle_attempt"
    ]
    puzzle_successes = sum(1 for event in puzzle_attempts if event.get("correct"))

    explored_tiles = {
        event.get("tile")
        for event in events
        if event.get("type") == "explore_tile" and event.get("tile") is not None
    }
    hidden_tiles = {
        event.get("tile")
        for event in events
        if event.get("type") == "explore_tile" and event.get("hidden")
    }

    retry_count = counts["retry"]
    choice_count = counts["risk_choice"] + counts["path_choice"] + counts["puzzle_attempt"]

    return {
        "avg_decision_time": round(
            sum(decision_times) / len(decision_times), 3
        )
        if decision_times
        else DEFAULT_FEATURES["avg_decision_time"],
        "hint_count": float(counts["hint_request"]),
        "risk_ratio": round(risk_count / len(risk_events), 3) if risk_events else 0.0,
        "exploration_score": float(len(explored_tiles) + len(hidden_tiles) * 2),
        "retry_rate": round(retry_count / max(1, len(puzzle_attempts)), 3),
        "puzzle_success_rate": round(
            puzzle_successes / max(1, len(puzzle_attempts)), 3
        ),
        "hidden_discovery_ratio": round(len(hidden_tiles) / max(1, len(explored_tiles)), 3),
        "choice_count": float(choice_count),
    }


def rule_based_scores(features: dict[str, float]) -> dict[str, float]:
    """Transparent fallback scoring used in the hybrid score."""
    avg_time = features["avg_decision_time"]
    hint_count = features["hint_count"]
    risk_ratio = features["risk_ratio"]
    exploration = features["exploration_score"]
    retry_rate = features["retry_rate"]
    success = features["puzzle_success_rate"]
    hidden_ratio = features["hidden_discovery_ratio"]

    confidence = 5.0
    confidence += max(0.0, 3.2 - avg_time) * 1.15
    confidence += success * 2.0
    confidence -= min(2.0, retry_rate * 1.1)

    curiosity = 4.0
    curiosity += min(3.0, hint_count * 0.65)
    curiosity += min(2.5, exploration * 0.16)
    curiosity += hidden_ratio * 1.2

    emotional_safety = 5.0
    emotional_safety += (1.0 - abs(risk_ratio - 0.45) * 2.0) * 2.0
    emotional_safety += min(1.2, retry_rate * 0.7)
    emotional_safety -= max(0.0, risk_ratio - 0.8) * 2.5

    exploratory_power = 3.0
    exploratory_power += min(4.5, exploration * 0.32)
    exploratory_power += hidden_ratio * 2.0
    exploratory_power += min(1.0, hint_count * 0.18)

    return {
        "confidence": clamp_score(confidence),
        "curiosity": clamp_score(curiosity),
        "emotional_safety": clamp_score(emotional_safety),
        "exploratory_power": clamp_score(exploratory_power),
    }


def clamp_score(value: float) -> float:
    return round(max(1.0, min(10.0, value)), 1)

