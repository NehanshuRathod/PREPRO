from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "synthetic_behavior.csv"
MODEL_DIR = ROOT / "data" / "models"

FEATURES = [
    "avg_decision_time",
    "hint_count",
    "risk_ratio",
    "exploration_score",
    "retry_rate",
    "puzzle_success_rate",
    "hidden_discovery_ratio",
    "choice_count",
]

TRAITS = ["confidence", "curiosity", "emotional_safety", "exploratory_power"]


def main() -> None:
    if not DATASET.exists():
        raise SystemExit(
            "Dataset not found. Run: python scripts/generate_synthetic_data.py"
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(DATASET)
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURES], frame[TRAITS], test_size=0.2, random_state=42
    )

    for trait in TRAITS:
        model = XGBRegressor(
            n_estimators=140,
            max_depth=4,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=42,
        )
        model.fit(x_train, y_train[trait])
        predictions = model.predict(x_test)
        mse = mean_squared_error(y_test[trait], predictions)
        r2 = r2_score(y_test[trait], predictions)
        joblib.dump(model, MODEL_DIR / f"{trait}.joblib")
        print(f"{trait}: MSE={mse:.3f} R2={r2:.3f}")

    print(f"Models saved to {MODEL_DIR}")


if __name__ == "__main__":
    main()

