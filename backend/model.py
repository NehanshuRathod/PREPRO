from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.feature_engineering import clamp_score, rule_based_scores


TRAITS = ["confidence", "curiosity", "emotional_safety", "exploratory_power"]
FEATURE_ORDER = [
    "avg_decision_time",
    "hint_count",
    "risk_ratio",
    "exploration_score",
    "retry_rate",
    "puzzle_success_rate",
    "hidden_discovery_ratio",
    "choice_count",
]


class BehavioralModel:
    """Prediction layer with optional XGBoost models and a no-dependency fallback."""

    def __init__(self, model_dir: str | Path = "data/models") -> None:
        self.model_dir = Path(model_dir)
        self.xgb_models: dict[str, Any] = {}
        self.mode = "fallback"
        self._load_xgboost_models()

    def _load_xgboost_models(self) -> None:
        try:
            import joblib  # type: ignore
        except Exception:
            return

        loaded: dict[str, Any] = {}
        for trait in TRAITS:
            model_path = self.model_dir / f"{trait}.joblib"
            if not model_path.exists():
                return
            loaded[trait] = joblib.load(model_path)

        self.xgb_models = loaded
        self.mode = "xgboost"

    def predict_model_scores(self, features: dict[str, float]) -> dict[str, float]:
        if self.xgb_models:
            vector = [[features[name] for name in FEATURE_ORDER]]
            return {
                trait: clamp_score(float(model.predict(vector)[0]))
                for trait, model in self.xgb_models.items()
            }

        return self._fallback_predict(features)

    def score(self, features: dict[str, float]) -> dict[str, Any]:
        model_scores = self.predict_model_scores(features)
        rule_scores = rule_based_scores(features)

        final_scores = {
            trait: clamp_score(model_scores[trait] * 0.7 + rule_scores[trait] * 0.3)
            for trait in TRAITS
        }

        return {
            "model_mode": self.mode,
            "model_scores": model_scores,
            "rule_scores": rule_scores,
            "scores": final_scores,
            "insights": build_insights(features, final_scores),
        }

    def _fallback_predict(self, features: dict[str, float]) -> dict[str, float]:
        """A deterministic boosted-rule approximation for local demos without packages."""
        avg_time = features["avg_decision_time"]
        hints = features["hint_count"]
        risk = features["risk_ratio"]
        exploration = features["exploration_score"]
        retry = features["retry_rate"]
        success = features["puzzle_success_rate"]
        hidden = features["hidden_discovery_ratio"]
        choices = features["choice_count"]

        confidence = (
            5.8
            - avg_time * 0.55
            + success * 2.6
            + min(1.0, choices / 8.0)
            - retry * 0.8
        )
        curiosity = 3.2 + hints * 0.55 + exploration * 0.19 + hidden * 1.5
        emotional_safety = 4.0 + (1 - abs(risk - 0.5) * 1.7) * 3.0 + retry * 0.35
        exploratory_power = 2.5 + exploration * 0.38 + hidden * 2.2 + min(1.0, hints * 0.12)

        return {
            "confidence": clamp_score(confidence),
            "curiosity": clamp_score(curiosity),
            "emotional_safety": clamp_score(emotional_safety),
            "exploratory_power": clamp_score(exploratory_power),
        }


def build_insights(features: dict[str, float], scores: dict[str, float]) -> list[str]:
    insights: list[str] = []

    if features["avg_decision_time"] <= 2.2:
        insights.append("Fast decisions suggest comfort acting under uncertainty.")
    elif features["avg_decision_time"] >= 4.5:
        insights.append("Longer decision times suggest a reflective, cautious style.")

    if features["hint_count"] >= 3:
        insights.append("Frequent hint use points to active information seeking.")
    elif features["hint_count"] == 0:
        insights.append("No hints were requested, suggesting independent problem solving.")

    if features["risk_ratio"] >= 0.65:
        insights.append("Risk-heavy choices show willingness to test uncertain paths.")
    elif features["risk_ratio"] <= 0.25:
        insights.append("Safe choices indicate preference for controlled outcomes.")

    if features["exploration_score"] >= 12:
        insights.append("High exploration activity strengthened exploratory power.")

    strongest = max(scores, key=scores.get)
    labels = {
        "confidence": "confidence",
        "curiosity": "curiosity",
        "emotional_safety": "emotional safety",
        "exploratory_power": "exploratory power",
    }
    insights.append(f"Strongest observed trait: {labels[strongest]}.")

    return insights


def write_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=True) + "\n")

