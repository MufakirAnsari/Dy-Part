# vqe_framework/vqe_executor_blind_deterministic.py
"""Deprecated: Use vqe_framework.vqe_executor.PartitionedVQE_Blind_Deterministic or PartitionedVQE(reconstruct_cuts=False).

Maintained for backwards compatibility (ISS-037, ACT-021).
"""

from .vqe_executor import PartitionedVQE_Blind_Deterministic

__all__ = ["PartitionedVQE_Blind_Deterministic"]