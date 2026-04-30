from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.feature_engineering import clamp_score, rule_based_scores


TRAITS = ["confidence", "curiosity", "emotional_safety", "exploratory_power"]
FEATURE_ORDER = [
    "avg_decision_time",
    "hint_count",
    "hint_dependency",
    "risk_ratio",
    "exploration_score",
    "retry_rate",
    "puzzle_success_rate",
    "hidden_discovery_ratio",
    "choice_count",
    "confidence_wager_avg",
    "confidence_wager_variance",
    "resource_efficiency",
    "recovery_index",
    "pattern_switch_rate",
    "information_gain",
    "event_count",
]

TRAIT_LABELS = {
    "confidence": "Confidence",
    "curiosity": "Curiosity",
    "emotional_safety": "Emotional Safety",
    "exploratory_power": "Exploratory Power",
}


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
            model = joblib.load(model_path)
            expected_features = getattr(model, "n_features_in_", len(FEATURE_ORDER))
            if int(expected_features) != len(FEATURE_ORDER):
                return
            loaded[trait] = model

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
            trait: clamp_score(model_scores[trait] * 0.72 + rule_scores[trait] * 0.28)
            for trait in TRAITS
        }
        report = build_report(features, final_scores, model_scores, rule_scores)

        return {
            "model_mode": self.mode,
            "model_scores": model_scores,
            "rule_scores": rule_scores,
            "scores": final_scores,
            "report": report,
            "insights": report["insights"],
            "feature_importance": self.feature_importance(),
        }

    def feature_importance(self) -> dict[str, list[dict[str, float | str]]]:
        if not self.xgb_models:
            return {}

        importance: dict[str, list[dict[str, float | str]]] = {}
        for trait, model in self.xgb_models.items():
            values = getattr(model, "feature_importances_", [])
            ranked = sorted(
                zip(FEATURE_ORDER, values),
                key=lambda item: float(item[1]),
                reverse=True,
            )[:5]
            importance[trait] = [
                {"feature": feature, "importance": round(float(value), 3)}
                for feature, value in ranked
            ]
        return importance

    def _fallback_predict(self, features: dict[str, float]) -> dict[str, float]:
        avg_time = features["avg_decision_time"]
        hints = features["hint_count"]
        hint_dependency = features["hint_dependency"]
        risk = features["risk_ratio"]
        exploration = features["exploration_score"]
        retry = features["retry_rate"]
        success = features["puzzle_success_rate"]
        hidden = features["hidden_discovery_ratio"]
        wager = features["confidence_wager_avg"]
        efficiency = features["resource_efficiency"]
        recovery = features["recovery_index"]
        information = features["information_gain"]

        confidence = 4.4 - avg_time * 0.35 + success * 2.5 + wager * 0.2 + efficiency * 0.55 - retry * 0.8
        curiosity = 3.0 + hints * 0.4 + exploration * 0.17 + hidden * 1.4 + information * 0.08 - hint_dependency
        emotional_safety = 3.9 + (1 - abs(risk - 0.45) * 1.6) * 2.7 + recovery * 1.3 + efficiency * 0.35
        exploratory_power = 2.4 + exploration * 0.28 + hidden * 1.8 + information * 0.1

        return {
            "confidence": clamp_score(confidence),
            "curiosity": clamp_score(curiosity),
            "emotional_safety": clamp_score(emotional_safety),
            "exploratory_power": clamp_score(exploratory_power),
        }


def build_report(
    features: dict[str, float],
    scores: dict[str, float],
    model_scores: dict[str, float],
    rule_scores: dict[str, float],
) -> dict[str, Any]:
    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)
    reliability = assessment_reliability(features)
    profile = profile_name(scores, features)
    confidence_gap = round(
        sum(abs(model_scores[trait] - rule_scores[trait]) for trait in TRAITS) / len(TRAITS),
        2,
    )

    return {
        "profile": profile,
        "headline": build_headline(profile, strongest, weakest),
        "reliability": reliability,
        "confidence_gap": confidence_gap,
        "trait_explanations": trait_explanations(features, scores),
        "evidence": build_evidence(features),
        "recommendations": recommendations(scores, features),
        "insights": build_insights(features, scores),
    }


def assessment_reliability(features: dict[str, float]) -> dict[str, Any]:
    coverage = 0.0
    coverage += min(1.0, features["event_count"] / 18.0) * 0.3
    coverage += min(1.0, features["choice_count"] / 8.0) * 0.25
    coverage += min(1.0, features["exploration_score"] / 14.0) * 0.2
    coverage += min(1.0, features["information_gain"] / 12.0) * 0.15
    coverage += min(1.0, features["confidence_wager_avg"] / 6.0) * 0.1
    value = round(coverage * 100)
    level = "High" if value >= 75 else "Medium" if value >= 52 else "Low"
    return {
        "level": level,
        "score": value,
        "note": "More varied actions produce a more reliable behavioral signature.",
    }


