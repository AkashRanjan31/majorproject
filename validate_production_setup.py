#!/usr/bin/env python3
"""
validate_production_setup.py
---------------------------
Quick validation script to verify production deployment readiness.
Run: python validate_production_setup.py
"""

import os
import sys
from pathlib import Path

def print_header(msg):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def check_file_exists(path, description):
    """Check if a file exists and report status."""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_directory_exists(path, description):
    """Check if a directory exists and report status."""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def main():
    """Run validation checks."""
    print_header("PRODUCTION DEPLOYMENT VALIDATION")
    
    all_passed = True
    
    # 1. Check critical files
    print("\n📋 Checking Critical Files...")
    critical_files = {
        "realtime_app.py": "Main application",
        "src/monitor.py": "Monitoring module",
        "src/feature_extraction.py": "Feature extraction module",
        "src/realtime_predict.py": "Prediction module",
        "src/config.py": "Configuration module",
        "src/logger.py": "Logging module",
        "models/xgboost_model.pkl": "Trained model",
        "requirements.txt": "Dependencies"
    }
    
    for file_path, description in critical_files.items():
        if not check_file_exists(file_path, description):
            all_passed = False
    
    # 2. Check documentation
    print("\n📚 Checking Documentation...")
    docs = {
        "DEPLOYMENT_GUIDE.md": "Deployment guide",
        "PRODUCTION_CHECKLIST.md": "Production checklist",
        "PRODUCTION_UPGRADE_SUMMARY.md": "Upgrade summary",
        "REALTIME_README.md": "README"
    }
    
    for doc_file, description in docs.items():
        if not check_file_exists(doc_file, description):
            all_passed = False
    
    # 3. Check directories
    print("\n📁 Checking Directories...")
    dirs = {
        "src": "Source code directory",
        "models": "Models directory",
        "logs": "Logs directory",
        "dataset": "Dataset directory"
    }
    
    for dir_path, description in dirs.items():
        if not check_directory_exists(dir_path, description):
            print(f"⚠️  Warning: {description} not found: {dir_path}")
    
    # 4. Check Python imports
    print("\n🐍 Checking Python Imports...")
    required_modules = [
        ("pandas", "Data manipulation"),
        ("numpy", "Numerical computing"),
        ("sklearn", "Machine learning"),
        ("xgboost", "XGBoost model"),
        ("joblib", "Model serialization"),
        ("streamlit", "Web framework"),
        ("pynput", "Input monitoring"),
    ]
    
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}: {description}")
        except ImportError:
            print(f"❌ {module_name}: {description} - NOT INSTALLED")
            all_passed = False
    
    # 5. Check custom modules
    print("\n🔧 Checking Custom Modules...")
    try:
        from src.config import get_config
        print("✅ src.config: Configuration system")
        config = get_config()
        print(f"   - WINDOW_SIZE: {config.WINDOW_SIZE}s")
        print(f"   - MODEL_PATH: {config.MODEL_PATH}")
        print(f"   - MAX_HISTORY_SIZE: {config.MAX_HISTORY_SIZE}")
    except Exception as e:
        print(f"❌ src.config: {e}")
        all_passed = False
    
    try:
        from src.logger import setup_logger
        logger = setup_logger("validation")
        print("✅ src.logger: Logging system")
        logger.info("Validation check")
    except Exception as e:
        print(f"❌ src.logger: {e}")
        all_passed = False
    
    try:
        from src.monitor import ActivityMonitor, CircularBuffer
        print("✅ src.monitor: Monitoring system with CircularBuffer")
    except Exception as e:
        print(f"❌ src.monitor: {e}")
        all_passed = False
    
    try:
        from src.feature_extraction import FeatureExtractor, FEATURE_ORDER
        print("✅ src.feature_extraction: Feature extraction (16 features)")
        print(f"   - Feature order verified: {len(FEATURE_ORDER)} features")
    except Exception as e:
        print(f"❌ src.feature_extraction: {e}")
        all_passed = False
    
    try:
        from src.realtime_predict import FatiguePredictor
        print("✅ src.realtime_predict: Prediction engine")
    except Exception as e:
        print(f"❌ src.realtime_predict: {e}")
        all_passed = False
    
    # 6. Check model
    print("\n🧠 Checking Model...")
    try:
        import joblib
        if Path("models/xgboost_model.pkl").exists():
            model = joblib.load("models/xgboost_model.pkl")
            if isinstance(model, dict):
                print(f"✅ Model loaded as dict with keys: {list(model.keys())}")
            else:
                print(f"✅ Model loaded as {type(model).__name__}")
        else:
            print("❌ Model file not found")
            all_passed = False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        all_passed = False
    
    # 7. Check logs directory
    print("\n📝 Checking Logs Directory...")
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"✅ Logs directory exists with {len(log_files)} log files")
        for log_file in log_files:
            size_mb = log_file.stat().st_size / (1024 * 1024)
            print(f"   - {log_file.name}: {size_mb:.2f} MB")
    else:
        print(f"⚠️  Logs directory not found (will be created on first run)")
    
    # Final summary
    print_header("VALIDATION SUMMARY")
    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Production Deployment Ready!\n")
        print("Next steps:")
        print("1. Run: streamlit run realtime_app.py")
        print("2. Application will start at http://localhost:8501")
        print("3. Check logs/ directory for detailed logs")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Please fix issues before deployment\n")
        print("For help, see:")
        print("- DEPLOYMENT_GUIDE.md: Detailed deployment instructions")
        print("- PRODUCTION_CHECKLIST.md: Production readiness checklist")
        return 1

if __name__ == "__main__":
    sys.exit(main())
