# vqe_framework/utils/hamiltonian_constructor.py
"""Hamiltonian construction and exact MaxCut evaluation utilities.

Provides standard MaxCut cost Hamiltonian construction (DEC-002 Option A),
exact MaxCut ground-state solver, cut value evaluation, and bounded Approximation Ratio
calculation guaranteeing AR in [0.0, 1.0] (ACT-009, ISS-003, ISS-009).
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import networkx as nx


def get_maxcut_hamiltonian(graph: nx.Graph, standard_convention: bool = True) -> SparsePauliOp:
    """Generates the Max-Cut Hamiltonian for a given graph.

    Args:
        graph: NetworkX graph object.
        standard_convention:
            If True (standard MaxCut minimization):
                H_cost = sum_{(u,v) in E} (Z_u Z_v - I) / 2
                Minimizing H_cost yields ground state energy = - MaxCut(G) <= 0.
                Expected cut value = - <H_cost>.
            If False (raw ZZ sum):
                H = sum_{(u,v) in E} Z_u Z_v

    Returns:
        Qiskit SparsePauliOp representing the Hamiltonian.
    """
    if not isinstance(graph, nx.Graph):
        raise TypeError("Input must be a NetworkX Graph object.")

    from qiskit.quantum_info import SparsePauliOp

    num_nodes = graph.number_of_nodes()
    if num_nodes == 0 or graph.number_of_edges() == 0:
        return SparsePauliOp(["I" * max(1, num_nodes)], [0.0])

    # Mapping from original node labels to contiguous local indices 0..N-1
    node_map = {node_label: i for i, node_label in enumerate(sorted(graph.nodes()))}

    pauli_list = []
    coeffs = []

    for i_global, j_global in graph.edges():
        i_local = node_map[i_global]
        j_local = node_map[j_global]

        pauli_op_str = ["I"] * num_nodes
        pauli_op_str[i_local] = "Z"
        pauli_op_str[j_local] = "Z"
        pauli_list.append("".join(pauli_op_str))

        if standard_convention:
            coeffs.append(0.5)
        else:
            coeffs.append(1.0)

    if standard_convention:
        # Subtract |E|/2 * I so that H_cost = sum (Z_u Z_v - I) / 2
        pauli_list.append("I" * num_nodes)
        coeffs.append(-0.5 * graph.number_of_edges())

    return SparsePauliOp(pauli_list, coeffs)


def get_graph_solution_value(graph: nx.Graph, solution_bitstring: str) -> int:
    """Calculates the cut size for a given solution bitstring.

    Assumes bitstring index matches sorted node ordering.
    """
    nodes = sorted(graph.nodes())
    node_to_idx = {n: i for i, n in enumerate(nodes)}

    cut_size = 0
    for u, v in graph.edges():
        idx_u = node_to_idx[u]
        idx_v = node_to_idx[v]
        if solution_bitstring[idx_u] != solution_bitstring[idx_v]:
            cut_size += 1
    return cut_size


def get_exact_maxcut(graph: nx.Graph) -> int:
    """Computes exact MaxCut for a graph via brute force search.

    Optimal for graphs up to 20 nodes; exploits Z2 spin-flip symmetry (fixing bit 0).
    """
    num_nodes = graph.number_of_nodes()
    if num_nodes <= 1 or graph.number_of_edges() == 0:
        return 0

    nodes = sorted(graph.nodes())
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    edges = [(node_to_idx[u], node_to_idx[v]) for u, v in graph.edges()]

    max_cut = 0
    # Fix bit 0 to 0 (reduces search to 2^(N-1))
    for b in range(1 << (num_nodes - 1)):
        cut = sum(1 for u, v in edges if ((b >> u) & 1) != ((b >> v) & 1))
        if cut > max_cut:
            max_cut = cut
    return max_cut


def calculate_approximation_ratio(cut_value: float, max_cut: float) -> float:
    """Calculates the bounded Approximation Ratio (AR).

    Guarantees AR in [0.0, 1.0] by construction (ISS-003, ACT-009).
    """
    if max_cut <= 0:
        return 1.0 if cut_value >= 0 else 0.0
    ratio = float(cut_value) / float(max_cut)
    return max(0.0, min(1.0, ratio))