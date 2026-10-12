# vqe_framework/utils/graph_partitioner.py

import networkx as nx
from typing import List, Tuple

def partition_graph_greedy(graph: nx.Graph, n_sub: int) -> Tuple[List[nx.Graph], int]:
    """
    Partitions a graph into subgraphs of a maximum size using a greedy strategy.
    
    The strategy is simple:
    1. Start a new subgraph with an unassigned node.
    2. Greedily add its neighbors until the subgraph is full (size n_sub).
    3. Repeat until all nodes are assigned to a subgraph.
    
    This is a placeholder and not a highly optimized graph partitioning algorithm,
    but it is sufficient for our framework's needs.
    
    Args:
        graph: The full graph to partition.
        n_sub: The maximum number of nodes allowed in each subgraph.
        
    Returns:
        A tuple containing:
        - A list of NetworkX graph objects (the subgraphs).
        - The total number of edges that were cut.
    """
    if n_sub >= graph.number_of_nodes():
        return [graph.copy()], 0
        
    nodes_to_assign = sorted(graph.nodes())
    subgraphs = []
    
    while nodes_to_assign:
        new_subgraph = nx.Graph()
        # Seed the new subgraph with a random unassigned node
        seed_node = nodes_to_assign.pop(0)
        new_subgraph.add_node(seed_node)
        
        # Use a queue for breadth-first expansion from the seed
        queue = sorted(graph.neighbors(seed_node))
        
        while len(new_subgraph.nodes()) < n_sub and nodes_to_assign:
            # Find a node in the queue that is still unassigned
            candidate_node = -1
            for node in queue:
                if node in nodes_to_assign:
                    candidate_node = node
                    break
            
            if candidate_node != -1:
                queue.remove(candidate_node)
                nodes_to_assign.remove(candidate_node)
                new_subgraph.add_node(candidate_node)
                # Add new neighbors to the back of the queue (sorted for determinism)
                for neighbor in sorted(graph.neighbors(candidate_node)):
                    if neighbor in nodes_to_assign and neighbor not in queue:
                        queue.append(neighbor)
            else:
                # If no neighbors are available, we have a disconnected component
                # or the subgraph is complete. Break and start a new one.
                break
        
        subgraphs.append(new_subgraph)
        
    # Now that we have the subgraphs, add the internal edges
    for subg in subgraphs:
        for u in subg.nodes():
            for v in subg.nodes():
                if u > v and graph.has_edge(u, v):
                    subg.add_edge(u, v)

    # Finally, calculate the number of cut edges
    num_cuts = 0
    original_edges = set(graph.edges())
    internal_edges = set()
    for subg in subgraphs:
        internal_edges.update(subg.edges())
        
    num_cuts = len(original_edges - internal_edges)
    
    return subgraphs, num_cuts