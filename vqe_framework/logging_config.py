# vqe_framework/logging_config.py
"""Centralized logging configuration for the Dy-Part framework.

Provides dual file+console logging with SLURM-aware file naming,
log rotation, and environment-variable configuration.

Environment variables:
    DYPART_LOG_DIR   — Directory for log files (default: ./logs/)
    DYPART_LOG_LEVEL — Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
    SLURM_JOB_ID     — Automatically set by SLURM; included in log filename
"""

import logging
import logging.handlers
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def setup_logging(level=None):
    """Configure the DyPart logger with both console and file handlers.

    Args:
        level: Logging level. If None, reads from DYPART_LOG_LEVEL env var
               (default: INFO).

    Returns:
        logging.Logger: Configured logger instance named 'DyPart'.
    """
    # Resolve log level
    if level is None:
        env_level = os.environ.get("DYPART_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    logger = logging.getLogger("DyPart")
    logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    # --- Format ---
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # --- Console handler (stdout) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- File handler ---
    log_dir = Path(os.environ.get("DYPART_LOG_DIR", "./logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    # Build filename with SLURM job ID or PID
    job_id = os.environ.get("SLURM_JOB_ID", f"pid{os.getpid()}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_filename = f"dypart_{job_id}_{timestamp}.log"
    log_path = log_dir / log_filename

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # File always captures DEBUG
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # --- Startup banner ---
    logger.info("=" * 70)
    logger.info("DY-PART LOGGING INITIALIZED")
    logger.info("  Python      : %s", sys.version.split()[0])
    logger.info("  Platform    : %s", platform.platform())
    logger.info("  Hostname    : %s", platform.node())
    logger.info("  PID         : %d", os.getpid())
    logger.info("  SLURM Job   : %s", os.environ.get("SLURM_JOB_ID", "N/A"))
    logger.info("  Log file    : %s", log_path)
    logger.info("  Console lvl : %s", logging.getLevelName(level))
    logger.info("  File lvl    : DEBUG")
    logger.info("  Log dir     : %s", log_dir.resolve())
    logger.info("=" * 70)

    return logger