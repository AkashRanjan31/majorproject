# Technology Stack

## Language
- Python 3.10+

## Core Dependencies (requirements.txt)
| Package | Version | Role |
|---|---|---|
| xgboost | >=1.7.0 | Fatigue classification model |
| scikit-learn | >=1.2.0 | Preprocessing, metrics, train/test split |
| pandas | >=1.5.0 | Dataset loading and manipulation |
| numpy | >=1.24.0 | Numerical feature computation |
| joblib | >=1.2.0 | Model serialization (.pkl) |
| streamlit | >=1.20.0 | Dashboard UI (static + real-time) |
| pynput | >=1.8.0 | Keyboard and mouse event capture |
| matplotlib | >=3.6.0 | Confusion matrix, feature importance, ROC plots |
| seaborn | >=0.12.0 | Heatmap styling for confusion matrix |
| python-dotenv | >=0.21.0 | .env file support for config |

## ML Model
- Algorithm: XGBoostClassifier (only model used — no alternatives)
- Artifact: `models/xgboost_model.pkl` (joblib serialization)
- Classes: 0 = Normal, 1 = Moderate Fatigue, 2 = High Fatigue
- ROC curve: skipped for 3-class problem (only generated for binary)

## Configuration
- `src/config.py`: `AppConfig` dataclass with `from_env()` classmethod
- Key env vars: `WINDOW_SIZE`, `MODEL_PATH`, `PREDICTION_INTERVAL`, `LOG_LEVEL`
- Defaults: 60s window, 30s prediction interval, INFO log level

## Logging
- `src/logger.py`: `setup_logger(name)` factory
- Rotating file handler: 10 MB max, 5 backups, stored in `logs/<module_name>.log`
- Console handler mirrors file at configured log level

## Frontend (web_app.py / static/)
- HTML template: `templates/index.html`
- CSS: `static/css/style.css`
- JS: `static/js/app.js`, `static/js/chart.js`

## Development Commands
```powershell
# Environment setup
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Data
python dataset/create_dataset.py   # Build dataset.csv from raw TSVs
python src/load_data.py            # Analyze dataset

# Training & evaluation
python src/train_model.py
python src/evaluate.py
python main.py                     # Full pipeline

# Inference
python src/predict.py              # Single prediction example

# Apps
streamlit run app.py               # Static Streamlit demo
streamlit run realtime_app.py      # Real-time monitoring app

# Validation
python validate_production_setup.py
```

## Output Artifacts
- `models/xgboost_model.pkl` — trained model
- `confusion_matrix.png` — evaluation plot
- `feature_importance.png` — feature importance plot
- `roc_curve.png` — ROC (binary only)
- `logs/*.log` — rotating application logs
