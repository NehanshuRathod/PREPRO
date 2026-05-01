from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic_behavior.csv"


FEATURES = [
    "avg_decision_time",
    "risk_score",
    "exploration_score",
    "curiosity_score",
    "information_score",
    "time_pressure_efficiency",
    "decision_consistency",
    "decision_variance",
    "risk_shift_over_time",
    "hint_dependency_curve",
    "exploration_depth",
    "pressure_success_rate",
    "option_entropy",
    "timeout_rate",
    "path_unlock_rate",
    "event_count",
]


def clamp_score(value: float) -> float:
    return round(max(1.0, min(10.0, value)), 2)


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def main() -> None:
    random.seed(101)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for index in range(1800):
        avg_decision_time = round(random.uniform(1.0, 11.5), 3)
        risk_score = round(random.betavariate(2.2, 2.4), 3)
        exploration_score = round(random.betavariate(2.0, 2.1), 3)
        curiosity_score = round(random.betavariate(2.0, 2.0), 3)
        information_score = round(clamp01(curiosity_score * 0.45 + random.random() * 0.55), 3)
        timeout_rate = round(random.betavariate(1.3, 5.5), 3)
        pressure_success_rate = round(clamp01(random.betavariate(2.4, 1.8) - timeout_rate * 0.35), 3)
        time_pressure_efficiency = round(
            clamp01((1.0 - avg_decision_time / 13.0) * 0.45 + pressure_success_rate * 0.45 + information_score * 0.1),
            3,
        )
        decision_variance = round(random.betavariate(1.4, 4.5), 3)
        decision_consistency = round(clamp01(1.0 - decision_variance + random.uniform(-0.08, 0.08)), 3)
        risk_shift_over_time = round(random.uniform(-0.55, 0.55), 3)
        hint_dependency_curve = round(random.uniform(-0.35, 0.65), 3)
        path_unlock_rate = round(random.betavariate(1.7, 4.0), 3)
        exploration_depth = round(clamp01(exploration_score * 0.65 + path_unlock_rate * 0.35), 3)
        option_entropy = round(random.betavariate(3.0, 1.8), 3)
        event_count = random.randint(10, 24)

        confidence = clamp_score(
            3.5
            + time_pressure_efficiency * 4.1
            + pressure_success_rate * 1.25
            + decision_consistency * 1.2
            - timeout_rate * 2.1
            - max(0.0, avg_decision_time - 8.0) * 0.12
            + random.gauss(0, 0.45)
        )
        curiosity = clamp_score(
            3.0
            + curiosity_score * 3.3
            + information_score * 1.7
            + max(0.0, hint_dependency_curve) * 0.55
            - max(0.0, hint_dependency_curve - 0.45) * 1.0
            + random.gauss(0, 0.48)
        )
        emotional_safety = clamp_score(
            3.7
            + (1.0 - abs(risk_score - 0.45) * 1.75) * 2.55
            + decision_consistency * 1.1
            + pressure_success_rate * 0.75
            - timeout_rate * 1.55
            - max(0.0, risk_shift_over_time - 0.35) * 1.1
            + random.gauss(0, 0.48)
        )
        exploratory_power = clamp_score(
            2.6
            + exploration_score * 3.0
            + exploration_depth * 2.0
            + path_unlock_rate * 1.1
            + option_entropy * 0.85
            + random.gauss(0, 0.42)
        )

        feature_values = {
            "avg_decision_time": avg_decision_time,
            "risk_score": risk_score,
            "exploration_score": exploration_score,
            "curiosity_score": curiosity_score,
            "information_score": information_score,
            "time_pressure_efficiency": time_pressure_efficiency,
            "decision_consistency": decision_consistency,
            "decision_variance": decision_variance,
            "risk_shift_over_time": risk_shift_over_time,
            "hint_dependency_curve": hint_dependency_curve,
            "exploration_depth": exploration_depth,
            "pressure_success_rate": pressure_success_rate,
            "option_entropy": option_entropy,
            "timeout_rate": timeout_rate,
            "path_unlock_rate": path_unlock_rate,
            "event_count": event_count,
        }
        row = {
            "user_id": f"TCBIS{index:04d}",
            "confidence": confidence,
            "curiosity": curiosity,
            "emotional_safety": emotional_safety,
            "exploratory_power": exploratory_power,
        }
        row.update(feature_values)
        rows.append(row)

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["user_id", *FEATURES, "confidence", "curiosity", "emotional_safety", "exploratory_power"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
