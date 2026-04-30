from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic_behavior.csv"


def clamp(value: float) -> float:
    return round(max(1.0, min(10.0, value)), 2)


def main() -> None:
    random.seed(42)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for index in range(1400):
        avg_decision_time = round(random.uniform(0.7, 7.2), 3)
        hint_count = random.randint(0, 9)
        choice_count = random.randint(4, 16)
        hint_dependency = round(hint_count / max(1, choice_count), 3)
        risk_ratio = round(random.betavariate(2.2, 2.4), 3)
        exploration_score = random.randint(1, 25)
        retry_rate = round(random.uniform(0, 1.7), 3)
        puzzle_success_rate = round(random.betavariate(2.4, 1.8), 3)
        hidden_discovery_ratio = round(random.random(), 3)
        confidence_wager_avg = round(random.uniform(0, 10), 3)
        confidence_wager_variance = round(random.uniform(0, 4.5), 3)
        resource_efficiency = round(random.uniform(0.15, 2.4), 3)
        recovery_index = round(random.betavariate(2.1, 1.8), 3)
        pattern_switch_rate = round(random.random(), 3)
        information_gain = round(
            exploration_score * 0.38
            + hidden_discovery_ratio * 4.2
            + hint_count * 0.7
            + resource_efficiency * 1.5
            + random.uniform(0, 2.2),
            3,
        )
        event_count = random.randint(12, 34)

        confidence = clamp(
            4.0
            - avg_decision_time * 0.32
            + puzzle_success_rate * 2.45
            + confidence_wager_avg * 0.21
            + resource_efficiency * 0.55
            - retry_rate * 0.7
            - max(0, confidence_wager_variance - 3.0) * 0.22
            + random.gauss(0, 0.45)
        )
        curiosity = clamp(
            2.7
            + hint_count * 0.34
            + exploration_score * 0.16
            + hidden_discovery_ratio * 1.35
            + information_gain * 0.09
            - max(0, hint_dependency - 0.65) * 1.5
            + random.gauss(0, 0.5)
        )
        emotional_safety = clamp(
            3.8
            + (1 - abs(risk_ratio - 0.45) * 1.65) * 2.55
            + recovery_index * 1.3
            + resource_efficiency * 0.42
            - max(0, confidence_wager_variance - 2.5) * 0.3
            + random.gauss(0, 0.48)
        )
        exploratory_power = clamp(
            2.2
            + exploration_score * 0.26
            + hidden_discovery_ratio * 1.65
            + information_gain * 0.1
            + pattern_switch_rate * 0.75
            + random.gauss(0, 0.5)
        )

        rows.append(
            {
                "user_id": f"SYN{index:04d}",
                "avg_decision_time": avg_decision_time,
                "hint_count": hint_count,
                "hint_dependency": hint_dependency,
                "risk_ratio": risk_ratio,
                "exploration_score": exploration_score,
                "retry_rate": retry_rate,
                "puzzle_success_rate": puzzle_success_rate,
                "hidden_discovery_ratio": hidden_discovery_ratio,
                "choice_count": choice_count,
                "confidence_wager_avg": confidence_wager_avg,
                "confidence_wager_variance": confidence_wager_variance,
                "resource_efficiency": resource_efficiency,
                "recovery_index": recovery_index,
                "pattern_switch_rate": pattern_switch_rate,
                "information_gain": information_gain,
                "event_count": event_count,
                "confidence": confidence,
                "curiosity": curiosity,
                "emotional_safety": emotional_safety,
                "exploratory_power": exploratory_power,
            }
        )

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
