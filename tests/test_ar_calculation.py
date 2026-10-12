# tests/test_ar_calculation.py
"""Tests verifying that Approximation Ratio (AR) is strictly bounded in [0.0, 1.0] (TEST-003, ACT-009, ISS-003)."""

import unittest
import networkx as nx
from vqe_framework.utils.hamiltonian_constructor import (
    calculate_approximation_ratio,
    get_exact_maxcut,
    get_graph_solution_value,
)


class TestARCalculationBounds(unittest.TestCase):
    def setUp(self):
        # 4-cycle graph: MaxCut = 4 (bipartite graph with 4 edges)
        self.c4 = nx.cycle_graph(4)

        # 6-node 3-regular graph: 9 edges, known MaxCut
        self.reg6 = nx.random_regular_graph(3, 6, seed=42)

    def test_exact_maxcut_known_graphs(self):
        """Verify exact MaxCut calculation on canonical graphs."""
        # C4 is bipartite -> all 4 edges can be cut
        self.assertEqual(get_exact_maxcut(self.c4), 4)

        # K3 (triangle) -> MaxCut is 2
        k3 = nx.complete_graph(3)
        self.assertEqual(get_exact_maxcut(k3), 2)

        # K4 -> MaxCut is 4
        k4 = nx.complete_graph(4)
        self.assertEqual(get_exact_maxcut(k4), 4)

    def test_ar_strictly_bounded_in_0_1(self):
        """Verify AR function never produces values outside [0.0, 1.0] under any input."""
        test_cases = [
            (0.0, 10.0),    # Zero cut -> AR = 0.0
            (5.0, 10.0),    # 50% cut -> AR = 0.5
            (10.0, 10.0),   # 100% cut -> AR = 1.0
            (12.5, 10.0),   # Numerical overshoot/overestimation -> AR clamped to 1.0
            (-2.0, 10.0),   # Negative value -> AR clamped to 0.0
            (0.0, 0.0),     # Degenerate case -> AR = 1.0
        ]

        for cut, max_cut in test_cases:
            ar = calculate_approximation_ratio(cut, max_cut)
            self.assertGreaterEqual(ar, 0.0, f"AR must be >= 0 for cut={cut}, max={max_cut}")
            self.assertLessEqual(ar, 1.0, f"AR must be <= 1 for cut={cut}, max={max_cut}")

    def test_solution_bitstring_cut_matches(self):
        """Verify bitstring evaluation matches analytical cut value."""
        # For C4: alternating bitstring "0101" cuts all 4 edges
        cut = get_graph_solution_value(self.c4, "0101")
        self.assertEqual(cut, 4)

        # "0000" cuts 0 edges
        self.assertEqual(get_graph_solution_value(self.c4, "0000"), 0)


if __name__ == "__main__":
    unittest.main()
