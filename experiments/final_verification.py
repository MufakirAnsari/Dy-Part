# experiments/final_verification.py
# This script produces the final, definitive comparison plot for the paper.

import networkx as nx
import matplotlib.pyplot as plt
import os
import time

from vqe_framework.qpu_interface import NoisyQPU
from qiskit_algorithms.optimizers import COBYLA

# Import ALL THREE executors we have built
from vqe_framework.vqe_executor_blind import PartitionedVQE_Blind
from vqe_framework.vqe_executor_deterministic import PartitionedVQE_Deterministic

from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver

if __name__ == "__main__":
    start_time = time.time()
    print("--- Final Verification: Blind vs. Cut-Aware VQE (Deterministic) ---")
    
    # --- 1. Setup ---
    graph = nx.random_regular_graph(d=3, n=8, seed=42)
    qpu = NoisyQPU(n_qubits=8, gate_error_rate=1e-3, readout_error_rate=1e-2)
    
    # Use COBYLA for smooth convergence and high shots for accuracy
    optimizer_config = {"maxiter": 200}
    shots_config = 8192
    
    # Use a fixed partition plan that is non-trivial
    partition_plan = {"optimal_n_sub": 4}

    # --- 2. Run the "Blind" VQE ---
    print("\n--- Running Blind VQE (COBYLA, High Shots) ---")
    blind_optimizer = COBYLA(**optimizer_config)
    # We need a deterministic blind executor. Let's create it on the fly.
    # A better way is to create a new file, but for speed, let's adapt.
    # Let's create vqe_executor_blind_deterministic.py for cleanliness.
    # For now, let's assume we've done that.
    
    # Let's create the blind executor based on the deterministic one.
    # Create a new file vqe_framework/vqe_executor_blind_deterministic.py
    # and copy the content of vqe_executor_deterministic.py into it,
    # then modify its _energy_evaluation_function to be blind.
    from vqe_framework.vqe_executor_blind_deterministic import PartitionedVQE_Blind_Deterministic
    
    blind_vqe = PartitionedVQE_Blind_Deterministic(
        graph=graph, qpu=qpu, optimizer=blind_optimizer, shots=shots_config
    )
    blind_result = blind_vqe.run(partition_plan)

    # --- 3. Run the "Cut-Aware" VQE ---
    print("\n--- Running Cut-Aware VQE (COBYLA, High Shots) ---")
    aware_optimizer = COBYLA(**optimizer_config)
    cut_aware_vqe = PartitionedVQE_Deterministic(
        graph=graph, qpu=qpu, optimizer=aware_optimizer, shots=shots_config
    )
    cut_aware_result = cut_aware_vqe.run(partition_plan)

    # --- 4. Analysis ---
    exact_solver = NumPyMinimumEigensolver()
    full_hamiltonian = get_maxcut_hamiltonian(graph)
    true_min_energy = exact_solver.compute_minimum_eigenvalue(full_hamiltonian).eigenvalue.real

    # The true AR is for the cut-aware version
    aware_ar = cut_aware_result['final_energy'] / true_min_energy

    print("\n--- FINAL VERIFICATION COMPLETE ---")
    print(f"True Ground State Energy: {true_min_energy:.4f}")
    print(f"Blind VQE Final Internal Energy:   {blind_result['final_energy']:.4f} (Objective function value, not true energy)")
    print(f"Cut-Aware VQE Final Full Energy: {cut_aware_result['final_energy']:.4f} (AR: {aware_ar:.4f})")
    
    # --- 5. Plotting ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(blind_result['convergence_data']['iters'], blind_result['convergence_data']['vals'], 'o-', color='darkorange', markersize=4, label=f'Blind VQE (Internal Energy Only)')
    ax.plot(cut_aware_result['convergence_data']['iters'], cut_aware_result['convergence_data']['vals'], 's-', color='dodgerblue', markersize=4, label=f'Cut-Aware VQE (Full Energy, Final AR={aware_ar:.3f})')
    
    ax.axhline(y=true_min_energy, color='red', linestyle='--', label=f'True Ground State Energy ({true_min_energy:.2f})')
    
    ax.set_xlabel("Optimizer Iteration", fontsize=12)
    ax.set_ylabel("Reconstructed Energy", fontsize=12)
    ax.set_title("Verification: Cut-Aware vs. Blind VQE with Deterministic Optimizer", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    if not os.path.exists("results"):
        os.makedirs("results")
    plt.savefig("results/day8_final_verification_plot.png", dpi=300)
    print("\nFinal verification plot saved to 'results/day8_final_verification_plot.png'")
    
    end_time = time.time()
    print(f"Total experiment runtime: {end_time - start_time:.2f} seconds.")
    
    plt.show()