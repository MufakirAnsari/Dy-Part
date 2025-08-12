# vqe_framework/logging_config.py
import logging
import sys

def setup_logging(level=logging.INFO):
    """Sets up a basic console logger for the framework."""
    # Get the root logger
    logger = logging.getLogger("DyPart")
    logger.setLevel(level)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger