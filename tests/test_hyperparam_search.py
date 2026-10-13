"""tests/test_hyperparam_search.py

Unit tests for hyperparameter grid search configuration generation,
validation, and optimal parameter selection logic (ACT-014, ACT-015).
"""

import os
import tempfile
import unittest
import pandas as pd
import numpy as np

from experiments.run_hyperparam_search import (
    COLUMNS,
    ALPHA_GRID,
    BETA_GRID,
    GAMMA_GRID,
    get_all_configurations,
)
from scripts.merge_hyperparam_results import validate_hyperparam_dataframe


class TestHyperparamSearchConfig(unittest.TestCase):
    """Tests grid search configuration generation and properties."""

    def test_configuration_count(self):
        configs = get_all_configurations()
        expected_count = len(ALPHA_GRID) * len(BETA_GRID) * len(GAMMA_GRID)
        self.assertEqual(len(configs), expected_count)
        self.assertEqual(len(configs), 200)

    def test_unique_config_ids(self):
        configs = get_all_configurations()
        ids = [c["config_id"] for c in configs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, list(range(200)))

    def test_config_keys_and_values(self):
        configs = get_all_configurations()
        for c in configs:
            self.assertIn("config_id", c)
            self.assertIn("alpha", c)
            self.assertIn("beta", c)
            self.assertIn("gamma", c)
            self.assertIn(c["alpha"], ALPHA_GRID)
            self.assertIn(c["beta"], BETA_GRID)
            self.assertIn(c["gamma"], GAMMA_GRID)


class TestHyperparamValidation(unittest.TestCase):
    """Tests schema validation and AR bounds checking for hyperparam datasets."""

    def _generate_mock_df(self) -> pd.DataFrame:
        rows = []
        for cfg_id in range(5):
            for s in range(2):
                rows.append({
                    "config_id": cfg_id,
                    "alpha": 0.5,
                    "beta": 1.5,
                    "gamma": 1.0,
                    "seed_id": s,
                    "num_nodes": 10,
                    "noise_level": 0.005,
                    "chosen_n_sub": 3,
                    "num_cuts": 4,
                    "quantum_cost": 0.1,
                    "classical_cost": 0.05,
                    "total_cost": 0.15,
                    "final_energy": -9.0,
                    "true_energy": -12.0,
                    "approximation_ratio": 0.75,
                    "runtime_seconds": 12.0,
                })
        return pd.DataFrame(rows)[COLUMNS]

    def test_valid_df_passes(self):
        df = self._generate_mock_df()
        validate_hyperparam_dataframe(df, "test")

    def test_missing_column_fails(self):
        df = self._generate_mock_df().drop(columns=["total_cost"])
        with self.assertRaises(ValueError):
            validate_hyperparam_dataframe(df, "test")

    def test_ar_above_one_fails(self):
        df = self._generate_mock_df()
        df.loc[0, "approximation_ratio"] = 1.08
        with self.assertRaises(ValueError):
            validate_hyperparam_dataframe(df, "test")


if __name__ == "__main__":
    unittest.main()
