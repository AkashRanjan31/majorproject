"""
logger.py
---------
Production-grade logging system.
"""

import logging
import logging.handlers
from pathlib import Path
from src.config import get_config


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Configured logger
    """
    config = get_config()
    logger = logging.getLogger(name)
    
    if logger.handlers:  # Already configured
        return logger

    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Format
    formatter = logging.Formatter(config.LOG_FORMAT)

    # File handler
    fh = logging.handlers.RotatingFileHandler(
        log_dir / f"{name}.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, config.LOG_LEVEL))
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
