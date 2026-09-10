# AI-Based Mental Health Fatigue Detection Using Keyboard and Mouse Behavior

This project predicts mental fatigue using only keyboard and mouse behavior. It does not use webcam data, face detection, eye tracking, EEG, wearables, or microphone input.

The machine learning model is only `XGBoostClassifier`.

## Folder Structure

```text
MentalHealthFatigue/
  dataset/
    dataset.csv
    Data/
  models/
    xgboost_model.pkl
  src/
    load_data.py
    preprocess.py
    feature_engineering.py
    train_model.py
    evaluate.py
    predict.py
  notebooks/
  app.py
  main.py
  requirements.txt
  README.md
```

## Dataset

The code first looks for `dataset/dataset.csv`. If it does not exist, the project automatically builds it from the raw TSV files in `dataset/Data/`.

Keyboard features:

- Key Press Count
- Key Hold Time
- Typing Speed
- Error Rate
- Backspace Count
- Idle Time

Mouse features:

- Mouse Click Count
- Left Click
- Right Click
- Double Click
- Scroll Count
- Cursor Speed
- Cursor Distance
- Drag Count
- Movement Speed
- Idle Mouse Time

Target classes:

- `0` - Normal
- `1` - Moderate Fatigue
- `2` - High Fatigue

## VS Code Setup

Install Python 3.10 or newer from <https://www.python.org/downloads/>. During installation, enable "Add Python to PATH".

Open this project folder in VS Code, then run these commands in the VS Code terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the Project

Analyze the dataset:

```powershell
python src/load_data.py
```

Train the XGBoost model:

```powershell
python src/train_model.py
```

Evaluate the model:

```powershell
python src/evaluate.py
```

Run the full pipeline:

```powershell
python main.py
```

Run one prediction example:

```powershell
python src/predict.py
```

Launch the Streamlit interface:

```powershell
streamlit run app.py
```

## Expected Output

Training saves the model to:

```text
models/xgboost_model.pkl
```

Evaluation prints accuracy, precision, recall, F1 score, confusion matrix values, and classification report. It also saves:

```text
confusion_matrix.png
feature_importance.png
roc_curve.png
```

The ROC curve is generated only when the dataset has two classes. For the three-class fatigue problem, ROC is skipped to keep the project beginner friendly.

## Real-Time Collection Idea

For live prediction, a small background Python script can collect keyboard and mouse events over a fixed time window, such as 5 or 30 minutes. Libraries such as `pynput` can record key press counts, hold time, backspace usage, mouse clicks, cursor movement, drag actions, scrolling, and idle time.

After each time window, calculate the same feature names used during training and pass them to `predict_fatigue()` in `src/predict.py`. The trained XGBoost model will return the predicted fatigue level and confidence score.
