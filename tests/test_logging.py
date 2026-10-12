# tests/test_logging.py
"""Tests verifying the dual file+console logging system (ACT-003, ISS-038, TEST-007)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from vqe_framework.logging_config import setup_logging


class TestLoggingConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_log_dir = os.environ.get("DYPART_LOG_DIR")
        self.orig_job_id = os.environ.get("SLURM_JOB_ID")
        os.environ["DYPART_LOG_DIR"] = self.temp_dir
        os.environ["SLURM_JOB_ID"] = "testjob999"

    def tearDown(self):
        if self.orig_log_dir is not None:
            os.environ["DYPART_LOG_DIR"] = self.orig_log_dir
        else:
            os.environ.pop("DYPART_LOG_DIR", None)

        if self.orig_job_id is not None:
            os.environ["SLURM_JOB_ID"] = self.orig_job_id
        else:
            os.environ.pop("SLURM_JOB_ID", None)

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logging_creates_file_and_logs(self):
        logger = setup_logging()
        self.assertIsNotNone(logger)

        test_msg = "Verification message for logging test"
        logger.info(test_msg)

        # Check that log files exist in the directory
        log_files = list(Path(self.temp_dir).glob("dypart_testjob999_*.log"))
        self.assertGreaterEqual(len(log_files), 1)

        # Read the log file and verify contents
        content = log_files[0].read_text(encoding="utf-8")
        self.assertIn("DY-PART LOGGING INITIALIZED", content)
        self.assertIn("SLURM Job   : testjob999", content)
        self.assertIn(test_msg, content)


if __name__ == "__main__":
    unittest.main()
