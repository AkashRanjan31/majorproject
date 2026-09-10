# 🧠 AI-Based Mental Fatigue Detection Using Keyboard and Mouse Behavior

## Overview

This is a **real-time mental fatigue detection system** that continuously monitors keyboard and mouse activity and predicts the user's fatigue level using a trained XGBoost machine learning model.

The system does NOT use webcams, face detection, eye tracking, microphones, EEG, or wearable devices. It relies **entirely on behavioral patterns** from keyboard and mouse activity.

---

## 📋 Project Structure

```
├── realtime_app.py              # Main real-time application (Streamlit)
├── main.py                      # Batch pipeline (train & evaluate)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── src/
│   ├── monitor.py              # Real-time keyboard & mouse monitoring
│   ├── feature_extraction.py   # Convert raw data to ML features
│   ├── realtime_predict.py     # Load model & make predictions
│   ├── dashboard.py            # Streamlit UI components
│   ├── load_data.py            # Load dataset
│   ├── preprocess.py           # Data preprocessing
│   ├── feature_engineering.py  # Feature engineering
│   ├── train_model.py          # Train XGBoost model
│   ├── evaluate.py             # Evaluate model
│   └── predict.py              # Batch predictions
│
├── dataset/
│   ├── create_dataset.py       # Build dataset from raw data
│   └── Data/
│       ├── user 1/
│       └── user 2/
│
├── models/
│   └── xgboost_model.pkl       # Trained XGBoost model
│
└── notebooks/
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Real-Time Monitoring

```bash
streamlit run realtime_app.py
```

The app will open in your browser at `http://localhost:8501`

### 3. Features Monitored

**Keyboard Metrics:**
- Key press count
- Key hold time (duration keys are pressed)
- Typing speed (WPM)
- Error rate (based on backspace frequency)
- Backspace count
- Idle keyboard time

**Mouse Metrics:**
- Left clicks, right clicks, double clicks
- Total mouse click count
- Scroll count
- Cursor speed (pixels/second)
- Cursor movement distance
- Movement speed
- Mouse idle time

---

## 📊 Fatigue Levels

The model predicts three fatigue levels:

| Level | Emoji | Status | Meaning |
|-------|-------|--------|---------|
| 0 | 🟢 | Normal | User is alert and focused |
| 1 | 🟡 | Moderate Fatigue | Early signs of fatigue detected |
| 2 | 🔴 | High Fatigue | Significant fatigue detected |

---

## 🎯 How It Works

### Real-Time Process

1. **Monitoring** → Captures keyboard and mouse events continuously
2. **Feature Extraction** → Calculates 16 behavioral features every 60 seconds
3. **Prediction** → Passes features to XGBoost model for fatigue prediction
4. **Display** → Shows prediction, confidence, and activity metrics on dashboard

### Feature Extraction Window

Features are calculated over a **60-second sliding window**:
- Raw events are collected continuously
- Every 60 seconds, features are extracted and prediction is made
- Window resets automatically

---

## 🛠️ Architecture

### Module Descriptions

#### `monitor.py` - Real-Time Activity Monitoring
- Captures keyboard press/release events
- Captures mouse movement, clicks, and scrolls
- Tracks idle times
- Thread-safe data collection using locks

#### `feature_extraction.py` - Feature Engineering
- Converts raw events to ML features
- Maintains **exact feature order** used during training
- Handles edge cases (no movement, no clicks, etc.)

#### `realtime_predict.py` - Prediction Engine
- Loads trained XGBoost model
- Makes predictions on feature vectors
- Returns fatigue level, confidence, and probabilities

#### `dashboard.py` - Streamlit UI Components
- Status display with colored indicators
- Real-time metrics cards
- Prediction history charts
- Activity timeline graphs
- Session information

#### `realtime_app.py` - Main Application
- Integrates all components
- Manages session state
- Handles auto-refresh
- Displays multi-tab dashboard

---

## 📈 Dashboard Features

### Tab 1: Current Status
- **Main Status Card** → Current fatigue level with confidence score
- **Live Metrics** → Real-time keyboard and mouse activity
- **Session Info** → Start time, duration, prediction count

### Tab 2: History
- **Fatigue Level Graph** → Prediction trends over time
- **Activity Timeline** → Typing speed and cursor speed evolution

### Tab 3: Details
- **Keyboard Features** → All keyboard metrics with values
- **Mouse Features** → All mouse metrics with values
- **Prediction Details** → Model output and probability distribution

### Sidebar
- **Update Interval** → Adjust refresh rate (5-120 seconds)
- **About** → System information and feature descriptions

---

## 🔑 Key Features

✅ **Real-Time Monitoring** - Captures activity as it happens
✅ **Continuous Prediction** - Updates fatigue level every 60 seconds
✅ **No Privacy Concerns** - Only keyboard and mouse, no webcam/audio
✅ **Live Dashboard** - Beautiful Streamlit interface with charts
✅ **Confidence Scores** - Shows model certainty for each prediction
✅ **Activity Metrics** - Display typing speed, clicks, movements, idle time
✅ **Prediction History** - Track fatigue trends over time
✅ **Session Tracking** - Monitor total duration and prediction count

