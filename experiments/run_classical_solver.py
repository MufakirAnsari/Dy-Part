# experiments/run_classical_solver.py
# This script provides the "ground truth" by solving the Max-Cut problem exactly.

import networkx as nx
import time

# Import our existing Hamiltonian constructor
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver

if __name__ == "__main__":
    print("--- Running Classical Exact Solver Baseline ---")
    start_time = time.time()
    
    # --- 1. Define the Problem ---
    # Use the same 8-node graph from our integration test for consistency
    graph = nx.random_regular_graph(d=3, n=8, seed=42)
    print(f"Problem Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # --- 2. Build the Hamiltonian ---
    hamiltonian = get_maxcut_hamiltonian(graph)
    
    # --- 3. Run the Exact Classical Solver ---
    exact_solver = NumPyMinimumEigensolver()
    result = exact_solver.compute_minimum_eigenvalue(operator=hamiltonian)
    
    true_min_energy = result.eigenvalue.real
    
    end_time = time.time()
    
    # --- 4. Report the Result ---
    print("\n--- CLASSICAL SOLVER COMPLETE ---")
    print(f"True Ground State Energy: {true_min_energy:.4f}")
    print(f"Runtime: {end_time - start_time:.4f} seconds")