def profile_name(scores: dict[str, float], features: dict[str, float]) -> str:
    if scores["curiosity"] >= 7.5 and scores["exploratory_power"] >= 7.5:
        return "Deep Explorer"
    if scores["confidence"] >= 7.2 and scores["emotional_safety"] >= 7.0:
        return "Steady Decider"
    if scores["confidence"] >= 7.4 and features["risk_ratio"] >= 0.65:
        return "Bold Pathfinder"
    if scores["emotional_safety"] >= 7.2 and scores["curiosity"] < 6.2:
        return "Careful Stabilizer"
    if features["hint_dependency"] >= 0.55 and scores["curiosity"] >= 6.5:
        return "Guided Investigator"
    return "Adaptive Problem Solver"


def build_headline(profile: str, strongest: str, weakest: str) -> str:
    return (
        f"{profile}: strongest signal is {TRAIT_LABELS[strongest].lower()}, "
        f"with {TRAIT_LABELS[weakest].lower()} as the main growth area."
    )


def trait_explanations(features: dict[str, float], scores: dict[str, float]) -> dict[str, str]:
    return {
        "confidence": (
            "Raised by fast choices, successful puzzle handling, and larger confidence wagers. "
            f"Your average decision time was {features['avg_decision_time']}s and wager average was {features['confidence_wager_avg']}/10."
        ),
        "curiosity": (
            "Raised by voluntary exploration, information seeking, and hidden discoveries. "
            f"Information gain reached {features['information_gain']} with hint dependency at {features['hint_dependency']}."
        ),
        "emotional_safety": (
            "Raised by balanced risk, recovery after friction, and stable resource choices. "
            f"Risk ratio was {features['risk_ratio']} and recovery index was {features['recovery_index']}."
        ),
        "exploratory_power": (
            "Raised by map coverage, hidden-zone discovery, and switching strategies when evidence changed. "
            f"Exploration score was {features['exploration_score']} with switch rate {features['pattern_switch_rate']}."
        ),
    }


def build_evidence(features: dict[str, float]) -> list[dict[str, str | float]]:
    return [
        {"label": "Decision Tempo", "value": features["avg_decision_time"], "unit": "sec"},
        {"label": "Information Gain", "value": features["information_gain"], "unit": "pts"},
        {"label": "Risk Balance", "value": features["risk_ratio"], "unit": "ratio"},
        {"label": "Recovery", "value": features["recovery_index"], "unit": "index"},
        {"label": "Resource Efficiency", "value": features["resource_efficiency"], "unit": "gain/energy"},
        {"label": "Hidden Discovery", "value": features["hidden_discovery_ratio"], "unit": "ratio"},
    ]


def recommendations(scores: dict[str, float], features: dict[str, float]) -> list[str]:
    items: list[str] = []
    if scores["confidence"] < 6.5:
        items.append("Use smaller early wagers, then increase commitment after one successful signal.")
    if scores["curiosity"] < 6.5:
        items.append("Explore at least two optional branches before locking a route.")
    if scores["emotional_safety"] < 6.5:
        items.append("Balance risk by pairing one bold move with one stabilizing move.")
    if scores["exploratory_power"] < 6.5:
        items.append("Search for hidden signals before spending hints; it improves independent exploration.")
    if features["hint_dependency"] > 0.55:
        items.append("Try delaying hints until after one independent attempt.")
    if not items:
        items.append("Strong balance across the session; the next upgrade is consistency across repeated runs.")
    return items[:4]


def build_insights(features: dict[str, float], scores: dict[str, float]) -> list[str]:
    insights: list[str] = []

    if features["avg_decision_time"] <= 2.2:
        insights.append("Fast decisions suggest comfort acting under uncertainty.")
    elif features["avg_decision_time"] >= 4.5:
        insights.append("Longer decision times suggest a reflective, cautious style.")

    if features["information_gain"] >= 10:
        insights.append("You gathered enough optional evidence to support a high-information decision pattern.")
    if features["resource_efficiency"] >= 1.2:
        insights.append("Resource spending was efficient: energy converted into useful clues.")
    if features["recovery_index"] >= 0.75:
        insights.append("Recovery behavior stayed strong after friction or retries.")
    if features["hint_dependency"] >= 0.55:
        insights.append("The model detected high reliance on hints relative to independent decisions.")

    strongest = max(scores, key=scores.get)
    insights.append(f"Strongest observed trait: {TRAIT_LABELS[strongest].lower()}.")
    return insights


def write_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=True) + "\n")
