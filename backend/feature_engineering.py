from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev
from typing import Any


DEFAULT_FEATURES = {
    "avg_decision_time": 3.0,
    "hint_count": 0.0,
    "hint_dependency": 0.0,
    "risk_ratio": 0.0,
    "exploration_score": 0.0,
    "retry_rate": 0.0,
    "puzzle_success_rate": 0.0,
    "hidden_discovery_ratio": 0.0,
    "choice_count": 0.0,
    "confidence_wager_avg": 0.0,
    "confidence_wager_variance": 0.0,
    "resource_efficiency": 0.0,
    "recovery_index": 0.0,
    "pattern_switch_rate": 0.0,
    "information_gain": 0.0,
    "event_count": 0.0,
}


DECISION_EVENT_TYPES = {
    "risk_choice",
    "puzzle_attempt",
    "path_choice",
    "resource_allocation",
    "confidence_wager",
    "signal_choice",
    "stability_choice",
}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def engineer_features(events: list[dict[str, Any]]) -> dict[str, float]:
    """Convert raw browser events into ML-ready behavioral features."""
    if not events:
        return dict(DEFAULT_FEATURES)

    counts = Counter(event.get("type", "unknown") for event in events)
    decision_times = [
        max(0.05, _number(event.get("decision_time"), 0.0))
        for event in events
        if event.get("type") in DECISION_EVENT_TYPES
        and event.get("decision_time") is not None
    ]

    risk_events = [event for event in events if event.get("type") == "risk_choice"]
    risk_levels = [
        max(0.0, min(1.0, _number(event.get("risk_level"), -1.0)))
        for event in risk_events
        if event.get("risk_level") is not None
    ]
    risk_count = sum(1 for event in risk_events if event.get("choice") == "risk")

    puzzle_attempts = [event for event in events if event.get("type") == "puzzle_attempt"]
    puzzle_successes = sum(1 for event in puzzle_attempts if event.get("correct"))
    retry_count = counts["retry"]

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

    wagers = [
        max(0.0, min(10.0, _number(event.get("wager"), 0.0)))
        for event in events
        if event.get("type") == "confidence_wager"
    ]

    allocation_events = [
        event for event in events if event.get("type") == "resource_allocation"
    ]
    energy_spent = sum(_number(event.get("energy_spent"), 0.0) for event in allocation_events)
    clue_value = sum(_number(event.get("clue_value"), 0.0) for event in allocation_events)

    pattern_labels = [
        str(event.get("pattern"))
        for event in events
        if event.get("pattern") is not None
        and event.get("type") in {"risk_choice", "path_choice", "signal_choice"}
    ]
    switches = sum(
        1 for previous, current in zip(pattern_labels, pattern_labels[1:]) if previous != current
    )

    choice_count = (
        counts["risk_choice"]
        + counts["path_choice"]
        + counts["puzzle_attempt"]
        + counts["signal_choice"]
        + counts["confidence_wager"]
    )

    information_gain = (
        len(hidden_tiles) * 2.2
        + len(explored_tiles) * 0.35
        + counts["hint_request"] * 0.7
        + clue_value * 0.45
    )
    success_rate = puzzle_successes / max(1, len(puzzle_attempts))
    retry_rate = retry_count / max(1, len(puzzle_attempts))
    recovery_index = success_rate * (1.0 if retry_count else 0.65) + min(0.35, retry_count * 0.08)

    return {
        "avg_decision_time": round(mean(decision_times), 3)
        if decision_times
        else DEFAULT_FEATURES["avg_decision_time"],
        "hint_count": float(counts["hint_request"]),
        "hint_dependency": round(counts["hint_request"] / max(1, choice_count), 3),
        "risk_ratio": round(mean(risk_levels), 3)
        if risk_levels
        else round(risk_count / len(risk_events), 3)
        if risk_events
        else 0.0,
        "exploration_score": float(len(explored_tiles) + len(hidden_tiles) * 2),
        "retry_rate": round(retry_rate, 3),
        "puzzle_success_rate": round(success_rate, 3),
        "hidden_discovery_ratio": round(len(hidden_tiles) / max(1, len(explored_tiles)), 3),
        "choice_count": float(choice_count),
        "confidence_wager_avg": round(mean(wagers), 3) if wagers else 0.0,
        "confidence_wager_variance": round(pstdev(wagers), 3) if len(wagers) > 1 else 0.0,
        "resource_efficiency": round(clue_value / max(1.0, energy_spent), 3),
        "recovery_index": round(min(1.0, recovery_index), 3),
        "pattern_switch_rate": round(switches / max(1, len(pattern_labels) - 1), 3),
        "information_gain": round(information_gain, 3),
        "event_count": float(len(events)),
    }


def rule_based_scores(features: dict[str, float]) -> dict[str, float]:
    """Transparent score used in the hybrid output and final explanation."""
    avg_time = features["avg_decision_time"]
    hint_count = features["hint_count"]
    hint_dependency = features["hint_dependency"]
    risk_ratio = features["risk_ratio"]
    exploration = features["exploration_score"]
    retry_rate = features["retry_rate"]
    success = features["puzzle_success_rate"]
    hidden_ratio = features["hidden_discovery_ratio"]
    wager_avg = features["confidence_wager_avg"]
    wager_variance = features["confidence_wager_variance"]
    efficiency = features["resource_efficiency"]
    recovery = features["recovery_index"]
    switch_rate = features["pattern_switch_rate"]
    information_gain = features["information_gain"]

    confidence = 4.2
    confidence += max(0.0, 3.4 - avg_time) * 0.95
    confidence += success * 2.0
    confidence += min(1.5, wager_avg * 0.18)
    confidence += min(1.0, efficiency * 0.55)
    confidence -= min(2.0, retry_rate * 1.05)

    curiosity = 3.2
    curiosity += min(2.4, hint_count * 0.42)
    curiosity += min(2.7, exploration * 0.13)
    curiosity += hidden_ratio * 1.25
    curiosity += min(1.4, information_gain * 0.09)
    curiosity -= max(0.0, hint_dependency - 0.7) * 1.3

    emotional_safety = 4.0
    emotional_safety += (1.0 - abs(risk_ratio - 0.45) * 1.7) * 2.4
    emotional_safety += recovery * 1.35
    emotional_safety += min(1.0, efficiency * 0.45)
    emotional_safety -= max(0.0, wager_variance - 2.2) * 0.35

    exploratory_power = 2.7
    exploratory_power += min(4.0, exploration * 0.24)
    exploratory_power += hidden_ratio * 1.55
    exploratory_power += min(1.5, information_gain * 0.1)
    exploratory_power += min(0.8, switch_rate * 0.8)

    return {
        "confidence": clamp_score(confidence),
        "curiosity": clamp_score(curiosity),
        "emotional_safety": clamp_score(emotional_safety),
        "exploratory_power": clamp_score(exploratory_power),
    }


def clamp_score(value: float) -> float:
    return round(max(1.0, min(10.0, value)), 1)
