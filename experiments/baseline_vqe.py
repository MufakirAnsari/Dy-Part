# experiments/baseline_vqe.py

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# --- Qiskit Imports ---
# For problem definition
from qiskit.quantum_info import SparsePauliOp

# For the VQE algorithm components
from qiskit_algorithms.minimum_eigensolvers import VQE
from qiskit_algorithms.optimizers import SPSA

# For the ansatz (quantum circuit)
from qiskit.circuit.library import TwoLocal

# For simulation with Primitives
from qiskit_aer.primitives import Estimator as AerEstimator
from qiskit.primitives import Sampler

# --- 1. Problem Definition: A 4-Node Square Graph for Max-Cut ---
print("--- Step 1: Defining the Max-Cut Problem ---")
n_nodes = 4
graph = nx.Graph()
graph.add_nodes_from(range(n_nodes))
graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])

def get_maxcut_hamiltonian(graph: nx.Graph) -> SparsePauliOp:
    """Generates the Max-Cut Hamiltonian for a given graph as a SparsePauliOp."""
    num_nodes = graph.number_of_nodes()
    pauli_list = []
    for i, j in graph.edges():
        pauli_op = ["I"] * num_nodes
        pauli_op[i] = "Z"
        pauli_op[j] = "Z"
        pauli_list.append("".join(pauli_op))
    coeffs = [1.0] * len(pauli_list)
    return SparsePauliOp(pauli_list, coeffs)

hamiltonian = get_maxcut_hamiltonian(graph)
print("Max-Cut Hamiltonian created for the graph.")
print(hamiltonian.to_list())

# --- 2. VQE Setup ---
print("\n--- Step 2: Configuring the VQE Algorithm ---")

# IMPROVEMENT: Increased maxiter for better convergence.
# SPSA is a good choice as it's resilient to noise, which will be important in Day 2.
optimizer = SPSA(maxiter=100)
print(f"Optimizer: SPSA with maxiter={optimizer.maxiter}")

# The quantum circuit ansatz. TwoLocal is a general-purpose, hardware-efficient ansatz.
ansatz = TwoLocal(hamiltonian.num_qubits, "ry", "cz", reps=2, entanglement="linear")
print(f"Ansatz: TwoLocal with {ansatz.num_parameters} parameters.")

# The Estimator primitive from Qiskit Aer. This is our local, ideal, noiseless simulator.
estimator = AerEstimator()

# --- 3. Running the VQE ---
print("\n--- Step 3: Executing VQE ---")
intermediate_results = {"iters": [], "vals": []}
def vqe_callback(eval_count, parameters, mean, std):
    """Callback function to store intermediate energy values."""
    intermediate_results["iters"].append(eval_count)
    intermediate_results["vals"].append(mean)
    if eval_count % 10 == 0:
        print(f"Iteration {eval_count}: Energy = {mean:.4f}")

# Set a seed for the random number generator for reproducibility.
np.random.seed(42)
initial_point = np.random.random(ansatz.num_parameters)

vqe = VQE(
    estimator=estimator,
    ansatz=ansatz,
    optimizer=optimizer,
    initial_point=initial_point,
    callback=vqe_callback,
)

result = vqe.compute_minimum_eigenvalue(operator=hamiltonian)
print("\n--- VQE Final Result ---")
print(f"Optimal value (minimum energy): {result.optimal_value:.4f}")

# --- 4. Analyzing the Solution ---
print("\n--- Step 4: Analyzing the Solution ---")
optimal_params = result.optimal_parameters

# Create the final circuit with the optimal parameters
final_circuit = ansatz.assign_parameters(optimal_params)

# Add measurement to the circuit. This requires a ClassicalRegister.
from qiskit.circuit import ClassicalRegister
creg = ClassicalRegister(n_nodes, name="creg")
final_circuit.add_register(creg)
final_circuit.measure(range(n_nodes), range(n_nodes))

# Use the Sampler primitive to get the probability distribution of outcomes
sampler = Sampler()
job = sampler.run(final_circuit, shots=2048) # Increased shots for better stats
sampler_result = job.result()
counts = sampler_result.quasi_dists[0].binary_probabilities()

# The most frequent measurement is our candidate solution
solution_bitstring = max(counts, key=counts.get)

# Note: Qiskit's bitstring format is often right-to-left ('q3 q2 q1 q0')
# We will reverse it for consistent interpretation with our graph nodes [0, 1, 2, 3]
solution_bitstring_ordered = solution_bitstring[::-1]

print(f"Most likely solution bitstring (q0q1q2q3): {solution_bitstring_ordered}")

# The true minimum energy for this specific Hamiltonian is -4.0
true_min_energy = -4.0
approximation_ratio = result.optimal_value / true_min_energy
print(f"Approximation Ratio: {approximation_ratio:.4f}")


# --- 5. Visualization and Saving Plots ---
print("\n--- Step 5: Generating and Saving High-Definition Plots ---")

# Plot 1: The Problem Graph
plt.figure(figsize=(6, 6))
nx.draw_kamada_kawai(graph, with_labels=True, alpha=0.9, node_size=600, font_size=12)
plt.title("Problem Definition: 4-Node Max-Cut Graph", fontsize=14)
plt.savefig("results/day1_problem_graph.png", dpi=300, bbox_inches='tight')

# Plot 2: The Ansatz Circuit
plt.figure(figsize=(12, 6))
ansatz.decompose().draw('mpl', style='iqx')
plt.suptitle("VQE Ansatz: TwoLocal(reps=2, ry, cz)", fontsize=14)
plt.savefig("results/day1_ansatz_circuit.png", dpi=300, bbox_inches='tight')

# Plot 3: VQE Convergence
plt.figure(figsize=(12, 7))
plt.plot(intermediate_results["iters"], intermediate_results["vals"], color='blue', marker='o', linestyle='-', markersize=4, label='VQE Energy')
plt.axhline(y=true_min_energy, color='red', linestyle='--', label=f"True Ground State Energy ({true_min_energy})")
plt.xlabel("Optimizer Iteration", fontsize=12)
plt.ylabel("Hamiltonian Expectation Value (Energy)", fontsize=12)
plt.title("VQE Convergence Profile", fontsize=14)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.legend(fontsize=12)
plt.savefig("results/day1_vqe_convergence.png", dpi=300, bbox_inches='tight')

# Plot 4: The Solution
plt.figure(figsize=(6, 6))
# Colors are based on the bitstring '0' -> red, '1' -> blue
colors = ['#FF6B6B' if bit == '0' else '#4D96FF' for bit in solution_bitstring_ordered]
nx.draw_kamada_kawai(graph, with_labels=True, node_color=colors, alpha=0.9, node_size=600, font_size=12)
plt.title(f"Final Solution Coloring (Bitstring: {solution_bitstring_ordered})", fontsize=14)
plt.savefig("results/day1_solution_graph.png", dpi=300, bbox_inches='tight')

print("All plots saved to the 'results/' directory.")

# This will display all plot windows at the end of the script execution
plt.show()