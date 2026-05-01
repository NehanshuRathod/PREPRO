from __future__ import annotations

import math
from collections import Counter
from statistics import mean, pstdev
from typing import Any


DEFAULT_FEATURES = {
    "avg_decision_time": 4.0,
    "risk_score": 0.0,
    "exploration_score": 0.0,
    "curiosity_score": 0.0,
    "information_score": 0.0,
    "time_pressure_efficiency": 0.0,
    "decision_consistency": 0.0,
    "decision_variance": 0.0,
    "risk_shift_over_time": 0.0,
    "hint_dependency_curve": 0.0,
    "exploration_depth": 0.0,
    "pressure_success_rate": 0.0,
    "option_entropy": 0.0,
    "timeout_rate": 0.0,
    "path_unlock_rate": 0.0,
    "event_count": 0.0,
}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _weights(event: dict[str, Any]) -> dict[str, float]:
    raw = event.get("option_weights") or {}
    return {
        "risk": _number(raw.get("risk"), _number(event.get("risk_level"), 0.0)),
        "information": _number(raw.get("information"), _number(event.get("information"), 0.0)),
        "explore": _number(raw.get("explore"), _number(event.get("explore"), 0.0)),
        "curiosity": _number(raw.get("curiosity"), _number(event.get("curiosity"), 0.0)),
        "pressure": _number(raw.get("pressure"), 0.5),
    }


def engineer_features(events: list[dict[str, Any]]) -> dict[str, float]:
    """Convert timed weighted decision logs into TCBIS model features."""
    decision_events = [
        event
        for event in events
        if event.get("type") in {"decision", "timeout"}
        or event.get("selected_option") is not None
    ]
    if not decision_events:
        return dict(DEFAULT_FEATURES)

    weights = [_weights(event) for event in decision_events]
    time_taken = [
        max(0.0, _number(event.get("time_taken"), _number(event.get("decision_time"), 0.0)))
        for event in decision_events
    ]
    time_limits = [
        max(1.0, _number(event.get("time_limit"), 10.0))
        for event in decision_events
    ]
    time_ratios = [
        min(1.5, taken / limit) for taken, limit in zip(time_taken, time_limits)
    ]
    timed_out = [
        bool(event.get("timeout")) or event.get("selected_option") == "TIMEOUT"
        for event in decision_events
    ]
    hints = [1.0 if event.get("hint_used") or event.get("option_intent") == "hint" else 0.0 for event in decision_events]
    path_unlocks = [1.0 if event.get("path_unlocked") else 0.0 for event in decision_events]
    option_keys = [str(event.get("selected_option", "")) for event in decision_events]

    risk_values = [item["risk"] for item in weights]
    explore_values = [item["explore"] for item in weights]
    curiosity_values = [item["curiosity"] for item in weights]
    information_values = [item["information"] for item in weights]
    pressure_values = [item["pressure"] for item in weights]

    quality_values = [
        item["information"] * 0.35
        + item["explore"] * 0.25
        + item["curiosity"] * 0.2
        + (1.0 - abs(item["risk"] - 0.48)) * 0.2
        for item in weights
    ]
    pressure_efficiency_values = [
        max(0.0, 1.0 - ratio) * quality * (0.75 + pressure * 0.25)
        for ratio, quality, pressure in zip(time_ratios, quality_values, pressure_values)
    ]
    pressure_success_values = [
        1.0 if ratio <= 1.0 and quality >= 0.45 and not timeout else 0.0
        for ratio, quality, timeout in zip(time_ratios, quality_values, timed_out)
    ]

    decision_vectors = [
        item["risk"] * 0.4 + item["explore"] * 0.25 + item["curiosity"] * 0.2 + item["information"] * 0.15
        for item in weights
    ]
    variance = pstdev(decision_vectors) if len(decision_vectors) > 1 else 0.0
    consistency = max(0.0, 1.0 - variance)
    split = max(1, len(decision_events) // 2)
    first_risk = mean(risk_values[:split])
    second_risk = mean(risk_values[split:]) if risk_values[split:] else first_risk
    first_hint = mean(hints[:split])
    second_hint = mean(hints[split:]) if hints[split:] else first_hint

    return {
        "avg_decision_time": round(mean(time_taken), 3),
        "risk_score": round(mean(risk_values), 3),
        "exploration_score": round(mean(explore_values), 3),
        "curiosity_score": round(mean(curiosity_values), 3),
        "information_score": round(mean(information_values), 3),
        "time_pressure_efficiency": round(mean(pressure_efficiency_values), 3),
        "decision_consistency": round(consistency, 3),
        "decision_variance": round(variance, 3),
        "risk_shift_over_time": round(second_risk - first_risk, 3),
        "hint_dependency_curve": round(second_hint - first_hint, 3),
        "exploration_depth": round(mean(explore_values) * 0.65 + mean(path_unlocks) * 0.35, 3),
        "pressure_success_rate": round(mean(pressure_success_values), 3),
        "option_entropy": round(_option_entropy(option_keys), 3),
        "timeout_rate": round(mean(1.0 if item else 0.0 for item in timed_out), 3),
        "path_unlock_rate": round(mean(path_unlocks), 3),
        "event_count": float(len(decision_events)),
    }


def rule_based_scores(features: dict[str, float]) -> dict[str, float]:
    """Rule intelligence half of the hybrid scorer."""
    confidence = 3.8
    confidence += features["time_pressure_efficiency"] * 4.0
    confidence += features["pressure_success_rate"] * 1.5
    confidence += features["decision_consistency"] * 1.2
    confidence -= features["timeout_rate"] * 2.2
    confidence -= max(0.0, features["avg_decision_time"] - 7.0) * 0.15

    curiosity = 3.2
    curiosity += features["curiosity_score"] * 3.2
    curiosity += features["information_score"] * 1.8
    curiosity += max(0.0, features["hint_dependency_curve"]) * 0.7
    curiosity -= max(0.0, features["hint_dependency_curve"] - 0.45) * 1.2

    emotional_safety = 4.0
    emotional_safety += (1.0 - abs(features["risk_score"] - 0.45) * 1.7) * 2.5
    emotional_safety += features["decision_consistency"] * 1.2
    emotional_safety += features["pressure_success_rate"] * 0.8
    emotional_safety -= features["timeout_rate"] * 1.5
    emotional_safety -= max(0.0, features["risk_shift_over_time"] - 0.35) * 1.1

    exploratory_power = 2.8
    exploratory_power += features["exploration_score"] * 3.0
    exploratory_power += features["exploration_depth"] * 2.0
    exploratory_power += features["path_unlock_rate"] * 1.0
    exploratory_power += features["option_entropy"] * 0.9

    return {
        "confidence": clamp_score(confidence),
        "curiosity": clamp_score(curiosity),
        "emotional_safety": clamp_score(emotional_safety),
        "exploratory_power": clamp_score(exploratory_power),
    }


def _option_entropy(option_keys: list[str]) -> float:
    if not option_keys:
        return 0.0
    counts = Counter(option_keys)
    total = len(option_keys)
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log(probability, 2)
    return min(1.0, entropy / math.log(5, 2))


def clamp_score(value: float) -> float:
    return round(max(1.0, min(10.0, value)), 1)
