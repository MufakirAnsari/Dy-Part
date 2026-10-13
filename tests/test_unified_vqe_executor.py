# tests/test_unified_vqe_executor.py
"""Unit tests verifying the consolidated PartitionedVQE executor and backward-compatibility aliases (ACT-021, ISS-037)."""

import unittest
import networkx as nx
from qiskit_algorithms.optimizers import COBYLA

from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.vqe_executor import (
    PartitionedVQE,
    PartitionedVQE_Blind,
    PartitionedVQE_Deterministic,
    PartitionedVQE_Blind_Deterministic,
)
from vqe_framework.vqe_executor_blind import PartitionedVQE_Blind as ReexportedBlind
from vqe_framework.vqe_executor_deterministic import PartitionedVQE_Deterministic as ReexportedDet
from vqe_framework.vqe_executor_blind_deterministic import (
    PartitionedVQE_Blind_Deterministic as ReexportedBlindDet,
)


class TestUnifiedVQEExecutor(unittest.TestCase):
    """Verify initialization, parameters, and legacy alias wrappers of PartitionedVQE."""

    def setUp(self):
        self.graph = nx.cycle_graph(4)
        self.qpu = NoisyQPU(n_qubits=4, gate_error_rate=1e-3)
        self.optimizer = COBYLA(maxiter=5)

    def test_default_partitioned_vqe(self):
        """Verify default configuration: cut-aware reconstruction, 8192 shots."""
        vqe = PartitionedVQE(self.graph, self.qpu, self.optimizer, seed=42)
        self.assertTrue(vqe.reconstruct_cuts)
        self.assertEqual(vqe.shots, 8192)
        self.assertEqual(vqe.seed, 42)

    def test_blind_partitioned_vqe(self):
        """Verify blind configuration: reconstruct_cuts=False."""
        vqe = PartitionedVQE(
            self.graph, self.qpu, self.optimizer, seed=42, reconstruct_cuts=False
        )
        self.assertFalse(vqe.reconstruct_cuts)

    def test_legacy_blind_wrapper(self):
        """Verify PartitionedVQE_Blind is a subclass with reconstruct_cuts=False."""
        vqe = PartitionedVQE_Blind(self.graph, self.qpu, self.optimizer)
        self.assertIsInstance(vqe, PartitionedVQE)
        self.assertFalse(vqe.reconstruct_cuts)
        self.assertEqual(vqe.shots, 8192)

    def test_legacy_deterministic_wrapper(self):
        """Verify PartitionedVQE_Deterministic has reconstruct_cuts=True and custom shots."""
        vqe = PartitionedVQE_Deterministic(self.graph, self.qpu, self.optimizer, shots=2048)
        self.assertIsInstance(vqe, PartitionedVQE)
        self.assertTrue(vqe.reconstruct_cuts)
        self.assertEqual(vqe.shots, 2048)
        self.assertEqual(vqe.seed, 42)

    def test_legacy_blind_deterministic_wrapper(self):
        """Verify PartitionedVQE_Blind_Deterministic has reconstruct_cuts=False and custom shots."""
        vqe = PartitionedVQE_Blind_Deterministic(self.graph, self.qpu, self.optimizer, shots=1024)
        self.assertIsInstance(vqe, PartitionedVQE)
        self.assertFalse(vqe.reconstruct_cuts)
        self.assertEqual(vqe.shots, 1024)
        self.assertEqual(vqe.seed, 42)

    def test_module_reexport_identity(self):
        """Verify backward-compatible module re-exports point to identical class objects."""
        self.assertIs(ReexportedBlind, PartitionedVQE_Blind)
        self.assertIs(ReexportedDet, PartitionedVQE_Deterministic)
        self.assertIs(ReexportedBlindDet, PartitionedVQE_Blind_Deterministic)


if __name__ == "__main__":
    unittest.main()
