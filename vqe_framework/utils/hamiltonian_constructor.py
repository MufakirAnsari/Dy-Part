# vqe_framework/utils/hamiltonian_constructor.py
# --- VERSION 2: ROBUST TO ARBITRARY NODE LABELS ---

import networkx as nx
from qiskit.quantum_info import SparsePauliOp

def get_maxcut_hamiltonian(graph: nx.Graph) -> SparsePauliOp:
    """
    Generates the Max-Cut Hamiltonian for a given graph.
    
    This version is robust to graphs where node labels are not contiguous
    from 0 to N-1, which is common for subgraphs.
    
    Args:
        graph: A NetworkX graph object.
    
    Returns:
        A Qiskit SparsePauliOp representing the Hamiltonian.
    """
    if not isinstance(graph, nx.Graph):
        raise TypeError("Input must be a NetworkX Graph object.")
    
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        return SparsePauliOp([], [])

    # *** THE FIX IS HERE: Create a mapping from original labels to local indices ***
    # e.g., if graph.nodes() is [5, 7], node_map will be {5: 0, 7: 1}
    node_map = {node_label: i for i, node_label in enumerate(graph.nodes())}

    pauli_list = []
    for i_global, j_global in graph.edges():
        # Get the local indices corresponding to the global node labels
        i_local = node_map[i_global]
        j_local = node_map[j_global]
        
        # Create a Pauli string for the subgraph's size
        pauli_op_str = ['I'] * num_nodes
        
        # Use the local indices to place the Z gates
        pauli_op_str[i_local] = 'Z'
        pauli_op_str[j_local] = 'Z'
        pauli_list.append("".join(pauli_op_str))

    coeffs = [1.0] * len(pauli_list)
    
    return SparsePauliOp(pauli_list, coeffs)

def get_graph_solution_value(graph: nx.Graph, solution_bitstring: str) -> int:
    """
    Calculates the value of the cut for a given solution bitstring.
    Note: Assumes solution_bitstring is for the full graph with original labels.
    """
    cut_size = 0
    for i, j in graph.edges():
        if solution_bitstring[i] != solution_bitstring[j]:
            cut_size += 1
    return cut_size