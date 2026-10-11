# experiments/run_static_vqe.py
# This script runs the "Static Partitioner" baseline, which uses a fixed subgraph size.

import networkx as nx
import matplotlib.pyplot as plt
import os
import time

# Import our "Cut-Aware" VQE executor
from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.vqe_executor import PartitionedVQE
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA

if __name__ == '__main__':
    start_time = time.time()
    
    print("--- Running Static VQE Baseline ---")
    
    # --- 1. Define the Problem and Hardware ---
    graph = nx.random_regular_graph(d=3, n=8, seed=42)
    GATE_ERROR_RATE = 1e-3
    
    # --- 2. Define the STATIC Partition Plan ---
    # This is the key difference: we hard-code the partition size.
    # No scheduler is called.
    STATIC_PARTITION_SIZE = 4
    partition_plan = {"optimal_n_sub": STATIC_PARTITION_SIZE}
    print(f"Using fixed partition size (n_sub): {STATIC_PARTITION_SIZE}")

    # --- 3. Execute the VQE with the Static Plan ---
    qpu = NoisyQPU(n_qubits=graph.number_of_nodes(), gate_error_rate=GATE_ERROR_RATE)
    optimizer = COBYLA(maxiter=150)
    
    # We use the same high-quality "Cut-Aware" executor for a fair comparison
    static_vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer)
    result = static_vqe.run(partition_plan)
    
    # --- 4. Analyze and Report Results ---
    final_energy = result['final_energy']
    
    # Get the true ground state energy for AR calculation
    exact_solver = NumPyMinimumEigensolver()
    full_hamiltonian = get_maxcut_hamiltonian(graph)
    true_min_energy = exact_solver.compute_minimum_eigenvalue(full_hamiltonian).eigenvalue.real
    
    approximation_ratio = final_energy / true_min_energy
    
    print("\n--- FINAL RESULTS (STATIC VQE) ---")
    print(f"Static VQE Final Energy: {final_energy:.4f}")
    print(f"Approximation Ratio: {approximation_ratio:.4f}")
    
    end_time = time.time()
    print(f"\nTotal Static VQE Runtime: {end_time - start_time:.2f} seconds.")