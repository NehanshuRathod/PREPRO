# AI Behavioral Assessment Game

An end-to-end working prototype for an AI-driven behavioral assessment game. Users play **Unknown World Explorer**, the app logs behavior, engineers features, predicts four behavioral traits with XGBoost, and shows an evidence-backed behavioral report.

Traits:

- Confidence
- Curiosity
- Emotional Safety
- Exploratory Power

The project runs out of the box with Python's standard library. If XGBoost is installed, you can train and use real XGBoost models with the included scripts.

## Project Structure

```text
.
├── backend/
│   ├── __init__.py
│   ├── feature_engineering.py
│   ├── model.py
│   └── server.py
├── data/
│   └── .gitkeep
├── frontend/
│   ├── app.css
│   ├── app.js
│   └── index.html
├── ml/
│   └── train_xgboost.py
├── scripts/
│   └── generate_synthetic_data.py
├── requirements.txt
└── README.md
```

## Run The Working App

```bash
python backend/server.py
```

Open:

```text
http://localhost:8000
```

## What The Game Measures

The upgraded game is not just a click demo. It captures tradeoffs across five stages:

- Route risk vs stability
- Energy budget allocation
- Hidden-zone exploration
- AI hint dependence
- Confidence wagering under uncertainty
- Retry and recovery behavior
- Strategy switching after new evidence

## How It Works

1. The browser game records decisions, timing, hints, risk levels, hidden-zone exploration, resource allocation, wagers, retries, and puzzle success.
2. The backend converts raw events into behavioral features.
3. XGBoost predicts trait scores from 1 to 10.
4. The report layer adds reliability, profile type, evidence metrics, recommendations, and trait explanations.
5. Final scores combine model output and rule-based output:

```text
final_score = 0.7 * model_score + 0.3 * rule_score
```

## API Endpoints

### `GET /api/health`

Returns server and model status.

### `POST /api/score`

Scores one completed game session.

Request:

```json
{
  "user_id": "U123",
  "events": [
    {
      "type": "risk_choice",
      "choice": "risk",
      "timestamp": 1000
    }
  ]
}
```

Response:

```json
{
  "user_id": "U123",
  "features": {
    "avg_decision_time": 2.4,
    "hint_count": 3,
    "hint_dependency": 0.2,
    "risk_ratio": 0.5,
    "exploration_score": 12,
    "retry_rate": 0.25,
    "confidence_wager_avg": 7,
    "resource_efficiency": 1.4,
    "information_gain": 10.2
  },
  "scores": {
    "confidence": 7.1,
    "curiosity": 8.4,
    "emotional_safety": 6.2,
    "exploratory_power": 8.9
  },
  "report": {
    "profile": "Steady Decider",
    "headline": "Steady Decider: strongest signal is confidence, with curiosity as the main growth area.",
    "reliability": {
      "level": "High",
      "score": 82
    }
  }
}
```

## Generate Synthetic Data

```bash
python scripts/generate_synthetic_data.py
```

This creates:

```text
data/synthetic_behavior.csv
```

## Optional: Train Real XGBoost Models

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate data and train:

```bash
python scripts/generate_synthetic_data.py
python ml/train_xgboost.py
```

This writes model files to:

```text
data/models/
```

Restart the server. It will automatically use trained XGBoost models if the `xgboost` package and model files are available.

## Ethical Notes

This is a behavioral analytics prototype, not a clinical or diagnostic tool. The dashboard avoids medical claims and uses transparent score explanations, reliability labels, and evidence metrics so users can see why a conclusion appeared.
