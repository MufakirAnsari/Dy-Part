"""vqe_framework/utils/metis_partitioner.py

Graph partitioning implementation using METIS (via pymetis).
Provides the standard classical graph partitioning baseline for DEC-003 and ACT-016.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple
import networkx as nx

from vqe_framework.logging_config import setup_logging

logger = setup_logging()

try:
    import pymetis
    PYMETIS_AVAILABLE = True
except ImportError:
    PYMETIS_AVAILABLE = False


def partition_graph_metis(graph: nx.Graph, n_sub: int) -> Tuple[List[nx.Graph], int]:
    """Partitions a graph into subgraphs of target maximum size using METIS.

    Args:
        graph: NetworkX graph to partition.
        n_sub: Target maximum number of nodes allowed in each subgraph.

    Returns:
        A tuple of (subgraphs, num_cuts):
        - subgraphs: List of NetworkX Graph objects.
        - num_cuts: Total number of cut edges between subgraphs.
    """
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        return [], 0

    if n_sub >= num_nodes or num_nodes <= 1:
        return [graph.copy()], 0

    # Calculate number of partitions: k = ceil(|V| / n_sub)
    n_parts = max(1, math.ceil(num_nodes / max(1, n_sub)))
    if n_parts == 1:
        return [graph.copy()], 0

    # Map graph nodes to contiguous 0..N-1 indices
    sorted_nodes = sorted(graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(sorted_nodes)}
    idx_to_node = {idx: node for idx, node in enumerate(sorted_nodes)}

    if not PYMETIS_AVAILABLE:
        logger.warning("pymetis is not installed; falling back to greedy partitioner.")
        from vqe_framework.utils.graph_partitioner import partition_graph_greedy
        return partition_graph_greedy(graph, n_sub)

    try:
        # Build adjacency list formatted for pymetis:
        # adjacency[i] is a list of contiguous neighbor indices for node index i
        adjacency = []
        for i in range(num_nodes):
            orig_node = idx_to_node[i]
            nbr_indices = sorted([node_to_idx[nbr] for nbr in graph.neighbors(orig_node)])
            adjacency.append(nbr_indices)

        # Execute METIS graph partitioning
        _, membership = pymetis.part_graph(nparts=n_parts, adjacency=adjacency)

        # Group nodes by assigned partition ID
        part_nodes: Dict[int, List[int]] = {}
        for idx, part_id in enumerate(membership):
            orig_node = idx_to_node[idx]
            part_nodes.setdefault(part_id, []).append(orig_node)

        # Construct induced subgraphs
        subgraphs = []
        for p_id in sorted(part_nodes.keys()):
            nodes_in_part = sorted(part_nodes[p_id])
            subg = graph.subgraph(nodes_in_part).copy()
            subgraphs.append(subg)

        # Compute cuts using canonical undirected edge sorting
        original_edges = {tuple(sorted(e)) for e in graph.edges()}
        internal_edges = {tuple(sorted(e)) for subg in subgraphs for e in subg.edges()}
        num_cuts = len(original_edges - internal_edges)

        return subgraphs, num_cuts

    except Exception as exc:
        logger.warning("pymetis partitioning failed (%s); falling back to greedy.", exc)
        from vqe_framework.utils.graph_partitioner import partition_graph_greedy
        return partition_graph_greedy(graph, n_sub)
