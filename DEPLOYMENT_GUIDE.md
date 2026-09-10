# 🚀 Production Deployment Guide

## System Requirements

### Hardware
- **CPU**: Minimum 2 cores, recommended 4+ cores
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 2GB free space
- **Network**: Stable internet connection (optional for offline mode)

### Software
- **Python**: 3.8 or higher
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

---

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd minor project
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "from src.monitor import ActivityMonitor; print('✅ Installation successful')"
```

---

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Monitoring
WINDOW_SIZE=60
MAX_KEY_EVENTS_PER_WINDOW=5000
MAX_MOUSE_MOVEMENTS_PER_WINDOW=10000

# Model
MODEL_PATH=models/xgboost_model.pkl

# Performance
PREDICTION_INTERVAL=30
AUTO_CLEANUP_INTERVAL=300

# Logging
LOG_LEVEL=INFO

# History
MAX_HISTORY_SIZE=100
MAX_TIMELINE_SIZE=100
```

### Configuration Priority
1. Environment variables (highest)
2. `.env` file
3. Defaults in `src/config.py` (lowest)

---

## Running the Application

### Start the Real-Time Dashboard
```bash
streamlit run realtime_app.py
```

The application will:
- Initialize monitoring system
- Load the trained XGBoost model
- Start keyboard and mouse tracking
- Open the dashboard in your browser (http://localhost:8501)

### Output
- Browser: Interactive Streamlit dashboard
- Console: Logging output with timestamps
- Files: Detailed logs in `logs/` directory

---

## Monitoring & Logging

### Log Files Location
```
logs/
├── logger.log           # General logs
├── __main__.log         # Main application
├── monitor.log          # Monitoring events
├── realtime_predict.log # Predictions
└── feature_extraction.log # Feature extraction
```

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for very serious problems

### Checking Logs
```bash
# View all logs
cat logs/logger.log

# Real-time log monitoring
tail -f logs/logger.log

# Filter by error level
grep ERROR logs/logger.log
```

---

## Production Best Practices

### 1. Error Recovery
- Application automatically recovers from minor errors
- Failed predictions are logged but don't crash the system
- Safe default values returned on errors

### 2. Resource Management
- Memory is automatically cleaned every 60 seconds
- Circular buffers prevent unbounded growth
- Graceful shutdown on Ctrl+C

### 3. Performance Monitoring
- Check `logs/logger.log` for performance metrics
- Monitor buffer usage via dashboard
- Review prediction confidence scores

### 4. Data Privacy
- No data is stored to disk (in-memory only)
- Logs contain only activity statistics, not personal data
- No external API calls

### 5. Security
- Input validation on all data
- Bounds checking on mouse positions
- Type validation for features
- Model integrity verification

---

## Troubleshooting

### Issue: "Permission Denied" Error
**Solution**: Application needs permission to monitor input
- **Windows**: Run as Administrator
- **macOS**: Grant accessibility permissions in System Preferences → Security & Privacy
- **Linux**: Run with appropriate privileges or use accessibility configuration

### Issue: "Model Not Found"
**Solution**: Ensure trained model exists
```bash
# Train the model
python main.py

# Verify model file
ls -lh models/xgboost_model.pkl
```

### Issue: Low Prediction Accuracy
**Solution**: Model accuracy depends on training data
- Collect more user data
- Retrain with new data: `python main.py`
- Adjust model parameters in `src/train_model.py`

### Issue: High CPU Usage
**Solution**: Reduce update frequency
- Increase PREDICTION_INTERVAL in `.env` (default: 30s)
- Reduce WINDOW_SIZE (default: 60s)

### Issue: Memory Leaks
**Solution**: Verify cleanup is running
- Check logs for cleanup messages
- Restart application if memory usage exceeds limits
- Verify AUTO_CLEANUP_INTERVAL setting

---

## Performance Optimization

### Tuning Parameters

#### Window Size (WINDOW_SIZE)
- **Smaller (30s)**: More responsive, less accurate
- **Larger (90s)**: More accurate, less responsive
- **Default**: 60 seconds

#### Prediction Interval (PREDICTION_INTERVAL)
- **Smaller (15s)**: More frequent updates, higher CPU
- **Larger (60s)**: Less frequent updates, lower CPU
- **Default**: 30 seconds

#### Buffer Sizes
- **MAX_KEY_EVENTS_PER_WINDOW**: 5000 (adjust based on typing speed)
- **MAX_MOUSE_MOVEMENTS_PER_WINDOW**: 10000 (adjust based on mouse sensitivity)

### Memory Usage Examples
- Typical usage: 200-300 MB
- With high activity: 400-600 MB
- Max with all buffers full: ~1 GB

---

## Deployment Scenarios

### Scenario 1: Single User Development
```bash
streamlit run realtime_app.py
```

### Scenario 2: Multi-User Organization
```bash
# Deploy with Streamlit Cloud
streamlit deploy realtime_app.py

# Or use Docker
docker build -t fatigue-detection .
docker run -p 8501:8501 fatigue-detection
```

### Scenario 3: Headless Monitoring
```python
from src.monitor import ActivityMonitor
from src.realtime_predict import FatiguePredictor

monitor = ActivityMonitor(window_size=60)
predictor = FatiguePredictor()

monitor.start()
# Use monitor.get_raw_data() and predictor.predict() programmatically
```

---

## Backup & Recovery

### Data Backup
- No persistent data to backup (in-memory only)
- Model is static (train once, use many times)
- Logs can be archived periodically

### Model Backup
```bash
# Backup current model
cp models/xgboost_model.pkl models/xgboost_model_backup.pkl

# Restore from backup
cp models/xgboost_model_backup.pkl models/xgboost_model.pkl
```

---

## Maintenance

### Weekly Tasks
- Review logs for errors
- Check model accuracy
- Verify resource usage

### Monthly Tasks
- Retrain model with new data (if available)
- Archive old logs
- Review performance metrics

### Quarterly Tasks
- Update dependencies
- Security audit
- Performance optimization

---

## Support & Debugging

### Enable Debug Logging
```python
# In .env
LOG_LEVEL=DEBUG

# Or
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Collect Debug Information
```bash
python -c "
from src.config import get_config
from src.logger import setup_logger
import sys

config = get_config()
print('Python:', sys.version)
print('Config:', config)
"
```

### Get Application Statistics
```bash
tail -100 logs/logger.log | grep -i "stats\|performance"
```

---

## Version Information
- **Application**: v1.0 Production
- **Python**: 3.8+
- **Last Updated**: 2026-07-11
- **Status**: Production Ready ✅

---

For additional support, check PRODUCTION_CHECKLIST.md and REALTIME_README.md
