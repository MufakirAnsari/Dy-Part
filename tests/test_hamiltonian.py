# tests/test_hamiltonian.py

import unittest
import networkx as nx
from qiskit.quantum_info import SparsePauliOp
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian

class TestHamiltonianConstructor(unittest.TestCase):
    def test_square_graph(self):
        """Test the Hamiltonian for a 4-node square graph (DEC-002 Option A)."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
        hamiltonian = get_maxcut_hamiltonian(graph)
        
        # In standard MaxCut convention: H = sum (Z_u Z_v - I) / 2
        # Includes 4 edge ZZ terms (coeff 0.5) and 1 identity term (coeff -2.0)
        expected_paulis = {'ZZII', 'IZZI', 'IIZZ', 'ZIIZ', 'IIII'}
        self.assertEqual(set(hamiltonian.paulis.to_labels()), expected_paulis)
        self.assertEqual(len(hamiltonian.coeffs), 5)
        
        # Also test raw ZZ sum convention without identity shift
        hamiltonian_raw = get_maxcut_hamiltonian(graph, standard_convention=False)
        expected_raw_paulis = {'ZZII', 'IZZI', 'IIZZ', 'ZIIZ'}
        self.assertEqual(set(hamiltonian_raw.paulis.to_labels()), expected_raw_paulis)
        self.assertEqual(len(hamiltonian_raw.coeffs), 4)
        self.assertTrue(all(c == 1.0 for c in hamiltonian_raw.coeffs))

if __name__ == '__main__':
    unittest.main()