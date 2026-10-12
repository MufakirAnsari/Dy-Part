# tests/test_cost_model.py

import unittest
import networkx as nx
from vqe_framework.cost_model import HeuristicCostModel

class TestHeuristicCostModel(unittest.TestCase):
    def setUp(self):
        """Set up a simple graph for testing."""
        self.graph = nx.complete_graph(10) # 10-node complete graph
        # Total edges = n*(n-1)/2 = 10*9/2 = 45
    
    def test_initialization(self):
        """Test that the model initializes correctly and rejects bad inputs."""
        model = HeuristicCostModel(gate_error_rate=1e-3, alpha=0.5, beta=2.0)
        self.assertEqual(model.gate_error_rate, 1e-3)
        self.assertEqual(model.alpha, 0.5)
        self.assertEqual(model.beta, 2.0)
        
        with self.assertRaises(ValueError):
            HeuristicCostModel(1e-3, alpha=1.1) # alpha > 1
        with self.assertRaises(ValueError):
            HeuristicCostModel(1e-3, beta=0.9) # beta < 1

    def test_quantum_cost_increases_with_size(self):
        """Verify that quantum cost increases for larger subgraphs."""
        model = HeuristicCostModel(gate_error_rate=1e-3)
        cost_4_qubit = model._calculate_quantum_cost(n_sub=4)
        cost_8_qubit = model._calculate_quantum_cost(n_sub=8)
        self.assertGreater(cost_8_qubit, cost_4_qubit)
        self.assertGreater(cost_4_qubit, 0)

    def test_classical_cost_increases_with_cuts(self):
        """Verify that classical cost increases with more cuts."""
        model = HeuristicCostModel(gate_error_rate=1e-3)
        cost_5_cuts = model._calculate_classical_cost(self.graph, num_cuts=5)
        cost_10_cuts = model._calculate_classical_cost(self.graph, num_cuts=10)
        self.assertGreater(cost_10_cuts, cost_5_cuts)
        self.assertGreater(cost_5_cuts, 0)
        
    def test_alpha_weighting(self):
        """Verify that the alpha parameter correctly weights the costs."""
        # Case 1: alpha = 1 (only quantum cost matters)
        model_quantum_only = HeuristicCostModel(gate_error_rate=1e-2, alpha=1.0)
        costs = model_quantum_only.calculate_total_cost(self.graph, n_sub=5, num_cuts=10)
        self.assertEqual(costs['total_cost'], costs['quantum_cost'])
        self.assertNotEqual(costs['total_cost'], 0)

        # Case 2: alpha = 0 (only classical cost matters)
        model_classical_only = HeuristicCostModel(gate_error_rate=1e-2, alpha=0.0)
        costs = model_classical_only.calculate_total_cost(self.graph, n_sub=5, num_cuts=10)
        self.assertEqual(costs['total_cost'], costs['classical_cost'])
        self.assertNotEqual(costs['total_cost'], 0)

    def test_beta_exponent_effect(self):
        """Verify that a higher beta penalizes cuts more severely (DEC-001 fix)."""
        model_beta_2 = HeuristicCostModel(gate_error_rate=1e-3, beta=2.0)
        model_beta_3 = HeuristicCostModel(gate_error_rate=1e-3, beta=3.0)
        
        cost_beta_2 = model_beta_2._calculate_classical_cost(self.graph, num_cuts=5)
        cost_beta_3 = model_beta_3._calculate_classical_cost(self.graph, num_cuts=5)
        
        # With corrected formula (cuts/edges)**(1/beta), higher beta strictly increases cost
        self.assertGreater(cost_beta_3, cost_beta_2)
        # Let's check with more cuts to be sure
        cost_beta_2_more_cuts = model_beta_2._calculate_classical_cost(self.graph, num_cuts=20)
        cost_beta_3_more_cuts = model_beta_3._calculate_classical_cost(self.graph, num_cuts=20)
        self.assertGreater(cost_beta_3_more_cuts, cost_beta_2_more_cuts)

if __name__ == '__main__':
    unittest.main()