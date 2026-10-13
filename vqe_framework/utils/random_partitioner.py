"""vqe_framework/utils/random_partitioner.py

Random-guess graph partitioner baseline for ACT-017 and DEC-003.
Provides an empirical sanity lower bound on partition quality and approximation ratio.
"""

from __future__ import annotations

from typing import List, Tuple
import networkx as nx
import numpy as np


def partition_graph_random(graph: nx.Graph, n_sub: int, seed: int = 42) -> Tuple[List[nx.Graph], int]:
    """Partitions a graph into random subgraphs of target maximum size.

    Args:
        graph: NetworkX graph to partition.
        n_sub: Maximum number of nodes allowed in each subgraph.
        seed: Random seed for reproducible partitioning.

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

    rng = np.random.default_rng(seed)
    nodes = list(sorted(graph.nodes()))
    rng.shuffle(nodes)

    # Chunk shuffled nodes into groups of size at most n_sub
    chunks = [nodes[i:i + n_sub] for i in range(0, len(nodes), n_sub)]

    subgraphs = []
    for chunk in chunks:
        subg = graph.subgraph(chunk).copy()
        subgraphs.append(subg)

    # Canonical edge sorting to prevent orientation artifacts
    original_edges = {tuple(sorted(e)) for e in graph.edges()}
    internal_edges = {tuple(sorted(e)) for subg in subgraphs for e in subg.edges()}
    num_cuts = len(original_edges - internal_edges)

    return subgraphs, num_cuts
