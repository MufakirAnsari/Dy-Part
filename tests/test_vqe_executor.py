# tests/test_vqe_executor.py
"""Test verifying PartitionedVQE import and execution compatibility."""

import unittest
import networkx as nx
from qiskit_algorithms.optimizers import COBYLA
from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.vqe_executor import PartitionedVQE


class TestVQEExecutorCompatibility(unittest.TestCase):
    def test_partitioned_vqe_import_and_init(self):
        """Verify PartitionedVQE can be imported and initialized without ImportError."""
        graph = nx.cycle_graph(4)
        qpu = NoisyQPU(n_qubits=4, gate_error_rate=1e-3)
        optimizer = COBYLA(maxiter=5)
        vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer, seed=42)
        self.assertIsNotNone(vqe)
        self.assertEqual(vqe.graph.number_of_nodes(), 4)
