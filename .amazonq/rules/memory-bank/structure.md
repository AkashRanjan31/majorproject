# Project Structure

## Directory Layout
```
d:\minor project/
├── src/                    # Core Python modules
│   ├── config.py           # AppConfig dataclass + env-var loading
│   ├── logger.py           # Rotating file + console logger factory
│   ├── load_data.py        # Dataset loading and analysis
│   ├── preprocess.py       # Feature scaling and label encoding
│   ├── feature_engineering.py  # Feature construction from raw data
│   ├── feature_extraction.py   # Real-time feature extraction from monitor buffers
│   ├── train_model.py      # XGBoost training + model persistence
│   ├── evaluate.py         # Metrics, confusion matrix, feature importance plots
│   ├── predict.py          # Single-sample prediction helper
│   ├── monitor.py          # pynput keyboard/mouse listener (ActivityMonitor)
│   ├── realtime_predict.py # FatiguePredictor wrapping the saved model
│   └── dashboard.py        # Streamlit UI component functions
├── dataset/
│   ├── dataset.csv         # Processed feature dataset (auto-built if missing)
│   ├── create_dataset.py   # Builds dataset.csv from raw TSV files
│   └── Data/
│       ├── user 1/         # Raw TSV files per user
│       └── user 2/         # keystrokes, mousedata, mouse_mov_speeds, etc.
├── models/
│   └── xgboost_model.pkl   # Trained model artifact (joblib)
├── static/
│   ├── css/style.css       # Web app styles
│   ├── js/app.js           # Web app logic
│   └── js/chart.js         # Chart rendering
├── templates/
│   └── index.html          # Flask/web app HTML template
├── tests/
│   └── test_audit.py       # Production audit tests
├── logs/                   # Rotating log files (auto-created)
├── app.py                  # Streamlit static demo app
├── realtime_app.py         # Streamlit real-time app (RealtimeApp class)
├── web_app.py              # Flask/alternative web interface
├── main.py                 # Pipeline runner (load → train → evaluate)
├── validate_production_setup.py  # Pre-flight validation script
└── requirements.txt
```

## Core Components and Relationships

### Data Pipeline (offline)
```
dataset/Data/ (TSV) → create_dataset.py → dataset.csv
dataset.csv → load_data.py → preprocess.py → feature_engineering.py → train_model.py → xgboost_model.pkl
xgboost_model.pkl → evaluate.py → metrics + plots
```

### Real-Time Pipeline
```
pynput events → monitor.py (ActivityMonitor)
                    ↓ get_raw_data()
             feature_extraction.py (FeatureExtractor.extract_features)
                    ↓ feature_vector
             realtime_predict.py (FatiguePredictor.predict)
                    ↓ prediction dict
             dashboard.py → realtime_app.py (Streamlit UI)
```

### Configuration Flow
```
environment variables → config.py (AppConfig.from_env) → get_config()
get_config() consumed by: realtime_app.py, monitor.py, realtime_predict.py, logger.py
```

## Architectural Patterns
- **Module separation**: data, training, evaluation, and real-time inference are fully decoupled
- **Session-state persistence**: Streamlit reruns handled via `st.session_state` in `RealtimeApp._init_session_state()`
- **Dataclass config**: `AppConfig` centralises all tuneable constants with env-var overrides
- **Logger factory**: `setup_logger(name)` returns per-module loggers with idempotent handler registration
- **Stateless feature extraction**: `FeatureExtractor.extract_features` is a `@staticmethod` / classmethod — no instance needed
- **Backup strategy**: `backup_pre_audit/` and `backups/` preserve pre-refactor snapshots
