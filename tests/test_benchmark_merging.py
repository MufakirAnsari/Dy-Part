"""tests/test_benchmark_merging.py

Unit tests for parallel benchmark partition validation and merging logic
in scripts/merge_baseline_results.py.
"""

import os
import tempfile
import unittest
import pandas as pd
import numpy as np

from scripts.merge_baseline_results import (
    EXPECTED_COLUMNS,
    EXPECTED_RUNS_PER_SEED,
    EXPECTED_TOTAL_RUNS,
    validate_dataframe,
)


def _generate_mock_seed_data(seed_id: int) -> pd.DataFrame:
    """Generates 48 mock runs for a single seed with valid schema and AR."""
    rows = []
    node_sizes = [8, 10, 12]
    noise_levels = np.logspace(-3.5, -1.5, 8)
    methods = ["dypart", "static"]

    for n in node_sizes:
        for noise in noise_levels:
            for m in methods:
                rows.append({
                    "method": m,
                    "num_nodes": n,
                    "noise_level": float(noise),
                    "chosen_n_sub": 2 if m == "dypart" else 4,
                    "final_energy": -8.0,
                    "true_energy": -10.0,
                    "approximation_ratio": 0.80,
                    "runtime_seconds": 15.0,
                    "seed_id": seed_id,
                })
    return pd.DataFrame(rows)[EXPECTED_COLUMNS]


class TestBenchmarkValidation(unittest.TestCase):
    """Tests schema validation, run count verification, and AR bounds checking."""

    def test_valid_dataframe_passes(self):
        df = _generate_mock_seed_data(0)
        validate_dataframe(df, "test", expected_seeds={0})

    def test_schema_mismatch_fails(self):
        df = _generate_mock_seed_data(0)
        df_invalid = df.drop(columns=["seed_id"])
        with self.assertRaises(ValueError):
            validate_dataframe(df_invalid, "test")

    def test_ar_above_one_fails(self):
        df = _generate_mock_seed_data(0)
        df.loc[0, "approximation_ratio"] = 1.05
        with self.assertRaises(ValueError):
            validate_dataframe(df, "test")

    def test_ar_below_zero_fails(self):
        df = _generate_mock_seed_data(0)
        df.loc[0, "approximation_ratio"] = -0.1
        with self.assertRaises(ValueError):
            validate_dataframe(df, "test")

    def test_missing_expected_seed_fails(self):
        df = _generate_mock_seed_data(0)
        with self.assertRaises(ValueError):
            validate_dataframe(df, "test", expected_seeds={0, 1})

    def test_incomplete_runs_fails(self):
        df = _generate_mock_seed_data(0).iloc[:20]  # Only 20 instead of 48
        with self.assertRaises(ValueError):
            validate_dataframe(df, "test")


class TestBenchmarkMergingPipeline(unittest.TestCase):
    """Tests end-to-end multi-partition merging."""

    def test_full_30_seed_merge_succeeds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Create base file (seeds 0..9)
            base_dfs = [_generate_mock_seed_data(s) for s in range(10)]
            base_df = pd.concat(base_dfs, ignore_index=True)
            base_path = os.path.join(tmpdir, "base.csv")
            base_df.to_csv(base_path, index=False)

            # 2. Create 4 part files (seeds 10..14, 15..19, 20..24, 25..29)
            ranges = [range(10, 15), range(15, 20), range(20, 25), range(25, 30)]
            part_paths = []
            for idx, r in enumerate(ranges):
                part_dfs = [_generate_mock_seed_data(s) for s in r]
                part_df = pd.concat(part_dfs, ignore_index=True)
                part_file = os.path.join(tmpdir, f"part_{idx}.csv")
                part_df.to_csv(part_file, index=False)
                part_paths.append(part_file)

            # 3. Simulate merge
            dfs = [pd.read_csv(base_path)] + [pd.read_csv(p) for p in part_paths]
            merged = pd.concat(dfs, ignore_index=True)
            validate_dataframe(merged, "Consolidated", expected_seeds=set(range(30)))

            self.assertEqual(len(merged), EXPECTED_TOTAL_RUNS)
            self.assertEqual(len(merged), 1440)
            self.assertEqual(set(merged["seed_id"].unique()), set(range(30)))
            self.assertTrue((merged["approximation_ratio"] <= 1.0).all())
            self.assertTrue((merged["approximation_ratio"] >= 0.0).all())


if __name__ == "__main__":
    unittest.main()
