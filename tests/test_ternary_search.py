# tests/test_ternary_search.py
"""Tests verifying discrete ternary search correctness and efficiency (TEST-004, ACT-010, ACT-011, ISS-001)."""

import unittest
import networkx as nx
from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler


class TestTernarySearch(unittest.TestCase):
    def setUp(self):
        self.graph12 = nx.random_regular_graph(3, 12, seed=42)
        self.graph16 = nx.random_regular_graph(3, 16, seed=123)
        self.graph20 = nx.random_regular_graph(3, 20, seed=999)

        self.cost_model = HeuristicCostModel(
            gate_error_rate=0.01, alpha=0.5, beta=1.5, gamma=1.0
        )
        self.scheduler = DyPartScheduler(self.cost_model)

    def test_ternary_matches_exhaustive_on_medium_graph(self):
        """Ternary search must find the same optimum (or near-identical cost) as exhaustive search."""
        res_exhaustive = self.scheduler.find_optimal_partition(
            self.graph12, search_method="exhaustive"
        )
        res_ternary = self.scheduler.find_optimal_partition(
            self.graph12, search_method="ternary"
        )

        self.assertEqual(
            res_ternary["optimal_n_sub"],
            res_exhaustive["optimal_n_sub"],
            "Ternary search must identify same optimal n_sub as exhaustive",
        )
        self.assertAlmostEqual(
            res_ternary["best_cost"],
            res_exhaustive["best_cost"],
            places=5,
            msg="Ternary search optimal cost must match exhaustive",
        )

    def test_ternary_evaluations_fewer_than_exhaustive_on_large_graph(self):
        """On larger graphs, ternary search must evaluate fewer points than full exhaustive scan."""
        res_exhaustive = self.scheduler.find_optimal_partition(
            self.graph20, search_method="exhaustive"
        )
        res_ternary = self.scheduler.find_optimal_partition(
            self.graph20, search_method="ternary"
        )

        self.assertLess(
            res_ternary["num_evaluations"],
            res_exhaustive["num_evaluations"],
            "Ternary search must evaluate strictly fewer points than exhaustive search",
        )

    def test_small_graph_fallback(self):
        """Small graphs (<= fallback threshold) must fall back to exhaustive search safely."""
        small_graph = nx.random_regular_graph(3, 6, seed=1)
        res = self.scheduler.find_optimal_partition(small_graph, fallback_threshold=6)

        self.assertEqual(res["search_method_used"], "exhaustive")
        self.assertIn("optimal_n_sub", res)


if __name__ == "__main__":
    unittest.main()
