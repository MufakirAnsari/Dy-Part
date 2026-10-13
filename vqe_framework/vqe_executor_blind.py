# vqe_framework/vqe_executor_blind.py
"""Deprecated: Use vqe_framework.vqe_executor.PartitionedVQE_Blind or PartitionedVQE(reconstruct_cuts=False).

Maintained for backwards compatibility (ISS-037, ACT-021).
"""

from .vqe_executor import PartitionedVQE_Blind

__all__ = ["PartitionedVQE_Blind"]