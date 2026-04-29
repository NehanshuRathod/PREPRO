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
    for index in range(800):
        avg_decision_time = round(random.uniform(0.8, 7.0), 3)
        hint_count = random.randint(0, 8)
        risk_ratio = round(random.random(), 3)
        exploration_score = random.randint(0, 20)
        retry_rate = round(random.uniform(0, 1.5), 3)
        puzzle_success_rate = round(random.random(), 3)
        hidden_discovery_ratio = round(random.random(), 3)
        choice_count = random.randint(2, 12)

        confidence = clamp(
            6.0
            - avg_decision_time * 0.55
            + puzzle_success_rate * 3.0
            - retry_rate * 0.9
            + random.gauss(0, 0.45)
        )
        curiosity = clamp(
            3.0
            + hint_count * 0.55
            + exploration_score * 0.18
            + hidden_discovery_ratio * 1.2
            + random.gauss(0, 0.55)
        )
        emotional_safety = clamp(
            4.5
            + (1 - abs(risk_ratio - 0.45) * 1.8) * 2.8
            + retry_rate * 0.35
            + random.gauss(0, 0.5)
        )
        exploratory_power = clamp(
            2.5
            + exploration_score * 0.34
            + hidden_discovery_ratio * 2.0
            + hint_count * 0.12
            + random.gauss(0, 0.5)
        )

        rows.append(
            {
                "user_id": f"SYN{index:04d}",
                "avg_decision_time": avg_decision_time,
                "hint_count": hint_count,
                "risk_ratio": risk_ratio,
                "exploration_score": exploration_score,
                "retry_rate": retry_rate,
                "puzzle_success_rate": puzzle_success_rate,
                "hidden_discovery_ratio": hidden_discovery_ratio,
                "choice_count": choice_count,
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

