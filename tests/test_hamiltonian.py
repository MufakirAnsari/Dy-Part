# tests/test_hamiltonian.py

import unittest
import networkx as nx
from qiskit.quantum_info import SparsePauliOp
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian

class TestHamiltonianConstructor(unittest.TestCase):
    def test_square_graph(self):
        """Test the Hamiltonian for a 4-node square graph."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
        hamiltonian = get_maxcut_hamiltonian(graph)
        
        # Expected Pauli strings for the edges
        expected_paulis = {'ZZII', 'IZZI', 'IIZZ', 'ZIIZ'}
        self.assertEqual(set(hamiltonian.paulis.to_labels()), expected_paulis)
        self.assertEqual(len(hamiltonian.coeffs), 4)
        self.assertTrue(all(c == 1.0 for c in hamiltonian.coeffs))

if __name__ == '__main__':
    unittest.main()