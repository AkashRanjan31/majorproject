# Product Overview

## Purpose
AI-Based Mental Health Fatigue Detection system that predicts mental fatigue levels using only keyboard and mouse behavioral signals — no webcam, EEG, wearables, or microphone required.

## Value Proposition
Passive, privacy-preserving fatigue monitoring that runs in the background and infers cognitive load from natural interaction patterns, requiring zero user effort beyond normal computer use.

## Key Features
- Real-time fatigue detection via keyboard/mouse monitoring
- Three-class fatigue classification: Normal (0), Moderate Fatigue (1), High Fatigue (2)
- XGBoost ML model trained on behavioral biometric data
- Streamlit dashboard with live status, history, and activity timeline
- Production-grade logging with rotating file handlers
- Environment-variable-driven configuration
- Full offline operation — no external API calls

## Fatigue Indicators Tracked

### Keyboard
- Key press count, hold time, typing speed, error rate, backspace count, idle time

### Mouse
- Click counts (left/right/double), scroll count, cursor speed/distance, drag count, movement speed, idle mouse time

## Target Users
- Knowledge workers monitoring their own cognitive fatigue
- Researchers studying behavioral biometrics
- Students building ML + HCI projects

## Use Cases
1. Personal fatigue awareness during long work/study sessions
2. Academic demonstration of behavioral ML pipeline
3. Foundation for workplace wellness tooling

## Entry Points
| Command | Purpose |
|---|---|
| `python main.py` | Full train + evaluate pipeline |
| `streamlit run app.py` | Static Streamlit demo |
| `streamlit run realtime_app.py` | Live real-time monitoring |
| `python src/train_model.py` | Train XGBoost model only |
| `python src/evaluate.py` | Evaluate saved model |
| `python src/predict.py` | Single prediction example |
