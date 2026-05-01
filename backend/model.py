from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.feature_engineering import clamp_score, rule_based_scores


TRAITS = ["confidence", "curiosity", "emotional_safety", "exploratory_power"]
FEATURE_ORDER = [
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
            trait: clamp_score(model_scores[trait] * 0.65 + rule_scores[trait] * 0.35)
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
        confidence = (
            3.8
            + features["time_pressure_efficiency"] * 4.2
            + features["pressure_success_rate"] * 1.4
            + features["decision_consistency"] * 1.1
            - features["timeout_rate"] * 2.0
        )
        curiosity = (
            3.0
            + features["curiosity_score"] * 3.4
            + features["information_score"] * 1.7
            + max(0.0, features["hint_dependency_curve"]) * 0.6
        )
        emotional_safety = (
            3.8
            + (1.0 - abs(features["risk_score"] - 0.45) * 1.7) * 2.6
            + features["decision_consistency"] * 1.1
            - features["timeout_rate"] * 1.4
        )
        exploratory_power = (
            2.6
            + features["exploration_score"] * 3.1
            + features["exploration_depth"] * 2.1
            + features["path_unlock_rate"] * 0.9
            + features["option_entropy"] * 0.8
        )
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
    profile = profile_name(scores, features)
    confidence_gap = round(
        sum(abs(model_scores[trait] - rule_scores[trait]) for trait in TRAITS) / len(TRAITS),
        2,
    )
    return {
        "profile": profile,
        "headline": build_headline(profile, strongest, weakest),
        "reliability": assessment_reliability(features),
        "confidence_gap": confidence_gap,
        "trait_explanations": trait_explanations(features),
        "score_reasons": score_reasons(features, scores, model_scores, rule_scores),
        "evidence": build_evidence(features),
        "recommendations": recommendations(scores, features),
        "insights": build_insights(features, scores),
    }


def assessment_reliability(features: dict[str, float]) -> dict[str, Any]:
    coverage = 0.0
    coverage += min(1.0, features["event_count"] / 16.0) * 0.28
    coverage += min(1.0, features["option_entropy"] / 0.8) * 0.18
    coverage += min(1.0, features["pressure_success_rate"] / 0.75) * 0.18
    coverage += min(1.0, features["information_score"] / 0.7) * 0.15
    coverage += min(1.0, features["exploration_depth"] / 0.65) * 0.13
    coverage += (1.0 - min(1.0, features["timeout_rate"])) * 0.08
    value = round(coverage * 100)
    level = "High" if value >= 76 else "Medium" if value >= 52 else "Low"
    return {
        "level": level,
        "score": value,
        "note": "Reliability rises when decisions are varied, timed, and completed without many timeouts.",
    }


def profile_name(scores: dict[str, float], features: dict[str, float]) -> str:
    if scores["confidence"] >= 7.5 and features["time_pressure_efficiency"] >= 0.45:
        return "Pressure-Ready Decider"
    if scores["curiosity"] >= 7.4 and features["hint_dependency_curve"] <= 0.25:
        return "Independent Investigator"
    if scores["exploratory_power"] >= 7.5 and features["path_unlock_rate"] >= 0.18:
        return "Pathfinding Explorer"
    if scores["emotional_safety"] >= 7.2 and abs(features["risk_score"] - 0.45) <= 0.18:
        return "Balanced Risk Regulator"
    if features["timeout_rate"] >= 0.25:
        return "Cautious Under Pressure"
    return "Adaptive Decision Analyst"


def build_headline(profile: str, strongest: str, weakest: str) -> str:
    return (
        f"{profile}: strongest signal is {TRAIT_LABELS[strongest].lower()}, "
        f"with {TRAIT_LABELS[weakest].lower()} as the main development area."
    )


def trait_explanations(features: dict[str, float]) -> dict[str, str]:
    return {
        "confidence": (
            "Driven by fast completion, pressure efficiency, and consistent decision patterns. "
            f"Average decision time was {features['avg_decision_time']}s with pressure efficiency {features['time_pressure_efficiency']}."
        ),
        "curiosity": (
            "Driven by information value, curiosity-weighted options, and the hint trend. "
            f"Curiosity score was {features['curiosity_score']} and information score was {features['information_score']}."
        ),
        "emotional_safety": (
            "Driven by balanced risk selection, consistency, and low timeout behavior. "
            f"Risk score was {features['risk_score']} with risk shift {features['risk_shift_over_time']}."
        ),
        "exploratory_power": (
            "Driven by exploration value, path unlocks, and option diversity. "
            f"Exploration depth was {features['exploration_depth']} and option entropy was {features['option_entropy']}."
        ),
    }


def score_reasons(
    features: dict[str, float],
    scores: dict[str, float],
    model_scores: dict[str, float],
    rule_scores: dict[str, float],
) -> dict[str, list[str]]:
    return {
        "confidence": [
            f"Final {scores['confidence']}/10 = 65% XGBoost ({model_scores['confidence']}) + 35% rules ({rule_scores['confidence']}).",
            _direction(
                features["time_pressure_efficiency"],
                0.45,
                "Time-pressure efficiency supported confidence.",
                "Low time-pressure efficiency reduced confidence."
            ),
            _direction(
                features["pressure_success_rate"],
                0.65,
                "Most timed choices were completed with useful decision quality.",
                "Timed choice quality was not consistently high."
            ),
            _direction(
                1.0 - features["timeout_rate"],
                0.85,
                "Few or no timeouts protected the confidence score.",
                "Timeouts pulled the confidence score down."
            ),
        ],
        "curiosity": [
            f"Final {scores['curiosity']}/10 = 65% XGBoost ({model_scores['curiosity']}) + 35% rules ({rule_scores['curiosity']}).",
            _direction(
                features["curiosity_score"],
                0.55,
                "You selected curiosity-weighted options often enough to raise this trait.",
                "Curiosity-weighted options were selected less often."
            ),
            _direction(
                features["information_score"],
                0.58,
                "Information-rich choices improved the curiosity signal.",
                "Information value was moderate or low across choices."
            ),
            _curve_reason(features["hint_dependency_curve"]),
        ],
        "emotional_safety": [
            f"Final {scores['emotional_safety']}/10 = 65% XGBoost ({model_scores['emotional_safety']}) + 35% rules ({rule_scores['emotional_safety']}).",
            _risk_reason(features["risk_score"]),
            _direction(
                features["decision_consistency"],
                0.72,
                "Consistent decision style supported emotional safety.",
                "Decision variance made emotional safety less stable."
            ),
            _direction(
                1.0 - features["timeout_rate"],
                0.85,
                "Low timeout behavior helped emotional safety.",
                "Timeout behavior reduced emotional safety under pressure."
            ),
        ],
        "exploratory_power": [
            f"Final {scores['exploratory_power']}/10 = 65% XGBoost ({model_scores['exploratory_power']}) + 35% rules ({rule_scores['exploratory_power']}).",
            _direction(
                features["exploration_score"],
                0.55,
                "Exploration-weighted options strengthened exploratory power.",
                "Exploration-weighted options were not chosen often enough."
            ),
            _direction(
                features["exploration_depth"],
                0.55,
                "Path-unlocking and exploration depth supported this score.",
                "Exploration depth stayed limited."
            ),
            _direction(
                features["option_entropy"],
                0.72,
                "A diverse option pattern gave the model stronger evidence.",
                "Option pattern diversity was limited."
            ),
        ],
    }


def _direction(value: float, threshold: float, high: str, low: str) -> str:
    return high if value >= threshold else low


def _risk_reason(risk_score: float) -> str:
    if 0.32 <= risk_score <= 0.62:
        return "Risk stayed in the balanced zone, which supports emotional safety."
    if risk_score > 0.62:
        return "Risk was high overall, which can lower emotional safety."
    return "Risk was very low overall, suggesting caution more than emotional flexibility."


def _curve_reason(value: float) -> str:
    if value > 0.25:
        return "Hint dependence increased later in the run, showing rising guidance-seeking."
    if value < -0.15:
        return "Hint dependence dropped later in the run, showing more independent exploration."
    return "Hint dependence stayed stable across the run."


def build_evidence(features: dict[str, float]) -> list[dict[str, str | float]]:
    return [
        {"label": "Risk Score", "value": features["risk_score"], "unit": "0-1"},
        {"label": "Curiosity Score", "value": features["curiosity_score"], "unit": "0-1"},
        {"label": "Exploration Depth", "value": features["exploration_depth"], "unit": "0-1"},
        {"label": "Time Efficiency", "value": features["time_pressure_efficiency"], "unit": "0-1"},
        {"label": "Consistency", "value": features["decision_consistency"], "unit": "0-1"},
        {"label": "Timeout Rate", "value": features["timeout_rate"], "unit": "0-1"},
    ]


def recommendations(scores: dict[str, float], features: dict[str, float]) -> list[str]:
    items: list[str] = []
    if scores["confidence"] < 6.5:
        items.append("Practice faster first-pass choices, then adjust after evidence appears.")
    if scores["curiosity"] < 6.5:
        items.append("Choose information-rich options before defaulting to safe routes.")
    if scores["emotional_safety"] < 6.5:
        items.append("Keep risk near the balanced range instead of jumping from safe to extreme.")
    if scores["exploratory_power"] < 6.5:
        items.append("Use at least two path-unlocking options during the timed run.")
    if features["timeout_rate"] > 0.2:
        items.append("Reduce hesitation under tight timers; late decisions are scored as pressure loss.")
    if not items:
        items.append("Strong balanced signature; next step is repeating the run to test consistency.")
    return items[:4]


def build_insights(features: dict[str, float], scores: dict[str, float]) -> list[str]:
    insights: list[str] = []
    if features["time_pressure_efficiency"] >= 0.45:
        insights.append("You converted limited time into useful decisions efficiently.")
    if features["risk_shift_over_time"] > 0.25:
        insights.append("Risk increased over time, suggesting growing confidence or pressure response.")
    elif features["risk_shift_over_time"] < -0.25:
        insights.append("Risk decreased over time, suggesting stabilization after early uncertainty.")
    if features["hint_dependency_curve"] > 0.25:
        insights.append("Hint reliance increased in later questions.")
    if features["option_entropy"] >= 0.8:
        insights.append("Option diversity was high, giving the model a broader behavioral signal.")
    strongest = max(scores, key=scores.get)
    insights.append(f"Strongest observed trait: {TRAIT_LABELS[strongest].lower()}.")
    return insights


def write_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=True) + "\n")
