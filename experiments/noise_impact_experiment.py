# experiments/noise_impact_experiment.py

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import time
import os

from qiskit.quantum_info import SparsePauliOp
from qiskit_algorithms.minimum_eigensolvers import VQE
from qiskit_algorithms.optimizers import SPSA
from qiskit.circuit.library import TwoLocal
from qiskit.circuit import ClassicalRegister

# Import our new NoisyQPU class
from vqe_framework.qpu_interface import NoisyQPU

# --- Same Hamiltonian function from Day 1 ---
def get_maxcut_hamiltonian(graph: nx.Graph) -> SparsePauliOp:
    num_nodes = graph.number_of_nodes()
    pauli_list = []
    for i, j in graph.edges():
        pauli_op = ["I"] * num_nodes
        pauli_op[i] = "Z"
        pauli_op[j] = "Z"
        pauli_list.append("".join(pauli_op))
    coeffs = [1.0] * len(pauli_list)
    return SparsePauliOp(pauli_list, coeffs)

def run_vqe_with_noise(graph, gate_error_rate, readout_error_rate):
    """
    A full VQE run for a given graph and noise level.
    Returns the final approximation ratio.
    """
    num_nodes = graph.number_of_nodes()
    hamiltonian = get_maxcut_hamiltonian(graph)
    
    # --- 1. Setup Noisy QPU ---
    # Instantiate our noisy simulator
    qpu = NoisyQPU(
        n_qubits=num_nodes,
        gate_error_rate=gate_error_rate,
        readout_error_rate=readout_error_rate
    )
    # Get the estimator primitive configured with the noise model
    noisy_estimator = qpu.get_estimator()
    
    # --- 2. VQE Configuration ---
    optimizer = SPSA(maxiter=100)
    ansatz = TwoLocal(hamiltonian.num_qubits, "ry", "cz", reps=2, entanglement="linear")
    
    np.random.seed(42) # Ensure the same starting point for fair comparison
    initial_point = np.random.random(ansatz.num_parameters)
    
    vqe = VQE(
        estimator=noisy_estimator,
        ansatz=ansatz,
        optimizer=optimizer,
        initial_point=initial_point,
    )
    
    # --- 3. Run VQE ---
    result = vqe.compute_minimum_eigenvalue(operator=hamiltonian)
    
    # --- 4. Calculate Approximation Ratio ---
    true_min_energy = -graph.number_of_edges() # For this simple unweighted graph
    approximation_ratio = result.optimal_value / true_min_energy
    
    print(f"  Gate Error: {gate_error_rate:.1e} -> Approx. Ratio: {approximation_ratio:.4f}")
    return approximation_ratio

# --- Main Experiment ---
if __name__ == "__main__":
    start_time = time.time()
    
    # Define the problem graph
    n_nodes = 4
    graph = nx.Graph()
    graph.add_nodes_from(range(n_nodes))
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])

    # Define the range of noise levels to test
    # We will sweep the gate error rate, keeping readout error proportional
    gate_error_rates = np.logspace(-4, -1.5, 10) # From 0.01% to ~3% error
    results = {"gate_errors": [], "approx_ratios": []}

    print("--- Starting Noise Impact Experiment ---")
    
    # Run VQE for each noise level
    for err in gate_error_rates:
        # We assume readout error is typically an order of magnitude higher than gate error
        readout_err = min(err * 10, 0.2) # Cap readout error at 20%
        
        ratio = run_vqe_with_noise(graph, gate_error_rate=err, readout_error_rate=readout_err)
        results["gate_errors"].append(err)
        results["approx_ratios"].append(ratio)
    
    print("--- Experiment Complete ---")

    # --- Plotting the Results ---
    print("\n--- Generating and Saving High-Definition Plot ---")
    if not os.path.exists("results"):
        os.makedirs("results")
        
    plt.figure(figsize=(12, 7))
    plt.plot(results["gate_errors"], results["approx_ratios"], 'o-', color='crimson', label='VQE Performance')
    
    plt.xscale('log')
    plt.xlabel('2-Qubit Gate Error Rate (Log Scale)', fontsize=12)
    plt.ylabel('Approximation Ratio (VQE Energy / True Energy)', fontsize=12)
    plt.title('VQE Performance Degradation with Increasing QPU Noise', fontsize=14)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Add a horizontal line for "random guess" performance
    # A random bitstring will have, on average, half the edges cut. Energy = 0. Approx Ratio = 0.
    # But a slightly better classical baseline is often around 0.5.
    plt.axhline(y=0.5, color='gray', linestyle=':', label='Classical Heuristic Guess Baseline (Approx. Ratio = 0.5)')
    plt.axhline(y=1.0, color='blue', linestyle='--', label='Ideal (Noiseless) Performance')
    
    plt.legend(fontsize=12)
    plt.ylim(0, 1.1) # Set y-axis limits
    
    # Add annotations to make the plot more informative
    plt.text(1e-4, 1.02, "Low Noise Regime\n(Near-Ideal)", color='blue', ha='left')
    plt.text(1e-2, 0.2, "High Noise Regime\n(Results are unreliable)", color='red', ha='center')

    plt.savefig("results/day2_noise_impact.png", dpi=300, bbox_inches='tight')
    
    end_time = time.time()
    print(f"Plot saved to 'results/day2_noise_impact.png'")
    print(f"Total experiment time: {end_time - start_time:.2f} seconds.")
    
    plt.show()