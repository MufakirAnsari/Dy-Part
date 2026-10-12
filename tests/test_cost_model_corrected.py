# tests/test_cost_model_corrected.py
"""Tests for corrected classical cost formula monotonicity (TEST-002, ACT-008, ISS-004)."""

import unittest
import networkx as nx
from vqe_framework.cost_model import HeuristicCostModel


class TestCostModelCorrected(unittest.TestCase):
    def setUp(self):
        self.graph = nx.random_regular_graph(3, 10, seed=42)  # 10 nodes, 15 edges

    def test_higher_beta_strictly_increases_cost(self):
        """Verify that higher beta strictly increases classical cost for fixed num_cuts > 0 (fixes ISS-004)."""
        num_cuts = 5
        beta_low = 1.0
        beta_mid = 2.0
        beta_high = 3.0

        model_low = HeuristicCostModel(gate_error_rate=0.01, beta=beta_low, gamma=1.0)
        model_mid = HeuristicCostModel(gate_error_rate=0.01, beta=beta_mid, gamma=1.0)
        model_high = HeuristicCostModel(gate_error_rate=0.01, beta=beta_high, gamma=1.0)

        cost_low = model_low._calculate_classical_cost(self.graph, num_cuts)
        cost_mid = model_mid._calculate_classical_cost(self.graph, num_cuts)
        cost_high = model_high._calculate_classical_cost(self.graph, num_cuts)

        self.assertGreater(cost_mid, cost_low, "beta=2.0 must have higher cost than beta=1.0")
        self.assertGreater(cost_high, cost_mid, "beta=3.0 must have higher cost than beta=2.0")

    def test_zero_cuts_has_zero_cost_regardless_of_beta(self):
        """Zero cuts must always have zero classical cost."""
        for beta in [1.0, 1.5, 2.0, 3.0, 5.0]:
            model = HeuristicCostModel(gate_error_rate=0.01, beta=beta, gamma=1.0)
            self.assertEqual(model._calculate_classical_cost(self.graph, 0), 0.0)

    def test_cost_increases_monotonically_with_num_cuts(self):
        """For a fixed beta, more cuts must increase the classical cost."""
        model = HeuristicCostModel(gate_error_rate=0.01, beta=2.0, gamma=1.0)
        costs = [model._calculate_classical_cost(self.graph, cuts) for cuts in range(16)]

        for i in range(len(costs) - 1):
            self.assertLessEqual(costs[i], costs[i + 1])

    def test_total_cost_convex_combination(self):
        """Total cost must strictly equal alpha * quantum + (1 - alpha) * classical."""
        for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:
            model = HeuristicCostModel(gate_error_rate=0.01, alpha=alpha, beta=2.0, gamma=1.0)
            res = model.calculate_total_cost(self.graph, n_sub=4, num_cuts=3)
            expected = alpha * res["quantum_cost"] + (1 - alpha) * res["classical_cost"]
            self.assertAlmostEqual(res["total_cost"], expected, places=6)


if __name__ == "__main__":
    unittest.main()
