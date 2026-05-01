# TCBIS: Time-Constrained Behavioral Intelligence System

TCBIS is a working behavioral decision intelligence prototype. It measures behavior through timed, weighted decision scenarios instead of questionnaires.

Core idea:

```text
User -> Timed Scenario -> Weighted Decision -> Event Logger -> Feature Engine -> XGBoost -> Hybrid Score -> Dashboard
```

Each scenario has five strategic options. Every option carries hidden weights:

- Risk value
- Information value
- Exploration value
- Curiosity value
- Time-pressure impact

The user sees a decision scenario. The system sees a structured behavioral signal.

## Run The App

```bash
.\.venv\Scripts\python.exe backend\server.py
```

Open:

```text
http://127.0.0.1:8000
```

## What Changed In The Final Version

- 100-question weighted scenario bank
- 20 timed scenarios per assessment run
- 5 to 15 second time limits
- Hidden option weights for risk, information, exploration, curiosity, and pressure
- Server-side event enrichment from `question_id` and `selected_option`
- 16 engineered behavioral features
- XGBoost models for four traits
- Hybrid scoring formula:

```text
Final Score = 0.65 * XGBoost + 0.35 * Rule-Based Intelligence
```

## Engineered Features

```text
avg_decision_time
risk_score
exploration_score
curiosity_score
information_score
time_pressure_efficiency
decision_consistency
decision_variance
risk_shift_over_time
hint_dependency_curve
exploration_depth
pressure_success_rate
option_entropy
timeout_rate
path_unlock_rate
event_count
```

## Predicted Traits

- Confidence
- Curiosity
- Emotional Safety
- Exploratory Power

## API

### `GET /api/health`

Returns model status and Gemini availability.

### `GET /api/questions`

Returns a 20-scenario assessment from the 100-question bank.

### `POST /api/score`

Scores a completed run.

Example event:

```json
{
  "type": "decision",
  "question_id": 12,
  "selected_option": "C",
  "time_taken": 3.2,
  "time_limit": 10,
  "decision_under_pressure": false
}
```

The server enriches the event with hidden option weights before feature engineering.

### `POST /api/gemini-scenario`

Optional Gemini 1.5 scenario generation endpoint. Set `GEMINI_API_KEY` first:

```powershell
$env:GEMINI_API_KEY="your_key_here"
```

If no key is set, the app still works from the built-in question bank.

## Train The Model

```bash
.\.venv\Scripts\python.exe scripts\generate_synthetic_data.py
.\.venv\Scripts\python.exe ml\train_xgboost.py
```

Model artifacts are saved to:

```text
data/models/
```

Metrics are saved to:

```text
data/models/metrics.json
```

## Current Training Metrics

```text
confidence: R2=0.820
curiosity: R2=0.777
emotional_safety: R2=0.583
exploratory_power: R2=0.823
```

Emotional safety is intentionally harder because it depends on balanced risk behavior, consistency, and time pressure rather than one direct action.

## Ethical Note

This is a behavioral analytics prototype, not a clinical or diagnostic tool. Scores are exploratory and should not be used for medical, hiring, or high-stakes decisions without validation.
