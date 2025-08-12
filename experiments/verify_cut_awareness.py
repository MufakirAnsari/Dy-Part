# experiments/verify_cut_awareness.py

import networkx as nx
import matplotlib.pyplot as plt
import os

from vqe_framework.qpu_interface import NoisyQPU
from qiskit_algorithms.optimizers import SPSA
# Import BOTH executor classes with clear aliases
from vqe_framework.vqe_executor import PartitionedVQE as CutAwareVQE
from vqe_framework.vqe_executor_blind import PartitionedVQE_Blind as BlindVQE
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver

if __name__ == "__main__":
    print("--- Verification Experiment: Cut-Aware vs. Blind VQE ---")
    
    # Setup
    graph = nx.random_regular_graph(d=3, n=8, seed=42)
    qpu = NoisyQPU(n_qubits=8, gate_error_rate=1e-3, readout_error_rate=1e-2)
    
    # Use a fresh optimizer instance for each run to be fair
    optimizer_blind = SPSA(maxiter=150)
    optimizer_aware = SPSA(maxiter=150)
    
    # We will use a fixed partition plan that requires significant recombination
    partition_plan = {"optimal_n_sub": 4}

    # --- Run 1: Blind VQE ---
    print("\n--- Running Blind VQE (Ignores Cut Energy) ---")
    blind_vqe = BlindVQE(graph=graph, qpu=qpu, optimizer=optimizer_blind)
    blind_result = blind_vqe.run(partition_plan)
    
    # --- Run 2: Cut-Aware VQE ---
    print("\n--- Running Cut-Aware VQE (Includes Cut Energy) ---")
    cut_aware_vqe = CutAwareVQE(graph=graph, qpu=qpu, optimizer=optimizer_aware)
    cut_aware_result = cut_aware_vqe.run(partition_plan)

    # --- Analysis ---
    exact_solver = NumPyMinimumEigensolver()
    full_hamiltonian = get_maxcut_hamiltonian(graph)
    true_min_energy = exact_solver.compute_minimum_eigenvalue(full_hamiltonian).eigenvalue.real

    # NOTE: The "blind" VQE minimizes a different objective. Its final "energy" isn't
    # the true energy. We would need to reconstruct it, but for the plot,
    # the convergence curve is what matters. The Cut-Aware AR is the true metric.
    aware_ar = cut_aware_result['final_energy'] / true_min_energy

    print("\n--- VERIFICATION COMPLETE ---")
    print(f"True Ground State Energy: {true_min_energy:.4f}")
    print(f"Blind VQE Final Internal Energy:   {blind_result['final_energy']:.4f} (Not the full energy)")
    print(f"Cut-Aware VQE Final Full Energy: {cut_aware_result['final_energy']:.4f} (AR: {aware_ar:.4f})")
    
    # --- Plotting ---
    plt.figure(figsize=(12, 7))
    plt.plot(blind_result['convergence_data']['iters'], blind_result['convergence_data']['vals'], 'o-', label=f'Blind VQE (Internal Energy Only)')
    plt.plot(cut_aware_result['convergence_data']['iters'], cut_aware_result['convergence_data']['vals'], 's-', label=f'Cut-Aware VQE (Full Energy, AR={aware_ar:.2f})')
    plt.axhline(y=true_min_energy, color='red', linestyle='--', label='True Ground State Energy')
    plt.xlabel("Optimizer Iteration")
    plt.ylabel("Reconstructed Energy")
    plt.title("Verification of Cut-Aware Energy Recombination")
    plt.legend()
    plt.grid(True)
    
    if not os.path.exists("results"):
        os.makedirs("results")
    plt.savefig("results/day8_verification_plot.png", dpi=300)
    print("\nVerification plot saved to 'results/day8_verification_plot.png'")
    plt.show()