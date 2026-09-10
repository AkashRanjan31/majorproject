# Development Guidelines

## Module Header Convention
Every Python file opens with a docstring block using this exact format:
```python
"""
filename.py
-----------
One-line description of the module's purpose.
"""
```
JavaScript files use a JSDoc block comment at the top:
```js
/**
 * filename.js - Short title
 * One-line description.
 */
```

## Naming Conventions
- Python: `snake_case` for variables, functions, and module names; `PascalCase` for classes
- Constants: `UPPER_SNAKE_CASE` (e.g., `MODEL_PATH`, `PROJECT_ROOT`, `MAX_BUFFER_SIZE`)
- JS: `camelCase` for variables/methods; `PascalCase` for classes (`FatigueChart`, `GaugeChart`)
- Private helpers: prefix with `_` (e.g., `_resize()`, `_init_session_state()`)
- Feature dict keys: exact column names from `dataset.csv` (e.g., `"key_press_count"`, `"cursor_speed"`)

## Project Root Resolution (Python)
Always resolve paths relative to the file, not the working directory:
```python
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
```
Save all output artifacts (plots, models) using `PROJECT_ROOT / "filename.ext"`.

## Configuration Pattern
Use `AppConfig` from `src/config.py` — never hardcode tuneable values:
```python
from src.config import get_config
config = get_config()
# Access: config.WINDOW_SIZE, config.MODEL_PATH, config.MAX_HISTORY_SIZE
```
`AppConfig.from_env()` reads env vars with fallback defaults — support `.env` files via `python-dotenv`.

## Logging Pattern
Use the logger factory — never call `logging.basicConfig` directly:
```python
from src.logger import setup_logger
logger = setup_logger(__name__)
logger.info("Starting...")
logger.debug(f"Value: {x}")
logger.warning("Non-fatal issue")
logger.error("Fatal issue")
```
`setup_logger` is idempotent (checks `logger.handlers` before adding). Log files go to `logs/<module_name>.log`.

## Model Persistence
The model artifact is a dict, not a bare model object:
```python
# Save
joblib.dump({"model": model, "feature_names": feature_names, "class_names": class_names}, MODEL_PATH)

# Load
saved = joblib.load(MODEL_PATH)
model = saved["model"]
feature_names = saved["feature_names"]
```

## Streamlit Session State
Persist objects across reruns using `st.session_state`. Always guard with `if 'key' not in st.session_state`:
```python
if 'monitor' not in st.session_state:
    st.session_state.monitor = None
```
Use `st.rerun()` (not `st.experimental_rerun`) after state changes.

## Streamlit UI Patterns
- `st.set_page_config()` must be the first Streamlit call in any app file
- Inject custom CSS via `st.markdown("""<style>...</style>""", unsafe_allow_html=True)` at the top
- Use `st.columns()` for side-by-side layout; `st.tabs()` for multi-section dashboards
- Use `st.metric()` for live numeric values in the dashboard
- Use `st.spinner()` around slow operations (model loading, initialization)
- Glassmorphism style: `background: rgba(255,255,255,.75); backdrop-filter: blur(20px); border-radius: 24px`
- Color palette: primary `#6366f1` (indigo), success `#22c55e`, warning `#f59e0b`, error `#ef4444`

## Evaluation Conventions
- Always use `weighted` average for multi-class metrics: `precision_score(..., average='weighted', zero_division=0)`
- ROC curve is only generated for binary classification — skip with a print message for 3-class
- Plots saved with `dpi=120`, `plt.tight_layout()`, then `plt.close()` to free memory
- Confusion matrix uses `seaborn.heatmap` with `cmap="Blues"`, `annot=True`, `fmt="d"`

## Data Generation / Reproducibility
- Always set `np.random.seed(42)` and `random_state=42` in train/test splits
- `train_test_split` uses `stratify=y` to preserve class balance
- Dataset is balanced: equal `N` samples per class, then shuffled with `sample(frac=1, random_state=42)`

## Feature Vector Ordering
The 16 features must always appear in this exact order when building a prediction input:
```
key_press_count, key_hold_time, typing_speed, error_rate, backspace_count, idle_time,
mouse_click_count, left_click, right_click, double_click, scroll_count,
cursor_speed, cursor_distance, drag_count, movement_speed, idle_mouse_time
```

## Error Handling
- Wrap initialization and prediction in `try/except Exception as e` and surface via `st.error()` / `st.warning()`
- Check for `None` before using `st.session_state` objects (monitor, predictor)
- Use `FileNotFoundError` specifically when the model file is missing, with a hint to run training

## JavaScript Canvas Charts
- Always account for `window.devicePixelRatio` when sizing canvas elements
- Use `_resize()` before every `render()` call to handle window resizes
- Export classes to `window` for cross-file access: `window.FatigueChart = FatigueChart`
- Padding object pattern: `const pad = { top: 20, right: 20, bottom: 30, left: 40 }`

## What NOT to Do
- Do not use any ML model other than XGBoostClassifier
- Do not add webcam, microphone, EEG, or wearable data sources
- Do not hardcode paths — use `Path(__file__).resolve()` or `config.MODEL_PATH`
- Do not call `logging.basicConfig` — always use `setup_logger(__name__)`
- Do not generate ROC curves for the 3-class problem
- Do not use `st.experimental_rerun` — use `st.rerun()`
