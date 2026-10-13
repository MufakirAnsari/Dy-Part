# vqe_framework/vqe_executor_deterministic.py
"""Deprecated: Use vqe_framework.vqe_executor.PartitionedVQE_Deterministic or PartitionedVQE(reconstruct_cuts=True).

Maintained for backwards compatibility (ISS-037, ACT-021).
"""

from .vqe_executor import PartitionedVQE_Deterministic

__all__ = ["PartitionedVQE_Deterministic"]