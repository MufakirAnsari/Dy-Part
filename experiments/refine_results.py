# experiments/refine_results.py

import networkx as nx
import matplotlib.pyplot as plt
import os

from vqe_framework.qpu_interface import NoisyQPU
from qiskit_algorithms.optimizers import COBYLA
# Import our new deterministic executor
from vqe_framework.vqe_executor_deterministic import PartitionedVQE_Deterministic
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver

if __name__ == "__main__":
    print("--- Refinement Experiment: Achieving a Cleaner VQE Result ---")
    
    # Setup
    graph = nx.random_regular_graph(d=3, n=8, seed=42)
    qpu = NoisyQPU(n_qubits=8, gate_error_rate=1e-3, readout_error_rate=1e-2)
    
    optimizer = COBYLA(maxiter=200) # Give COBYLA more iterations to converge smoothly
    shots_for_clean_result = 8192  # High shots for low statistical noise
    
    # We will use a fixed partition plan for this demonstration
    partition_plan = {"optimal_n_sub": 4}

    # --- Run the Deterministic, Cut-Aware VQE ---
    print("\n--- Running Cut-Aware VQE with COBYLA and High Shots ---")
    vqe = PartitionedVQE_Deterministic(
        graph=graph, 
        qpu=qpu, 
        optimizer=optimizer, 
        shots=shots_for_clean_result
    )
    result = vqe.run(partition_plan)

    # --- Analysis ---
    exact_solver = NumPyMinimumEigensolver()
    full_hamiltonian = get_maxcut_hamiltonian(graph)
    true_min_energy = exact_solver.compute_minimum_eigenvalue(full_hamiltonian).eigenvalue.real

    final_ar = result['final_energy'] / true_min_energy

    print("\n--- REFINEMENT COMPLETE ---")
    print(f"True Ground State Energy: {true_min_energy:.4f}")
    print(f"Refined VQE Final Energy: {result['final_energy']:.4f} (AR: {final_ar:.4f})")
    
    # --- Plotting ---
    plt.figure(figsize=(12, 7))
    plt.plot(result['convergence_data']['iters'], result['convergence_data']['vals'], 'o-', color='purple', label=f'Refined VQE (AR={final_ar:.3f})')
    plt.axhline(y=true_min_energy, color='red', linestyle='--', label=f'True Ground State Energy ({true_min_energy:.2f})')
    plt.xlabel("Optimizer Iteration")
    plt.ylabel("Reconstructed Total Energy")
    plt.title("Refined VQE Convergence Profile (COBYLA Optimizer, 8192 Shots)")
    plt.legend()
    plt.grid(True)
    
    if not os.path.exists("results"):
        os.makedirs("results")
    plt.savefig("results/day8_refined_result_plot.png", dpi=300)
    print("\nRefined result plot saved to 'results/day8_refined_result_plot.png'")
    plt.show()