---

## ⚙️ Configuration

### Adjust Window Size
Edit `realtime_app.py` to change the monitoring window:

```python
self.monitor = ActivityMonitor(window_size=60)  # Change 60 to desired seconds
```

### Adjust Refresh Rate
Use the sidebar slider in the Streamlit app (5-120 seconds)

### Change Model Path
Update the model path in `realtime_app.py`:

```python
self.predictor = FatiguePredictor('path/to/model.pkl')
```

---

## 📊 Model Information

- **Algorithm**: XGBoost (Gradient Boosting)
- **Input Features**: 16 behavioral metrics
- **Output Classes**: 3 (Normal, Moderate Fatigue, High Fatigue)
- **Training Data**: 98 samples from 2 users
- **Model File**: `models/xgboost_model.pkl`

---

## 🔄 Training Pipeline (Batch)

To retrain the model:

```bash
python main.py
```

This will:
1. Load and analyze the dataset
2. Train a new XGBoost model
3. Evaluate performance
4. Save the model to `models/xgboost_model.pkl`

---

## ⚠️ Important Notes

1. **Privacy** - The system monitors behavioral patterns only. It does NOT:
   - Record keystrokes
   - Capture screen content
   - Access webcam or microphone
   - Track personal information

2. **Accuracy** - The model's accuracy depends on:
   - Training data quality
   - Feature relevance
   - Individual behavioral patterns
   - Model tuning

3. **Limitations** - This is a behavioral indicator tool:
   - Does NOT diagnose clinical fatigue or sleep disorders
   - Should NOT be used as medical advice
   - Works best with personalized models trained on individual data

4. **Permissions** - May require:
   - Input monitoring permissions (macOS/Linux)
   - Accessibility permissions (Windows/macOS)

---

## 📚 Feature Details

### Feature Order (Critical for Model)
1. key_press_count
2. key_hold_time
3. typing_speed
4. error_rate
5. backspace_count
6. idle_time
7. mouse_click_count
8. left_click
9. right_click
10. double_click
11. scroll_count
12. cursor_speed
13. cursor_distance
14. drag_count
15. movement_speed
16. idle_mouse_time

**Important**: Features must be in this exact order when making predictions!

---

## 🐛 Troubleshooting

### Issue: "Model not found"
**Solution**: Ensure the model file exists at `models/xgboost_model.pkl`
Run `python main.py` to train and generate the model.

### Issue: "pynput not found"
**Solution**: Install pynput
```bash
pip install pynput
```

### Issue: Permission denied on macOS/Linux
**Solution**: Grant accessibility permissions to the Python process
- macOS: System Preferences → Security & Privacy → Accessibility
- Linux: May need to run with elevated privileges

### Issue: No keyboard/mouse activity detected
**Solution**: 
- Check that the app has proper permissions
- Try moving mouse/typing to generate events
- Check if another application is blocking input monitoring

### Issue: Very low prediction accuracy
**Solution**:
- System needs more training data (98 samples is minimal)
- Try collecting more user data
- Retrain the model with the new data

---

## 📝 Example Workflow

1. **Launch Application**
   ```bash
   streamlit run realtime_app.py
   ```

2. **Wait for Initialization** (60 seconds for baseline)
   - System collects initial keyboard and mouse activity

3. **View Dashboard**
   - See current fatigue level with confidence
   - Monitor real-time metrics (typing speed, clicks, etc.)
   - Check activity history

4. **Interpret Results**
   - 🟢 Green = Normal, work as usual
   - 🟡 Yellow = Moderate fatigue, consider a break
   - 🔴 Red = High fatigue, take a break immediately

5. **Review History**
   - Click "History" tab to see trends
   - Identify fatigue patterns throughout the day

---

## 🎓 Machine Learning Details

### Model Type
- **Algorithm**: XGBoost (Extreme Gradient Boosting)
- **Task**: Multi-class classification
- **Classes**: 3 (Normal, Moderate, High)

### Feature Scaling
- No explicit scaling (XGBoost is tree-based)
- Features are in different units (counts, speeds, times)

### Class Distribution
- Class 0 (Normal): ~7% of data
- Class 1 (Moderate): ~46% of data
- Class 2 (High): ~47% of data

**Note**: Small training dataset requires caution when interpreting results

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Ensure all dependencies are installed
4. Verify model file exists and is valid

---

## 📄 License

This project is for educational and research purposes.

---

## 🎯 Next Steps & Improvements

1. **Data Collection**
   - Collect more user data for better model accuracy
   - Create user-specific models for personalization

2. **Feature Engineering**
   - Add inter-keystroke timing patterns
   - Add mouse acceleration metrics
   - Include time-of-day features

3. **Model Improvements**
   - Try deep learning (LSTM, CNN)
   - Implement ensemble methods
   - Add anomaly detection

4. **UI Enhancements**
   - Add data export functionality
   - Create alerts/notifications
   - Add daily/weekly reports

5. **Integration**
   - Integrate with productivity tools
   - Connect to calendar for context
   - Sync with health trackers (optional)

---

**Happy monitoring! 🚀**
